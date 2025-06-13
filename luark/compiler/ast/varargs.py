from luark.compiler.ast.expressions import MultiresExpression
from luark.compiler.compiler_state import CompilerState
from luark.opcode.varargs import Varargs as VarargsOpcode


class Varargs(MultiresExpression):
    def evaluate(self, state: CompilerState, return_count: int = 2) -> None:
        assert return_count != 1, "varargs not returning a value"
        if return_count >= 2:
            return_count -= 1
        state.add_opcode(VarargsOpcode(return_count))
