from typing import Self

from luark.opcode import Opcode


class Test(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert Test.INSTANCE is None
        super().__init__("test")


Test.INSTANCE = Test()


class TestNil(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert TestNil.INSTANCE is None
        super().__init__("test_nil")


TestNil.INSTANCE = TestNil()


class TestNumericFor(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("test_for")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)
