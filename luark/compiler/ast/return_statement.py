from dataclasses import dataclass

from luark.compiler.ast.expressions import ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.opcode.return_opcode import Return


@dataclass
class ReturnStatement(Statement):
    expression_list: ExpressionList | None = None

    def compile(self, state: CompilerState) -> None:
        if self.expression_list is None:
            state.add_opcode(Return(1))
            return

        adjust_to: int | None
        if self.expression_list.is_multires:
            adjust_to = None
        else:
            adjust_to = len(self.expression_list.expressions)

        self.expression_list.evaluate(state, adjust_to=adjust_to)
        if adjust_to is None:
            adjust_to = 0
        else:
            adjust_to += 1
        state.add_opcode(Return(adjust_to))
