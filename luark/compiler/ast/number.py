from dataclasses import dataclass

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.opcode.push import PushConst


@dataclass
class Number(CompileTimeConstant):
    value: int | float

    def evaluate(self, state: CompilerState) -> None:
        const_index = state.get_const_index(self.value)
        state.add_opcode(PushConst(const_index))
