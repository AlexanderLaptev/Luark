from dataclasses import dataclass

from luark.compiler.ast.expressions import ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.variable import Lvalue
from luark.compiler.compiler_state import CompilerState


@dataclass
class AssignmentStatement(Statement):
    targets: list[Lvalue]
    expression_list: ExpressionList

    def compile(self, state: CompilerState) -> None:
        temporaries: list[int] = []

        # Cache variables used in dot/table accesses to
        # ensure the assignment does not affect them.
        for target in self.targets:
            target.evaluate(state, temporaries)

        self.expression_list.evaluate(state, len(self.targets))
        temporaries = temporaries[::-1]  # ensure they are read in reverse order
        for target in self.targets:
            target.assign(state, temporaries)

        for temp in temporaries:
            state.release_locals(temp)
