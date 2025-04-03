from dataclasses import dataclass

from luark.compiler.ast.expressions import Expression
from luark.compiler.compiler_state import CompilerState


@dataclass
class Variable(Expression):
    name: str

    def evaluate(self, state: CompilerState) -> None:
        state.resolve_variable(self.name, "read")
