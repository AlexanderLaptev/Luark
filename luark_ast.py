from dataclasses import dataclass
from typing import List

from lark import ast_utils, Transformer


class Prototype:
    def __init__(self):
        self.consts: List[str] = []
        self.opcodes: List[str] = []

    def __str__(self):
        result = ["constants:"]
        for i, c in enumerate(self.consts):
            name = str(c)
            if isinstance(c, str):
                name = '"' + name + '"'
            result.append(f"\t{i}\t\t{name}")
        result.append("instructions:")
        for i, o in enumerate(self.opcodes):
            result.append(f"\t{i}\t\t{o}")
        return "\n".join(result)

    def get_const(self, const):
        if const in self.consts:
            return self.consts.index(const)
        else:
            index = len(self.consts)
            self.consts.append(const)
            return index

    def add_opcode(self, opcode):
        self.opcodes.append(opcode)


class _Ast(ast_utils.Ast):
    def evaluate(self, *args, **kwargs):
        raise NotImplementedError


@dataclass
class Var(_Ast):
    name: str

    def evaluate(self, *args, **kwargs):
        proto = args[0]
        idx = proto.get_const(self.name)
        proto.add_opcode(f"load {idx}")


class Expr(_Ast):
    pass


@dataclass
class String(Expr):
    value: str

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        idx = proto.get_const(self.value)
        proto.add_opcode(f"pushc {idx}")


@dataclass
class Number(Expr):
    value: float

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        idx = proto.get_const(self.value)
        proto.add_opcode(f"pushc {idx}")


@dataclass
class ExprList(_Ast, ast_utils.AsList):
    exprs: List[Expr]

    def evaluate(self, *args, **kwargs):
        for e in self.exprs:
            e.evaluate(*args, **kwargs)


@dataclass
class AddExpr(Expr):
    left: Expr
    right: Expr

    def evaluate(self, *args, **kwargs):
        proto = args[0]
        if (isinstance(self.left, Number)
                and isinstance(self.right, Number)):
            result = self.left.value + self.right.value
            idx = proto.get_const(result)
            proto.add_opcode(f"pushc {idx}")
        else:
            self.left.evaluate(*args, **kwargs)
            self.right.evaluate(*args, **kwargs)
            proto.add_opcode("add")


@dataclass
class FuncCall(_Ast):
    primary: str
    params: ExprList = None

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        my_idx = proto.get_const(self.primary)

        # exprs = self.params.evaluate(*args, **kwargs)
        # for e in exprs:
        #     idx = proto.get_const(e)
        #     proto.add_opcode(f"load {idx}")

        # for p in self.params:
        #     p.evaluate(*args, **kwargs)

        if self.params:
            self.params.evaluate(*args, **kwargs)

        proto.add_opcode(f"call {my_idx}")


@dataclass
class AssignStmt(_Ast):
    var_list: List[str]
    expr_list: ExprList

    def evaluate(self, *args, **kwargs):
        proto: Prototype = args[0]
        self.expr_list.evaluate(*args, **kwargs)
        for v in self.var_list[::-1]:
            idx = proto.get_const(v)
            proto.add_opcode(f"store {idx}")


@dataclass
class Chunk(_Ast, ast_utils.AsList):
    stmts: List[FuncCall]

    def evaluate(self, *args, **kwargs):
        proto = Prototype()
        for s in self.stmts:
            s.evaluate(proto)
        proto.add_opcode("return")
        print(proto)


class ToAst(Transformer):
    def DEC_NUMBER(self, n):
        return float(n)

    def HEX_NUMBER(self, n):
        return float(n)

    def STRING(self, s):
        return (str(s)[1:-1]
                .replace("\\z\n", "")
                .replace("\\n", "\n"))

    def MULTISTRING(self, s):
        s = str(s)
        size = s.find("[", 1) + 1
        return s[size:-size]

    def ID(self, s):
        return str(s)

    def var_list(self, l):
        return [v.name for v in l]
