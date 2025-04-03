from lark import Discard, Token, v_args
from lark.tree import Meta

from luark.compiler.ast import Block, Chunk
from luark.compiler.ast.constants import FalseValue, NilValue, TrueValue
from luark.compiler.ast.expression_transformer import ExpressionTransformer
from luark.compiler.ast.local_assignment_statement import (
    AttributedName
)
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.string import String
from luark.compiler.ast.variable import Variable


# noinspection PyPep8Naming
@v_args(inline=True)
class AstTransformer(ExpressionTransformer):
    def start(self, chunk: Chunk):
        return chunk

    @v_args(meta=True, inline=False)
    def block(self, _: Meta, statements: list[Statement]):
        return Block(statements)

    @v_args(meta=True, inline=True)
    def string(self, meta: Meta, token: Token):
        return String.of_token(meta, token)

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
