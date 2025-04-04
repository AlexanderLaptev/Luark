from dataclasses import dataclass

from luark.compiler.ast.expressions import ExpressionList, MultiresExpression
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

        expressions = self.expression_list.expressions
        for expr in expressions[:-1]:
            expr.evaluate(state)

        last = expressions[-1]
        return_count: int
        if isinstance(last, MultiresExpression):
            last.evaluate(state, 0)
            return_count = 0  # unknown count
        else:
            last.evaluate(state)
            return_count = 1 + len(expressions)

        state.add_opcode(Return(return_count))
