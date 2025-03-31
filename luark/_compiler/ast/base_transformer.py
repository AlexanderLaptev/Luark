from typing import Callable

from lark import Transformer, Token, Discard, v_args

from luark.compiler.ast.expressions import Number, NilValue, TrueValue, FalseValue, Expression, BinaryOpExpression, \
    String, UnaryExpression
from luark.compiler.ast.local_assignment import AttribName
from luark.compiler.ast.variables import Var, DotAccess, TableAccess
from luark.compiler.errors import InternalCompilerError


# noinspection PyPep8Naming
class LuarkTransformer(Transformer):
    def start(self, children):
        return children[-1]

    def dec_int(self, n):
        num: str = n[0]
        num: list[str] = num.casefold().split("e")
        if len(num) == 1:
            return Number(int(num[0]))
        elif len(num) == 2:
            return Number(int(num[0]) * 10 ** int(num[1]))
        else:
            raise InternalCompilerError(f"Illegal decimal integer literal: '{n}'")

    def dec_float(self, f):
        num: str = f[0]
        num: list[str] = num.casefold().split("e")
        if len(num) == 1:
            return Number(float(num[0]))
        elif len(num) == 2:
            return Number(float(num[0]) * 10 ** float(num[1]))
        else:
            raise InternalCompilerError(f"Illegal decimal float literal: '{f}'")

    def hex_number(self, n: list[Token]):
        return Number(float.fromhex(n[0].value))

    def empty_stmt(self, _):
        return Discard

    def nil(self, _):
        return NilValue.instance

    def true(self, _):
        return TrueValue.instance

    def false(self, _):
        return FalseValue.instance

    def expr_list(self, exprs) -> list[Expression]:
        return exprs

    def var_list(self, varz) -> list[Var | DotAccess | TableAccess]:
        return varz

    def attrib_name_list(self, names) -> list[AttribName]:
        return names

    def STRING(self, c):
        return c

    def MULTISTRING(self, c):
        return c

    def ID(self, s):
        return str(s)

    def _bin_num_op_expr(self, c: list, op: str, func: Callable):
        if isinstance(c[0], Number) and isinstance(c[1], Number):
            try:
                return Number(func(c[0].value, c[1].value))
            except ArithmeticError:
                return BinaryOpExpression(op, *c)
        else:
            return BinaryOpExpression(op, *c)

    def or_expr(self, c):
        return BinaryOpExpression("or", *c)

    def and_expr(self, c):
        return BinaryOpExpression("and", *c)

    def comp_lt(self, c):
        return BinaryOpExpression("lt", *c)

    def comp_gt(self, c):
        return BinaryOpExpression("gt", *c)

    def comp_le(self, c):
        return BinaryOpExpression("le", *c)

    def comp_ge(self, c):
        return BinaryOpExpression("ge", *c)

    def comp_eq(self, c):
        return BinaryOpExpression("eq", *c)

    def comp_neq(self, c):
        return BinaryOpExpression("neq", *c)

    def bw_or_expr(self, c):
        return BinaryOpExpression("bor", *c)

    def bw_xor_expr(self, c):
        return BinaryOpExpression("bxor", *c)

    def bw_and_expr(self, c):
        return BinaryOpExpression("band", *c)

    def lsh_expr(self, c):
        return BinaryOpExpression("lsh", *c)

    def rsh_expr(self, c):
        return BinaryOpExpression("rsh", *c)

    @v_args(meta=True)
    def concat_expr(self, meta, c):
        if (isinstance(c[0], String)
                and isinstance(c[1], String)):
            return String(meta, c[0].value + c[1].value)
        else:
            return BinaryOpExpression("concat", *c)

    def add_expr(self, c):
        return self._bin_num_op_expr(c, "add", lambda x, y: x + y)

    def sub_expr(self, c):
        return self._bin_num_op_expr(c, "sub", lambda x, y: x - y)

    def mul_expr(self, c):
        return self._bin_num_op_expr(c, "mul", lambda x, y: x * y)

    def div_expr(self, c):
        return self._bin_num_op_expr(c, "div", lambda x, y: x / y)

    def fdiv_expr(self, c):
        return self._bin_num_op_expr(c, "fdiv", lambda x, y: x // y)

    def mod_expr(self, c):
        return self._bin_num_op_expr(c, "mod", lambda x, y: x % y)

    def unary_minus(self, c):
        if isinstance(c[0], Number):
            return Number(-c[0].value)
        else:
            return UnaryExpression("negate")

    def unary_not(self, _):
        return UnaryExpression("not")

    def unary_length(self, _):
        return UnaryExpression("len")

    def unary_bw_not(self, _):
        return UnaryExpression("bnot")

    def exp_expr(self, c):
        return self._bin_num_op_expr(c, "exp", lambda x, y: x ** y)
