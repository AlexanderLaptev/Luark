from dataclasses import dataclass

from lark.ast_utils import Ast, AsList

from luark.compiler.ast.function_calls import FuncCall
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.ast.statement import Statement


@dataclass
class Block(Ast, AsList, Statement):
    statements: list[Statement]

    def emit(self, state: _ProgramState):
        for statement in self.statements:
            if isinstance(statement, Block):
                state.push_block()
                statement.emit(state)
                state.pop_block()
            elif isinstance(statement, FuncCall):
                statement.evaluate(state, 1)
            else:
                statement.emit(state)
