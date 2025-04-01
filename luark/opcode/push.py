from dataclasses import dataclass

from luark.compiler.compiler_state import CompilerState
from luark.opcode import Opcode


@dataclass
class PushConst(Opcode):
    index: int

    def __str__(self):
        return f"push_const {self.index}"

    def get_comment(self, state: CompilerState) -> str:
        value = state.get_const(self.index)
        return str(value)

    def __bytes__(self) -> bytes:
        raise NotImplementedError
