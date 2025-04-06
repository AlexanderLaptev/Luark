from luark.compiler.ast.expressions import MultiresExpression
from luark.compiler.compiler_state import CompilerState
from luark.opcode.varargs import Varargs as VarargsOpcode


class Varargs(MultiresExpression):
    def evaluate(
            self,
            state: CompilerState,
            return_count: int = 1
    ) -> None:
        state.add_opcode(VarargsOpcode(return_count))
