from dataclasses import dataclass

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


@dataclass
class RepeatStatement(Statement):
    body: Block
    condition: Expression

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
