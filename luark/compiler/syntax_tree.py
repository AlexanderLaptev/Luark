import math
from collections.abc import Callable
from dataclasses import dataclass

from lark import ast_utils, Transformer
from lark.visitors import Discard

from luark.compiler.errors import InternalCompilerError
from luark.compiler.program import Prototype


class CompilationError(RuntimeError):
    pass


class _Ast(ast_utils.Ast):
    def evaluate(self, *args, **kwargs):
        raise NotImplementedError


@dataclass
class Var(_Ast):
    name: str

    def evaluate(self, *args, **kwargs):
        proto = args[0]
        idx = proto.get_const(self.name)
        proto.add_opcode(f"global_load {idx}")


class NilValue(_Ast):
    def evaluate(self, *args, **kwargs):
        args[0].add_opcode("push_nil")


class TrueValue(_Ast):
    def evaluate(self, *args, **kwargs):
        args[0].add_opcode("push_true")


class FalseValue(_Ast):
    def evaluate(self, *args, **kwargs):
        args[0].add_opcode("push_true")


class Expr(_Ast):
    pass


@dataclass
class DotAccess(_Ast):
    primary: Expr
    name: str

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        self.primary.evaluate(*args, **kwargs)
        idx = proto.get_const(self.name)
        proto.add_opcode(f"push_int {idx}")
        proto.add_opcode(f"get_field")


@dataclass
class TableAccess(_Ast):
    primary: Expr
    expr: Expr

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        self.primary.evaluate(*args, **kwargs)
        self.expr.evaluate(*args, **kwargs)
        proto.add_opcode(f"get_field")


@dataclass
class String(Expr):
    value: str

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        idx = proto.get_const(self.value)
        proto.add_opcode(f"push_const {idx}")


@dataclass
class Number(Expr):
    value: int | float

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        if isinstance(self.value, int):
            proto.add_opcode(f"push_int {self.value}")
        elif isinstance(self.value, float):
            as_int = int(self.value)
            frac = self.value - int(self.value)
            if frac == 0:
                proto.add_opcode(f"push_float {as_int}")
            else:
                idx = proto.get_const(self.value)
                proto.add_opcode(f"push_const {idx}")
        else:
            raise Exception("Malformed number")


@dataclass
class BinOpExpr:
    op: str
    left: Expr
    right: Expr

    def evaluate(self, *args, **kwargs):
        proto = args[0]
        self.left.evaluate(*args, **kwargs)
        self.right.evaluate(*args, **kwargs)
        proto.add_opcode(self.op)


@dataclass
class FuncCall(_Ast):
    primary: Expr
    params: list[Expr] | None = None

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]

        if self.params:
            for e in self.params:
                e.evaluate(*args, **kwargs)

        self.primary.evaluate(*args, **kwargs)

        proto.add_opcode(f"call")


@dataclass
class AssignStmt(_Ast):
    var_list: list[str]
    expr_list: list[Expr]

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        nil_count = len(self.var_list) - len(self.expr_list)
        exprs: list[Expr | None] = self.expr_list
        for _ in range(nil_count):
            exprs.append(None)
        for v, e in zip(self.var_list, self.expr_list):
            if not e:
                proto.add_opcode("pushnil")
            else:
                e.evaluate(*args, **kwargs)
            idx = proto.get_const(v)
            proto.add_opcode(f"global_store {idx}")


@dataclass
class AttribName(_Ast):
    name: str
    attribute: str = None


@dataclass
class LocalStmt(_Ast):
    attrib_name_list: list[AttribName]
    expr_list: list[Expr] | None

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        raise Exception("TODO")


@dataclass
class Block(_Ast, ast_utils.AsList):
    stmts: list

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        for s in self.stmts:
            s.evaluate(proto)
        return proto


@dataclass
class Elseif(_Ast):
    expr: Expr
    block: Block


class IfStmt(_Ast, ast_utils.AsList):
    def __init__(self, children):
        self.expr: Expr = children[0]
        self.block: Block = children[1]
        self.elseifs: list[Elseif] = []
        self.elze: Block | None = None

        for i in range(2, len(children)):
            child = children[i]
            if isinstance(child, Elseif):
                self.elseifs.append(child)
            elif isinstance(child, Block):
                if self.elze:
                    raise InternalCompilerError("Extraneous 'else' block in if-statement.")
                self.elze = child
            else:
                raise InternalCompilerError("Malformed if-statement.")

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]

        blocks = [(self.block, self.expr), *((e.block, e.expr) for e in self.elseifs)]
        end_jumps = []

        for i, b in enumerate(blocks):
            b[1].evaluate(proto)
            proto.add_opcode("test")
            pc = proto.remember()
            b[0].evaluate(proto)
            if (i != len(blocks) - 1) or self.elze:
                end_jumps.append(proto.remember())
            proto.set_jump_here(pc)

        if self.elze:
            self.elze.evaluate(proto)

        for e in end_jumps:
            proto.set_jump_here(e)


@dataclass
class Chunk(_Ast):
    block: Block

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0].prototype
        self.block.evaluate(proto)
        proto.add_opcode("return")


# noinspection PyPep8Naming
class ToAst(Transformer):
    # def DEC_NUMBER(self, n):
    #     return float(n)
    #
    # def HEX_NUMBER(self, n):
    #     return float(n)

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

    def nil(self, c):
        return NilValue()

    def true(self, c):
        return TrueValue()

    def false(self, c):
        return FalseValue

    def ID(self, s):
        return str(s)

    def empty_stmt(self, c):
        return Discard

    def var_list(self, c):
        return [v.name for v in c]

    def attrib_name_list(self, c):
        return c

    def expr_list(self, c):
        return c

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
            return BinOpExpr(op, *c)

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
