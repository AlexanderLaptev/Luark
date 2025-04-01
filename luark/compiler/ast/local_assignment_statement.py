from dataclasses import dataclass

from luark.compiler.ast.expressions import ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


@dataclass
class AttributedName:
    name: str
    attribute: str


@dataclass
class LocalAssignmentStatement(Statement):
    attributed_names: list[AttributedName]
    expression_list: ExpressionList | None

    def compile(self, state: CompilerState) -> None:
        pass
