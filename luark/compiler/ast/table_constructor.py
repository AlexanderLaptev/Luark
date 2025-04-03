from dataclasses import dataclass

from luark.compiler.ast import AstNode
from luark.compiler.ast.expressions import Expression
from luark.compiler.compiler_state import CompilerState


class Field(AstNode):
    pass


@dataclass
class ExpressionField(Field):
    key: Expression
    value: Expression


@dataclass
class NameField(Field):
    name: str
    value: Expression


@dataclass
class TableConstructor(Expression):
    fields: list[Field]

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError
