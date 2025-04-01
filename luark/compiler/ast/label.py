from dataclasses import dataclass

from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


@dataclass
class Label(Statement):
    name: str

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
