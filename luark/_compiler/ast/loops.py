from dataclasses import dataclass

from lark.ast_utils import Ast, AsList

from luark.compiler.ast.block import Block
from luark.compiler.ast.expressions import Expression, MultiresExpression
from luark.compiler.ast.expr_list_utils import evaluate_single, adjust_static
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.ast.statement import Statement


@dataclass
class WhileStmt(Ast, Statement):
    expr: Expression
    block: Block

    def emit(self, state: _ProgramState):
        proto = state.proto

        start = proto.pc
        evaluate_single(state, self.expr)
        proto.add_opcode("test")
        jump_pc = proto.reserve_opcodes(1)

        state.push_block()
        proto.breaks.append([])
        self.block.emit(state)
        state.pop_block()
        proto.add_jump(start)
        block_end = proto.pc

        proto.set_jump(jump_pc, block_end)
        for br in proto.breaks[-1]:
            proto.set_jump(br, block_end)
        proto.breaks.pop()


@dataclass
class RepeatStmt(Ast, Statement):
    block: Block
    expr: Expression

    def emit(self, state: _ProgramState):
        proto = state.proto

        state.push_block()
        start = proto.pc
        proto.breaks.append([])
        self.block.emit(state)

        evaluate_single(state, self.expr)
        proto.add_opcode("test")
        proto.add_jump(start)
        block_end = state.proto.pc
        state.pop_block()

        for br in proto.breaks[-1]:
            state.proto.set_jump(br, block_end)
        proto.breaks.pop()


class BreakStmt(Ast, Statement):
    def emit(self, state: _ProgramState):
        pc = state.proto.pc
        state.proto.reserve_opcodes(1)
        state.proto.breaks[-1].append(pc)


def emit_for_loop_body(
        state: _ProgramState,
        body: Block,
        loop_start_pc: int,
):
    proto = state.proto
    escape_jump_pc = proto.reserve_opcodes(1)
    proto.breaks.append([])
    body.emit(state)
    proto.add_jump(loop_start_pc)

    proto.set_jump(escape_jump_pc)
    for br in proto.breaks[-1]:
        proto.set_jump(br)
    proto.breaks.pop()
    state.pop_block()


@dataclass
class ForLoopNum(Ast, Statement):
    control_name: str
    initial_expr: Expression
    limit_expr: Expression
    step_expr: Expression | None
    body: Block

    def emit(self, state: _ProgramState):
        proto = state.proto
        state.push_block()

        proto.linear_mode = True
        control_index = proto.new_local(self.control_name)
        for _ in range(2):
            proto.new_temporary()
        proto.linear_mode = False

        evaluate_single(state, self.initial_expr)
        evaluate_single(state, self.limit_expr)
        if self.step_expr:
            evaluate_single(state, self.step_expr)
        else:
            proto.add_opcode("push_int 1")
        proto.add_opcode(f"prepare_for_num {control_index}")

        loop_start_pc = proto.pc
        proto.add_opcode(f"test_for {control_index}")
        emit_for_loop_body(state, self.body, loop_start_pc)


@dataclass
class ForLoopGen(Ast, AsList, Statement):
    name_list: list[str]
    expr_list: list[Expression | MultiresExpression]
    body: Block

    def __init__(self, children: list):
        self.name_list = children[0:-2]
        self.expr_list = children[-2]
        self.body = children[-1]

    def emit(self, state: _ProgramState):
        proto = state.proto
        state.push_block()

        proto.linear_mode = True
        iterator_index = proto.new_temporary()
        state_index = proto.new_temporary()
        control_index = proto.get_local_index(self.name_list[0])
        closing_val_index = proto.new_temporary()
        proto.linear_mode = False

        name_indices = [control_index]
        for i in range(1, len(self.name_list)):
            name = self.name_list[i]
            index = proto.get_local_index(name)
            name_indices.append(index)

        proto.add_opcode(f"mark_tbc {closing_val_index}")
        adjust_static(state, 4, self.expr_list)
        proto.add_opcode(f"prepare_for_gen {iterator_index}")

        # TODO: check param and retval orders
        loop_start_pc = proto.pc
        proto.add_opcode(f"load_local {state_index}")
        proto.add_opcode(f"load_local {control_index}")
        proto.add_opcode(f"load_local {iterator_index}")
        proto.add_opcode(f"call 3 {1 + len(self.name_list)}")

        for index in reversed(name_indices):
            proto.add_opcode(f"store_local {index}")

        proto.add_opcode(f"load_local {control_index}")
        proto.add_opcode(f"test_nil")
        emit_for_loop_body(state, self.body, loop_start_pc)
