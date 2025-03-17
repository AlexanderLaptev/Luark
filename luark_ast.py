import math
from dataclasses import dataclass
from typing import List

from lark import ast_utils, Transformer

environment = {}


class _Ast(ast_utils.Ast):
    def evaluate(self):
        raise NotImplementedError


class Statement(_Ast):
    pass


class NameList(_Ast):
    pass


class Field(_Ast):
    pass


class FieldList(_Ast):
    pass


class TableConstructor(_Ast):
    pass


class Expr(_Ast):
    pass


@dataclass
class Var(Expr):
    name: str

    def evaluate(self):
        return environment.get(self.name, None)


@dataclass
class Number(Expr):
    value: float

    def evaluate(self):
        return self.value


@dataclass
class String(Expr):
    value: str

    def evaluate(self):
        return self.value


@dataclass
class BinaryOp:
    left: Expr
    right: Expr


class OrExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() or self.right.evaluate()


class AndExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() and self.right.evaluate()


class CompLt(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() < self.right.evaluate()


class CompGt(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() > self.right.evaluate()


class CompLe(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() <= self.right.evaluate()


class CompGe(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() >= self.right.evaluate()


class CompEq(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() == self.right.evaluate()


class CompNeq(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() != self.right.evaluate()


class BwOrExpr(Expr):
    pass


class BwXorExpr(Expr):
    pass


class BwAndExpr(Expr):
    pass


class LshExpr(Expr):
    pass


class RshExpr(Expr):
    pass


class AddExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() + self.right.evaluate()


class SubExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() - self.right.evaluate()


class MulExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() * self.right.evaluate()


class DivExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() / self.right.evaluate()


class FdivExpr(Expr, BinaryOp):
    def evaluate(self):
        return math.floor(self.left.evaluate() / self.right.evaluate())


class ModExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() % self.right.evaluate()


@dataclass
class UnaryOp:
    operand: Expr


class UnaryMinus(Expr, UnaryOp):
    def evaluate(self):
        return -self.operand.evaluate()


class UnaryNot(Expr, UnaryOp):
    def evaluate(self):
        return not self.operand.evaluate()


class UnaryLength(Expr, UnaryOp):
    def evaluate(self):
        raise NotImplementedError


class UnaryBwNot(Expr, UnaryOp):
    def evaluate(self):
        return ~self.operand.evaluate()


class ExpExpr(Expr, BinaryOp):
    def evaluate(self):
        return self.left.evaluate() ** self.right.evaluate()


@dataclass
class ExprList(_Ast, ast_utils.AsList):
    exprs: List[Expr]

    def evaluate(self):
        result = []
        for e in self.exprs:
            if isinstance(e, Expr):
                result.append(e.evaluate())
            else:
                result.append(e)
        return result


class EmptyStmt(Statement):
    pass


@dataclass
class AssignStmt(Statement):
    var_list: List[str]
    expr_list: ExprList

    def evaluate(self):
        values = self.expr_list.evaluate()
        for n, v in zip(self.var_list, values):
            environment[n] = v


class LocalStmt(Statement):
    pass


class FuncDefStmt(Statement):
    pass


@dataclass
class FuncCall(_Ast):
    primary: Expr
    params: ExprList | TableConstructor | str

    def evaluate(self):
        if isinstance(self.primary, Var) and self.primary.name == "print":
            if isinstance(self.params, ExprList):
                values = self.params.evaluate()
                for i in range(len(values)):
                    if values[i] is None:
                        values[i] = 'nil'
                print(*values)


class WhileStmt(Statement):
    pass


class RepeatStmt(Statement):
    pass


class BreakStmt(Statement):
    pass


class ForLoopNum(Statement):
    pass


class ForLoopGen(Statement):
    pass


class Label(Statement):
    pass


class GotoStmt(Statement):
    pass


class ReturnStmt(Statement):
    pass


@dataclass
class Chunk(_Ast, ast_utils.AsList):
    statements: List[Statement | ReturnStmt]

    def evaluate(self):
        for stmt in self.statements:
            stmt.evaluate()


@dataclass
class Elseif(_Ast):
    expr: Expr
    body: Chunk


class IfStmt(Statement, ast_utils.AsList):
    def __init__(self, children):
        self.expr = children[0]
        self.body = children[1]
        self.elseifs = []
        self.else_body = None
        for c in children[2:]:
            if isinstance(c, Elseif):
                self.elseifs.append(c)
            elif isinstance(c, Chunk):
                if self.else_body:
                    raise RuntimeError
                self.else_body = c

    def evaluate(self):
        value = self.expr.evaluate()
        if value:
            self.body.evaluate()
        else:
            if self.elseifs:
                for e in self.elseifs:
                    value = e.expr.evaluate()
                    if value:
                        e.body.evaluate()
                        return

            if self.else_body:
                self.else_body.evaluate()


class Attribute(_Ast):
    pass


class AttrNameList(Statement):
    pass


class FuncDef(Expr):
    pass


class FuncBody(_Ast):
    pass


class ParamList(_Ast):
    pass


class FuncName(_Ast):
    pass


class ToAst(Transformer):
    def var_list(self, c):
        return [c.name for c in c]

    def true(self, _):
        return True

    def false(self, _):
        return False

    def Nil(self, _):
        return None

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
