from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


class BreakStatement(Statement):
    def compile(self, state: CompilerState) -> None:
        state.add_break(self.meta)
