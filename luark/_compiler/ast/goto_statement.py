from dataclasses import dataclass

from lark.ast_utils import Ast

from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.ast.statement import Statement


@dataclass
class Label(Ast, Statement):
    name: str

    def emit(self, state: _ProgramState):
        state.proto.add_label(self.name)


@dataclass
class GotoStmt(Ast, Statement):
    label: str

    def emit(self, state: _ProgramState):
        state.proto.add_goto(self.label)
