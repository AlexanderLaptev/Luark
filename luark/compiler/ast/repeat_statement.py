from dataclasses import dataclass

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.opcode.test import Test


@dataclass
class RepeatStatement(Statement):
    body: Block
    condition: Expression

    def compile(self, state: CompilerState) -> None:
        state.begin_block()
        state.begin_loop()

        loop_start_pc = state.program_counter
        for statement in self.body.statements:
            statement.compile(state)

        self.condition.evaluate(state)
        state.add_opcode(Test.INSTANCE)
        state.add_jump(loop_start_pc)

        state.end_loop()
        state.end_block()
