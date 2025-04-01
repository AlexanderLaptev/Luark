from dataclasses import dataclass

from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.string import String
from luark.compiler.ast.table_constructor import TableConstructor
from luark.compiler.compiler_state import CompilerState


@dataclass
class FunctionCallParameters:
    parameters: ExpressionList | TableConstructor | String | None = None


@dataclass
class FunctionCall(Expression):
    primary: Expression
    parameters: FunctionCallParameters

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


@dataclass
class MethodCall(FunctionCall):
    method_name: str

    def __init__(self, primary: Expression, method_name: str, parameters: FunctionCallParameters):
        super().__init__(primary, parameters)
        self.method_name = method_name

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


@dataclass
class FunctionCallStatement(Statement):
    function_call: FunctionCall

    def compile(self, state: CompilerState) -> None:
        raise None
