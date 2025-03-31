from dataclasses import dataclass

from lark.ast_utils import Ast, AsList

from luark.compiler.ast.block import Block
from luark.compiler.ast.block_state import BlockState
from luark.compiler.ast.expressions import Expression, MultiresExpression
from luark.compiler.ast.expr_list_utils import evaluate_single
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.ast.statement import Statement
from luark.compiler.errors import InternalCompilerError


@dataclass
class ElseIf(Ast):
    condition: Expression
    block: Block


class IfStmt(Ast, AsList, Statement):
    def __init__(self, children: list):
        self.end_jumps: list[int] = []

        if isinstance(children[0], Expression | MultiresExpression):
            self.condition: Expression = children[0]
        else:
            raise InternalCompilerError("Illegal 'if' statement: non-expression in condition.")
        if isinstance(children[1], BlockState):
            self.block: Block = children[1]
        else:
            raise InternalCompilerError("Illegal 'if' statement: non-block body.")

        self.elseifs: list[ElseIf] = []
        self.elze: BlockState | None = children[-1]
        for i in range(2, len(children) - 1):
            self.elseifs.append(children[i])

    def emit(self, state: _ProgramState):
        proto = state.proto

        skip_end_jump = not self.elze and len(self.elseifs) == 0
        self._emit_branch(state, self.condition, self.block, skip_end_jump)
        for i, el in enumerate(self.elseifs):
            self._emit_branch(state, el.condition, el.block, i == len(self.elseifs) - 1)
        if self.elze:
            state.push_block()
            self.elze.emit(state)
            state.pop_block()

        for jump_pc in self.end_jumps:
            proto.set_jump(jump_pc)

    def _emit_branch(
            self,
            state: _ProgramState,
            condition: Expression,
            block: Block,
            skip_end_jump: bool
    ):
        proto = state.proto
        evaluate_single(state, condition)
        proto.add_opcode("test")
        jump_pc = proto.reserve_opcodes(1)

        state.push_block()
        block.emit(state)
        state.pop_block()

        if not skip_end_jump:
            self.end_jumps.append(proto.pc)
            proto.reserve_opcodes(1)
        proto.set_jump(jump_pc)
