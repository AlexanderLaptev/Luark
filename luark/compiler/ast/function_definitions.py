from dataclasses import dataclass
from typing import Self

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.varargs import Varargs
from luark.compiler.compiler_state import CompilerState


@dataclass
class ParameterList:
    names: list[str]
    has_varargs: bool

    def __init__(self, params: list):
        self.has_varargs = False

        if params:
            last = params[-1]
            if isinstance(last, Varargs):
                self.has_varargs = True
                self.names = params[:-1]
            else:
                self.names = params
        else:
            self.names = []

    @classmethod
    def of_varargs(cls) -> Self:
        return ParameterList([Varargs()])


@dataclass
class FunctionBody:
    parameter_list: ParameterList
    block: Block


@dataclass
class FunctionDefinition(Expression):
    body: FunctionBody
    name: str = None

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


@dataclass
class FunctionName:
    names: list[str]
    is_method: bool


@dataclass
class FunctionDefinitionStatement(Statement):
    function_name: FunctionName
    function_body: FunctionBody

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError


@dataclass
class LocalFunctionDefinitionStatement(FunctionDefinitionStatement):
    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
