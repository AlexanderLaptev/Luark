from dataclasses import dataclass

from lark.ast_utils import AsList
from lark.tree import Meta

from luark.compiler.ast import AstNode, Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.opcode.test import Test


@dataclass
class ElseIf(AstNode):
    condition: Expression
    body: Block


@dataclass
class IfStatement(Statement, AsList):
    condition: Expression
    body: Block
    else_if_branches: list[ElseIf]
    else_branch: Block | None

    def __init__(self, meta: Meta, children: list):
        self.meta = meta
        self.condition = children[0]
        self.body = children[1]

        children = children[2:]
        if not children:
            self.else_if_branches = []
            self.else_branch = None
            return

        if isinstance(children[-1], Block):
            self.else_if_branches = children[:-1]
            self.else_branch = children[-1]
        else:
            self.else_if_branches = children
            self.else_branch = None

    def compile(self, state: CompilerState) -> None:
        skip_end_jump = (not self.else_branch) and len(self.else_if_branches) == 0
        end_jumps = []
        self._emit_branch(state, self.condition, self.body, skip_end_jump, end_jumps)
        for i, branch in enumerate(self.else_if_branches):
            self._emit_branch(
                state,
                branch.condition,
                branch.body,
                skip_end_jump,
                end_jumps
            )
        if self.else_branch:
            state.begin_block()
            for stmt in self.else_branch.statements:
                stmt.compile(state)
            state.end_block()

        for jump_pc in end_jumps:
            state.set_jump(jump_pc)

    def _emit_branch(
            self,
            state: CompilerState,
            condition: Expression,
            block: Block,
            skip_end_jump: bool,
            end_jumps: list[int]
    ):
        condition.evaluate(state)
        state.add_opcode(Test.INSTANCE)
        jump_pc = state.reserve_opcode()

        state.begin_block()
        for stmt in block.statements:
            stmt.compile(state)
        state.end_block()

        if not skip_end_jump:
            end_jumps.append(state.program_counter)
            state.reserve_opcode()
        state.set_jump(jump_pc)
