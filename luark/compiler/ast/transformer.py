from lark import Discard, Token, v_args
from lark.tree import Meta

from luark.compiler.ast import Block, Chunk
from luark.compiler.ast.constants import FalseValue, NilValue, TrueValue
from luark.compiler.ast.expression_transformer import ExpressionTransformer
from luark.compiler.ast.expressions import (
    Expression,
    ExpressionList
)
from luark.compiler.ast.for_loops import GenericForLoop, NumericForLoop
from luark.compiler.ast.if_statement import ElseIf, IfStatement
from luark.compiler.ast.local_assignment_statement import (
    AttributedName
)
from luark.compiler.ast.string import String
from luark.compiler.ast.variable import Variable
from luark.compiler.exceptions import InternalCompilerError


# noinspection PyPep8Naming
# TODO: move custom logic into constructors
class LuarkTransformer(ExpressionTransformer):
    def start(self, chunk: Chunk):
        return chunk

    @v_args(meta=True, inline=True)
    def string(self, meta: Meta, token: Token):
        return String.of_token(token, meta)

    # noinspection PyShadowingBuiltins
    def var_list(self, vars: list[Variable]) -> list[Variable]:
        return vars

    def true(self, _) -> TrueValue:
        return TrueValue.INSTANCE

    def false(self, _) -> FalseValue:
        return FalseValue.INSTANCE

    def nil(self, _) -> NilValue:
        return NilValue.INSTANCE

    def empty_statement(self) -> Discard:
        return Discard

    @v_args(inline=False)
    def attributed_name_list(
            self,
            names: list[AttributedName]
    ) -> list[AttributedName]:
        return names

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
