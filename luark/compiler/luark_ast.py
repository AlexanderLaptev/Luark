import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from lark.ast_utils import Ast, AsList
from lark.visitors import Transformer, Discard

from luark.compiler.program import Program, Prototype


class _State:
    def __init__(self, program: Program):
        self.program = program
        self.proto = program.main_proto


class Statement(ABC):
    @abstractmethod
    def emit(self, state: _State):
        pass


class Expression(ABC):
    @abstractmethod
    def evaluate(self, state: _State):
        pass


@dataclass
class String(Ast, Expression):
    value: str

    def evaluate(self, state: _State):
        pass


@dataclass
class Number(Ast, Expression):
    value: int | float

    def evaluate(self, state: _State):
        pass


class NilValue(Expression):
    def evaluate(self, state: _State):
        pass


class TrueValue(Expression):
    def evaluate(self, state: _State):
        pass


class FalseValue(Expression):
    def evaluate(self, state: _State):
        pass


@dataclass
class Block(Ast, AsList):
    statements: list

    def emit(self, state: _State):
        for statement in self.statements:
            statement.emit(state)


@dataclass
class BinaryOpExpression(Expression):
    opcode: str
    left: Expression
    right: Expression

    def evaluate(self, state: _State):
        self.left.evaluate(state)
        self.right.evaluate(state)
        # state.add_opcode(self.opcode)


@dataclass
class Chunk(Ast):
    block: Block

    def emit(self):
        main_proto = Prototype()
        program = Program(main_proto)
        state = _State(program)
        self.block.emit(state)
        pass


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
            raise Exception(f"Illegal decimal integer literal: '{n}'")

    def dec_float(self, f):
        num: str = f[0]
        num: list[str] = num.casefold().split("e")
        if len(num) == 1:
            return Number(float(num[0]))
        elif len(num) == 2:
            return Number(float(num[0]) * 10 ** float(num[1]))
        else:
            raise Exception(f"Illegal decimal float literal: '{f}'")

    def empty_stmt(self, _):
        return Discard

    def nil(self, _):
        return NilValue()

    def true(self, _):
        return TrueValue()

    def false(self, _):
        return FalseValue()

    def ID(self, s):
        return str(s)

    # TODO: raise error on unknown escape sequences
    # TODO: support \xXX, \ddd, \u{XXX}
    def STRING(self, s):
        s = ''.join([s.strip() for s in s.split("\\z")])
        s = (str(s)[1:-1]
             .replace("\\a", "\a")
             .replace("\\b", "\b")
             .replace("\\f", "\f")
             .replace("\\n", "\n")
             .replace("\\r", "\r")
             .replace("\\t", "\t")
             .replace("\\v", "\v")
             .replace("\\\\", "\\")
             .replace("\\\"", "\"")
             .replace("\\\'", "\'")
             .replace("\\\n", "\n"))
        return s

    def MULTISTRING(self, s):
        raise NotImplementedError
        # s = str(s)
        # size = s.find("[", 1) + 1
        # return s[size:-size]

    def concat_expr(self, c):
        if (isinstance(c[0], String)
                and isinstance(c[1], String)):
            return String(c[0].value + c[1].value)
        else:
            raise NotImplementedError

    def _bin_num_op_expr(self, c: list, op: str, func: Callable):
        if (isinstance(c[0], Number)
                and isinstance(c[1], Number)):
            return Number(func(c[0].value, c[1].value))
        else:
            return BinaryOpExpression(op, *c)

    # TODO: optimize `or true`, `and false`

    def add_expr(self, c):
        return self._bin_num_op_expr(c, "add", lambda x, y: x + y)

    def sub_expr(self, c):
        return self._bin_num_op_expr(c, "sub", lambda x, y: x - y)

    def mul_expr(self, c):
        return self._bin_num_op_expr(c, "mul", lambda x, y: x * y)

    def div_expr(self, c):
        return self._bin_num_op_expr(c, "div", lambda x, y: x / y)

    def fdiv_expr(self, c):
        return self._bin_num_op_expr(c, "fdiv", lambda x, y: math.floor(x / y))

    def mod_expr(self, c):
        return self._bin_num_op_expr(c, "mod", lambda x, y: x % y)

    def exp_expr(self, c):
        return self._bin_num_op_expr(c, "exp", lambda x, y: x ** y)

    def unary_minus(self, c):
        if isinstance(c[0], Number):
            return Number(-c[0].value)
        else:
            raise NotImplementedError
