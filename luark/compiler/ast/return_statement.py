from dataclasses import dataclass

from luark.compiler.ast.expressions import ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


@dataclass
class ReturnStatement(Statement):
    expression_list: ExpressionList

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
