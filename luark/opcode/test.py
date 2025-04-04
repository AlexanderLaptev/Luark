from typing import Self

from luark.opcode import Opcode


class Test(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert Test.INSTANCE is None
        super().__init__("test")


Test.INSTANCE = Test()
