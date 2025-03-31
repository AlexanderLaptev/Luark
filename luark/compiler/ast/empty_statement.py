from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


class EmptyStatement(Statement):
    def compile(self, state: CompilerState) -> None:
        return
