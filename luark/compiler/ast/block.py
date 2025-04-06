from lark.ast_utils import AsList
from lark.tree import Meta

from luark.compiler.ast.goto_statement import Label
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


class Block(Statement, AsList):
    """
    A block is a collection of statements. The last statement may be a return statement.
    """

    def __init__(self, meta: Meta, statements: list[Statement]):
        super().__init__(meta)
        self.statements = statements

        end_label_count = 0
        for stmt in reversed(self.statements):
            if isinstance(stmt, Label):
                end_label_count += 1
            else:
                break

        label: Label
        for label in self.statements[-end_label_count:]:
            label.is_trailing = True

    def compile(self, state: CompilerState) -> None:
        state.begin_block()
        for stmt in self.statements:
            stmt.compile(state)
        state.end_block()
