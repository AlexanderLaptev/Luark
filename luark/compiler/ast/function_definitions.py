from dataclasses import dataclass

from luark.compiler.ast.assignment_statement import AssignmentStatement
from luark.compiler.ast.ast_node import AstNode
from luark.compiler.ast.block import Block
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.return_statement import ReturnStatement
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.variable import DotAccess, Lvalue, Variable
from luark.compiler.compiler_state import CompilerState
from luark.opcode.closure import Closure
from luark.opcode.return_opcode import Return


@dataclass
class ParameterList:
    names: list[str]
    has_varargs: bool


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
        param_count = 0
        is_variadic = False
        if params:
            param_count = len(params.names)
            is_variadic = params.has_varargs

        proto = state.begin_proto(name, param_count, is_variadic)
        state.begin_block()

        statements = self.body.block.statements
        if statements:
            last = statements[-1]
            for stmt in self.body.block.statements[:-1]:
                stmt.compile(state)
            last.compile(state)
            if not isinstance(last, ReturnStatement):
                state.add_opcode(Return(1))
        else:
            state.add_opcode(Return(1))

        state.end_block()
        state.end_proto()

        if create_closure:
            state.add_opcode(Closure(proto))


@dataclass
class FunctionName:
    names: list[str]
    is_method: bool


@dataclass
class FunctionDefinitionStatement(Statement):
    name: FunctionName
    body: FunctionBody

    def compile(self, state: CompilerState) -> None:
        names = self.name.names
        lvalue: Lvalue
        if len(names) == 1:
            lvalue = Variable(self.meta, names[0])
        else:
            lvalue = Variable(self.meta, names[0])
            for name in names[1:]:
                lvalue = DotAccess(self.meta, lvalue, name)

        params = self.body.parameter_list
        if not params:
            param_names = []
            if self.name.is_method:
                param_names.append("self")
            param_list = ParameterList(param_names, False)
        else:
            param_names: list[str]
            if params:
                if self.name.is_method:
                    param_names = ["self", *params.names]
                else:
                    param_names = params.names
            else:
                param_names = []
            param_list = ParameterList(param_names, params.has_varargs)

        func_def = FunctionDefinition(
            self.meta,
            FunctionBody(self.meta, param_list, self.body.block),
            names[-1]
        )
        assignment = AssignmentStatement(
            self.meta,
            [lvalue],
            ExpressionList(self.meta, [func_def])
        )
        assignment.compile(state)


@dataclass
class LocalFunctionDefinitionStatement(FunctionDefinitionStatement):
    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
