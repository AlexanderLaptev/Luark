from dataclasses import dataclass

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import InternalCompilerError
from luark.opcode.push import PushConst, PushFloat, PushInt


@dataclass
class Number(CompileTimeConstant):
    value: int | float

    def evaluate(self, state: CompilerState) -> None:
        if isinstance(self.value, int):
            state.add_opcode(PushInt(self.value))
        elif isinstance(self.value, float):
            frac = self.value - int(self.value)
            # Using an exact comparison here since the int must be representable
            # exactly. If there's *any* difference, we should use `push_const` instead.
            if frac == 0:
                PushFloat(self.value)
            else:
                const_index = state.get_const_index(self.value)
                state.add_opcode(PushConst(const_index))
        else:
            raise InternalCompilerError(f"illegal number type: {type(self.value)}")
