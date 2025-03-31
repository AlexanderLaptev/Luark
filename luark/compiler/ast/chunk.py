from dataclasses import dataclass

from luark.compiler.ast.block import Block
from luark.compiler.compiler_state import CompilerState


@dataclass
class Chunk:
    block: Block

    def compile(self, state: CompilerState):
        state.begin_chunk()
        for statement in self.block.statements:
            statement.compile(state)
        state.end_chunk()
