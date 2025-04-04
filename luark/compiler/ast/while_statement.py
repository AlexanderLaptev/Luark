from dataclasses import dataclass

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.opcode.test import Test


@dataclass
class WhileStatement(Statement):
    condition: Expression
    body: Block

    def compile(self, state: CompilerState) -> None:
        loop_start_pc = state.program_counter
        self.condition.evaluate(state)
        state.add_opcode(Test.INSTANCE)
        jump_pc = state.reserve_opcode()

        state.begin_block()
        state.begin_loop()

        for statement in self.body.statements:
            statement.compile(state)
        state.add_jump(loop_start_pc)
        block_end_pc = state.program_counter
        state.set_jump(jump_pc, block_end_pc)

        state.end_loop()
        state.end_block()
