from dataclasses import dataclass

from luark.opcode import Opcode


@dataclass
class LoadUpvalue(Opcode):
    index: int


@dataclass
class StoreUpvalue(Opcode):
    index: int
