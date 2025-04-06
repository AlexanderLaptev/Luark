from collections.abc import Callable

from lark import Token, Transformer, v_args
from lark.tree import Meta

from luark.compiler.ast.constants import FalseValue, TrueValue
from luark.compiler.ast.expressions import BinaryExpression, Expression
from luark.compiler.ast.number import Number
from luark.compiler.ast.string import String
from luark.opcode.binary import BinaryOperation


@v_args(meta=True, inline=True)
class ExpressionTransformer(Transformer):
    _COMPARISON_LOOKUP = {
        "<": (BinaryOperation.LESS_THAN, lambda x, y: x < y),
        ">": (BinaryOperation.GREATER_THAN, lambda x, y: x > y),
        "<=": (BinaryOperation.LESS_OR_EQUAL, lambda x, y: x <= y),
        ">=": (BinaryOperation.GREATER_OR_EQUAL, lambda x, y: x >= y),
        "==": (BinaryOperation.EQUAL, lambda x, y: x == y),
        "!=": (BinaryOperation.NOT_EQUAL, lambda x, y: x != y),
    }

    _ARITHMETIC_LOOKUP = {
        "+": (BinaryOperation.ADD, lambda x, y: x + y),
        "-": (BinaryOperation.SUBTRACT, lambda x, y: x - y),
        "*": (BinaryOperation.MULTIPLY, lambda x, y: x * y),
        "/": (BinaryOperation.DIVIDE, lambda x, y: x / y),
        "//": (BinaryOperation.FLOOR_DIVIDE, lambda x, y: x // y),
        "%": (BinaryOperation.MODULO_DIVIDE, lambda x, y: x % y),
        "^": (BinaryOperation.EXPONENTIATE, lambda x, y: x ** y),
    }

    def or_expression(self, meta: Meta, left: Expression, right: Expression) -> Expression:
        if left == TrueValue.INSTANCE:
            return left
        return BinaryExpression(meta, left, right, BinaryOperation.OR)

    def and_expression(self, meta: Meta, left: Expression, right: Expression) -> Expression:
        if left == FalseValue.INSTANCE:
            return left
        return BinaryExpression(meta, left, right, BinaryOperation.AND)

    def comparison_expression(self, meta: Meta, left: Expression, sign: Token, right: Expression) -> Expression:
        operation, comparator = self._COMPARISON_LOOKUP[sign]
        return self._comparison(meta, left, right, comparator, operation)

    def add_expression(self, meta: Meta, left: Expression, sign: Token, right: Expression) -> Expression:
        operation, calculator = self._ARITHMETIC_LOOKUP[sign]
        return self._arithmetic(meta, left, right, calculator, operation)

    def mul_expression(self, meta: Meta, left: Expression, sign: Token, right: Expression) -> Expression:
        operation, calculator = self._ARITHMETIC_LOOKUP[sign]
        return self._arithmetic(meta, left, right, calculator, operation)

    def _comparison(
            self,
            meta: Meta,
            left: Expression,
            right: Expression,
            comparator: Callable[[int | float, int | float], bool],
            operation: BinaryOperation,
    ) -> Expression:
        if isinstance(left, Number) and isinstance(right, Number):
            result = comparator(left.value, right.value)
            return TrueValue.INSTANCE if result else FalseValue.INSTANCE
        return BinaryExpression(meta, left, right, operation)

    def _arithmetic(
            self,
            meta: Meta,
            left: Expression,
            right: Expression,
            calculator: Callable[[int | float, int | float], int | float],
            operation: BinaryOperation,
    ) -> Expression:
        if isinstance(left, Number) and isinstance(right, Number):
            result = calculator(left.value, right.value)
            return Number(meta, result)
        return BinaryExpression(meta, left, right, operation)

    def concat_expression(self, meta: Meta, left: Expression, right: Expression) -> Expression:
        if isinstance(left, String) and isinstance(right, String):
            return String(meta, left.value + right.value)
        else:
            return BinaryExpression(meta, left, right, BinaryOperation.CONCATENATE)
