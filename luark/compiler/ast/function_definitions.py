from dataclasses import dataclass

from luark.compiler.ast.assignment_statement import AssignmentStatement
from luark.compiler.ast.ast_node import AstNode
from luark.compiler.ast.block import Block
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.local_assignment_statement import AttributedName
from luark.compiler.ast.local_assignment_statement import LocalAssignmentStatement
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
        func_names = self.name.names
        lvalue: Lvalue
        if len(func_names) == 1:
            lvalue = Variable(self.meta, func_names[0])
        else:
            lvalue = Variable(self.meta, func_names[0])
            for name in func_names[1:]:
                lvalue = DotAccess(self.meta, lvalue, name)

        old_param_list = self.body.parameter_list
        old_param_names = old_param_list.names if old_param_list else []
        new_param_names = ["self", *old_param_names] if self.name.is_method else old_param_names
        new_varargs = old_param_list.has_varargs if old_param_list else False
        new_param_list = ParameterList(new_param_names, new_varargs)

        func_def = FunctionDefinition(
            self.meta,
            FunctionBody(self.meta, new_param_list, self.body.block),
            func_names[-1]
        )
        assignment = AssignmentStatement(
            self.meta,
            [lvalue],
            ExpressionList(self.meta, [func_def])
        )
        assignment.compile(state)


@dataclass
class LocalFunctionDefinitionStatement(Statement):
    name: str
    body: FunctionBody

    def compile(self, state: CompilerState) -> None:
        func_def = FunctionDefinition(
            self.meta,
            FunctionBody(self.meta, self.body.parameter_list, self.body.block),
            self.name
        )
        assignment = LocalAssignmentStatement(
            self.meta,
            [AttributedName(self.meta, self.name, None)],
            ExpressionList(self.meta, [func_def])
        )
        assignment.compile(state)
