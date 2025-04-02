from lark import Discard, Token, v_args
from lark.tree import Meta

from luark.compiler.ast import Block, Chunk
from luark.compiler.ast.assignment_statement import AssignmentStatement
from luark.compiler.ast.break_statement import BreakStatement
from luark.compiler.ast.constants import FalseValue, NilValue, TrueValue
from luark.compiler.ast.expression_transformer import ExpressionTransformer
from luark.compiler.ast.expressions import (
    Expression,
    ExpressionList
)
from luark.compiler.ast.for_loops import GenericForLoop, NumericForLoop
from luark.compiler.ast.function_calls import (
    FunctionCall,
    FunctionCallParameters, FunctionCallStatement, MethodCall
)
from luark.compiler.ast.function_definitions import (
    FunctionBody, FunctionDefinition, FunctionDefinitionStatement,
    FunctionName, LocalFunctionDefinitionStatement, ParameterList
)
from luark.compiler.ast.goto_statement import GotoStatement
from luark.compiler.ast.if_statement import ElseIf, IfStatement
from luark.compiler.ast.label import Label
from luark.compiler.ast.local_assignment_statement import (
    AttributedName,
    LocalAssignmentStatement
)
from luark.compiler.ast.number import Number
from luark.compiler.ast.repeat_statement import RepeatStatement
from luark.compiler.ast.return_statement import ReturnStatement
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.string import String
from luark.compiler.ast.table_constructor import (
    ExpressionField, Field,
    NameField, TableConstructor
)
from luark.compiler.ast.varargs import Varargs
from luark.compiler.ast.variable import Variable
from luark.compiler.ast.while_statement import WhileStatement
from luark.compiler.exceptions import InternalCompilerError


