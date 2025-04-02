from dataclasses import dataclass

from luark.opcode import Opcode


@dataclass
class LoadLocal(Opcode):
    index: int


@dataclass
class StoreLocal(Opcode):
    index: int


@dataclass
class MarkTBC(Opcode):
    index: int
