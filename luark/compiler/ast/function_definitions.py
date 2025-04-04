from dataclasses import dataclass

from lark.ast_utils import AsList
from lark.tree import Meta

from luark.compiler.ast.ast_node import AstNode
from luark.compiler.ast.block import Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.return_statement import ReturnStatement
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.varargs import Varargs
from luark.compiler.compiler_state import CompilerState
from luark.opcode.return_opcode import Return


@dataclass
class ParameterList(AstNode, AsList):
    names: list[str]
    has_varargs: bool

    def __init__(self, meta: Meta, params: list):
        self.meta = meta
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
class FunctionBody(AstNode):
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

        statements = self.body.block.statements
        if statements:
            last = statements[-1]
            for stmt in self.body.block.statements[:-1]:
                stmt.compile(state)
            if isinstance(last, ReturnStatement):
                last.compile(state)
            else:
                state.add_opcode(Return(1))
        else:
            state.add_opcode(Return(1))

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
