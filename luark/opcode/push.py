from dataclasses import dataclass

from luark.opcode import Opcode


@dataclass
class PushConst(Opcode):
    index: int
