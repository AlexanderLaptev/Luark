from abc import ABC
from dataclasses import dataclass

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


class ForLoop(ABC, Statement):
    pass


@dataclass
class NumericForLoop(ForLoop):
    control_variable_name: str
    initial_expression: Expression
    limit_expression: Expression
    step_expression: Expression | None
    body: Block

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError


@dataclass
class GenericForLoop(ForLoop):
    name_list: list[str]
    expression_list: ExpressionList
    body: Block

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
