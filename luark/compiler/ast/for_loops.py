import warnings
from dataclasses import dataclass

from lark.ast_utils import AsList
from lark.tree import Meta

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import InternalCompilerError
from luark.opcode.local import LoadLocal, MarkTBC, StoreLocal
from luark.opcode.prepare_for import PrepareForGeneric, PrepareForNumeric
from luark.opcode.push import PushInt
from luark.opcode.test import TestNil, TestNumericFor


# noinspection PyAbstractClass
class ForLoop(Statement, AsList):
    body: Block

    def _emit_body(self, state: CompilerState, loop_start_pc: int) -> None:
        escape_jump_pc = state.reserve_opcode()
        state.begin_loop()
        for statement in self.body.statements:
            statement.compile(state)
        state.add_jump(loop_start_pc)
        state.set_jump(escape_jump_pc)

        state.end_loop()
        state.end_block()


@dataclass
class NumericForLoop(ForLoop):
    control_variable_name: str
    initial_expression: Expression
    limit_expression: Expression
    step_expression: Expression | None

    def __init__(self, meta: Meta, children: list):
        self.meta = meta
        self.control_variable_name = children[0]
        self.initial_expression = children[1]
        self.limit_expression = children[2]

        self.step_expression = None
        if len(children) == 4:
            self.body = children[3]
        elif len(children) == 5:
            self.step_expression = children[3]
            self.body = children[4]
        else:
            raise InternalCompilerError(f"invalid children ({len(children)}) for numeric for loop")

    def compile(self, state: CompilerState) -> None:
        state.begin_block()
        control_local = state.add_locals(self.control_variable_name, 3)

        self.initial_expression.evaluate(state)
        self.limit_expression.evaluate(state)
        if self.step_expression:
            self.step_expression.evaluate(state)
        else:
            state.add_opcode(PushInt(1))
        state.add_opcode(PrepareForNumeric(control_local.index))

        loop_start_pc = state.program_counter
        state.add_opcode(TestNumericFor(control_local.index))
        self._emit_body(state, loop_start_pc)
        state.release_locals(control_local.index, 3)


@dataclass
class GenericForLoop(ForLoop):
    name_list: list[str]
    expression_list: ExpressionList

    def __init__(self, meta: Meta, children: list):
        self.name_list = children[:-2]
        self.expression_list = children[-2]
        self.body = children[-1]

    def compile(self, state: CompilerState) -> None:
        state.begin_block()
        control_local = state.add_locals(self.name_list[0], 4)

        control_index = control_local.index
        state_index = control_index + 1
        iterator_index = control_index + 2
        closing_val_index = control_index + 3

        lvalues = [control_local]
        for name in self.name_list[1:]:
            local = state.add_locals(name)
            lvalues.append(local)

        state.add_opcode(MarkTBC(closing_val_index))
        self.expression_list.evaluate(state, 4)
        state.add_opcode(PrepareForGeneric(control_index))

        # TODO: check stack value orders
        loop_start_pc = state.program_counter
        state.add_opcode(LoadLocal(state_index))
        state.add_opcode(LoadLocal(control_index))
        state.add_opcode(LoadLocal(iterator_index))
        warnings.warn("function calls not yet implemented")  # TODO!

        for lvalue in reversed(lvalues):
            state.add_opcode(StoreLocal(lvalue.index))

        state.add_opcode(LoadLocal(control_index))
        state.add_opcode(TestNil.INSTANCE)
        self._emit_body(state, loop_start_pc)
        state.release_locals(control_local.index, 4)
