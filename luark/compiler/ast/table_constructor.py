from dataclasses import dataclass

from luark.compiler.ast.expressions import Expression
from luark.compiler.compiler_state import CompilerState


class Field:
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
