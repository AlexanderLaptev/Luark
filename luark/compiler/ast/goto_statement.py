from dataclasses import dataclass

from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


@dataclass
class Label(Statement):
    name: str
    is_trailing: bool = False

    def compile(self, state: CompilerState) -> None:
        state.add_label(self.meta, self.name, self.is_trailing)


@dataclass
class GotoStatement(Statement):
    target_label: str

    def compile(self, state: CompilerState) -> None:
        state.add_goto(self.meta, self.target_label)