# noinspection PyPep8Naming
@v_args(inline=True)
class LuarkTransformer(ExpressionTransformer):
    def start(self, chunk: Chunk):
        return chunk

    def chunk(self, block: Block):
        return Chunk(block)

    @v_args(inline=False)
    def block(self, statements: list[Statement]):
        return Block(statements)

    def number(self, number: int):
        return Number(number)

    @v_args(meta=True, inline=True)
    def string(self, meta: Meta, token: Token):
        return String.of_token(token, meta)

    def varargs(self, _):
        return Varargs()

    def var(self, name: str):
        return Variable(name)

    # noinspection PyShadowingBuiltins
    @v_args(inline=False)
    def var_list(self, vars: list[Variable]) -> list[Variable]:
        return vars

    @v_args(inline=False)
    def table_constructor(self, fields: list[Field]) -> TableConstructor:
        return TableConstructor(fields)

    def expression_field(self, key: Expression, value: Expression) -> ExpressionField:
        return ExpressionField(key, value)

    def name_field(self, name: str, value: Expression) -> NameField:
        return NameField(name, value)

    def true(self, _) -> TrueValue:
        return TrueValue.INSTANCE

    def false(self, _) -> FalseValue:
        return FalseValue.INSTANCE

    def nil(self, _) -> NilValue:
        return NilValue.INSTANCE

    @v_args(inline=False)
    def expression_list(self, expressions: list[Expression]) -> ExpressionList:
        return ExpressionList(expressions)

    def empty_statement(self) -> Discard:
        return Discard

    @v_args(meta=True)
    def while_statement(
            self,
            meta: Meta,
            condition: Expression,
            body: Block
    ) -> WhileStatement:
        return WhileStatement(meta, condition, body)

    @v_args(meta=True)
    def repeat_statement(
            self,
            meta: Meta,
            body: Block,
            condition: Expression
    ) -> RepeatStatement:
        return RepeatStatement(meta, body, condition)

    @v_args(meta=True)
    def break_statement(self, meta: Meta, _) -> BreakStatement:
        return BreakStatement(meta)

    @v_args(meta=True)
    def label(self, meta: Meta, name: str) -> Label:
        return Label(meta, name)

    @v_args(meta=True)
    def goto_statement(self, meta: Meta, target_label: str) -> GotoStatement:
        return GotoStatement(meta, target_label)

    @v_args(meta=True)
    def return_statement(
            self,
            meta: Meta,
            expression_list: ExpressionList
    ) -> ReturnStatement:
        return ReturnStatement(meta, expression_list)

    @v_args(meta=True, inline=True)
    def assignment_statement(
            self,
            meta: Meta,
            var_list: list[Variable],
            expression_list: ExpressionList
    ):
        return AssignmentStatement(meta, var_list, expression_list)

    @v_args(meta=True, inline=True)
    def local_assignment_statement(
            self,
            meta: Meta,
            names: list[AttributedName],
            expression_list: ExpressionList | None = None
    ) -> LocalAssignmentStatement:
        return LocalAssignmentStatement(meta, names, expression_list)

    @v_args(inline=False)
    def attributed_name_list(
            self,
            names: list[AttributedName]
    ) -> list[AttributedName]:
        return names

    def attributed_name(self, name: str, attribute: str) -> AttributedName:
        return AttributedName(name, attribute)

    def function_call_parameters(
            self,
            parameters: ExpressionList | TableConstructor | String | None = None
    ) -> FunctionCallParameters:
        return FunctionCallParameters(parameters)

    def function_call(
            self,
            primary: Expression,
            parameters: FunctionCallParameters
    ) -> FunctionCall:
        return FunctionCall(primary, parameters)

    def method_call(
            self,
            primary: Expression,
            method_name: str,
            parameters: FunctionCallParameters
    ) -> MethodCall:
        return MethodCall(primary, method_name, parameters)

    @v_args(meta=True, inline=True)
    def function_call_statement(
            self,
            meta: Meta,
            function_call: FunctionCall
    ) -> FunctionCallStatement:
        return FunctionCallStatement(meta, function_call)

    def function_definition(self, body: FunctionBody):
        return FunctionDefinition(body)

    def function_body(self, param_list: ParameterList | None, block: Block):
        return FunctionBody(param_list, block)

    @v_args(inline=False)
    def parameter_list(self, children: list):
        return ParameterList(children)

    @v_args(inline=False)
    def function_name(self, names: list[str]) -> FunctionName:
        return FunctionName(names, is_method=False)

    @v_args(inline=False)
    def method_name(self, names: list[str]) -> FunctionName:
        return FunctionName(names, is_method=True)

    @v_args(meta=True, inline=True)
    def function_definition_statement(
            self,
            meta: Meta,
            function_name: FunctionName,
            function_body: FunctionBody
    ) -> FunctionDefinitionStatement:
        return FunctionDefinitionStatement(meta, function_name, function_body)

    @v_args(meta=True, inline=True)
    def local_function_definition_statement(
            self,
            meta: Meta,
            function_name: FunctionName,
            function_body: FunctionBody
    ) -> LocalFunctionDefinitionStatement:
        return LocalFunctionDefinitionStatement(
            meta,
            function_name,
            function_body
        )

    @v_args(meta=True, inline=False)
    def if_statement(self, meta: Meta, children: list):
        condition: Expression = children[0]
        body: Block = children[1]
        else_if_branches: list[ElseIf]
        else_branch: Block | None = None

        if isinstance(children[-1], Block):
            else_if_branches = children[2:-1]
            else_branch = children[-1]
        else:
            else_if_branches = children[2:]

        return IfStatement(meta, condition, body, else_if_branches, else_branch)

    def else_if(self, condition: Expression, body: Block) -> ElseIf:
        return ElseIf(condition, body)

    @v_args(meta=True, inline=False)
    def numeric_for_loop(self, meta: Meta, children: list) -> NumericForLoop:
        control: str = children[0]
        initial: Expression = children[1]
        limit: Expression = children[2]

        step: Expression | None = None
        body: Block
        if len(children) == 4:
            body = children[3]
        elif len(children) == 5:
            step = children[3]
            body = children[4]
        else:
            raise InternalCompilerError(f"invalid children ({len(children)}) for numeric for loop")

        return NumericForLoop(meta, control, initial, limit, step, body)

    @v_args(meta=True, inline=False)
    def generic_for_loop(self, meta: Meta, children: list) -> GenericForLoop:
        name_list: list[str] = children[:-2]
        expression_list: ExpressionList = children[-2]
        body: Block = children[-1]
        return GenericForLoop(meta, name_list, expression_list, body)

    def DECIMAL_INT(self, number: str) -> int:
        return int(number, 10)

    def DECIMAL_FLOAT(self, number: str) -> float:
        return float(number)

    def HEX_INT(self, number: str) -> int:
        number = number.casefold()
        left, right = number.split("p")
        result = int(left, 16)
        if right:
            exponent = int(right, 10)
            result *= 2 ** exponent
        return result

    def HEX_FLOAT(self, number: str) -> float:
        return float.fromhex(number)

    # noinspection PyShadowingBuiltins
    def ID(self, id: str) -> str:
        return str(id)
