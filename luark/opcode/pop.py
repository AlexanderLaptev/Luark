from typing import Self

from luark.opcode import Opcode


class Pop(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert Pop.INSTANCE is None
        super().__init__("pop")


Pop.INSTANCE = Pop()
