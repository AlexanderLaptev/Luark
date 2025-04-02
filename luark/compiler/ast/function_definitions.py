from dataclasses import dataclass

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


@dataclass
class FunctionBody:
    parameter_list: ParameterList
    block: Block


@dataclass
class FunctionDefinition(Expression):
    body: FunctionBody
    name: str | None = None

    def evaluate(
            self,
            state: CompilerState,
            create_closure: bool = True
    ) -> None:
        name: str = self.name
        if self.name is None:
            name = f"<lambda#{state.next_lambda_index()}>"

        params = self.body.parameter_list
        param_count: int = len(params.names)
        is_variadic: bool = params.has_varargs

        state.begin_proto(name, param_count, is_variadic)
        state.begin_block()
        for statement in self.body.block.statements:
            statement.compile(state)
        state.end_block()
        state.end_proto()


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
