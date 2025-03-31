from dataclasses import dataclass
from typing import TypeAlias

from lark.ast_utils import Ast

from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.expr_list_utils import evaluate_single
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.errors import CompilationError


@dataclass
class Var(Ast, Expression):
    name: str

    def __init__(self, name: str):
        match name:
            case "nil" | "true" | "false":
                raise CompilationError(f"Syntax error near '{name}'.")
        self.name = name

    def evaluate(self, state: _ProgramState):
        state.read(state, self.name)


@dataclass
class DotAccess(Ast, Expression):
    expression: Expression
    name: str

    def evaluate(self, state: _ProgramState):
        proto = state.proto
        evaluate_single(state, self.expression)
        index = proto.get_const_index(self.name)
        proto.add_opcode(f"push_const {index}")
        proto.add_opcode("get_table")


@dataclass
class TableAccess(Ast, Expression):
    table: Expression
    key: Expression

    def evaluate(self, state: _ProgramState):
        proto = state.proto
        evaluate_single(state, self.table)
        evaluate_single(state, self.key)
        proto.add_opcode("get_table")


VarType: TypeAlias = Var | DotAccess | TableAccess
