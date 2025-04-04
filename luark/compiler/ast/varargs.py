from typing import Literal

from luark.compiler.ast.expressions import MultiresExpression
from luark.compiler.compiler_state import CompilerState


class Varargs(MultiresExpression):
    def evaluate(
            self,
            state: CompilerState,
            return_count: int | Literal["all"] = 1
    ) -> None:
        raise NotImplementedError
