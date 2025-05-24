from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype


class PushConst(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("push_const")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype, pc) -> str:
        value = proto.constant_pool[self.index]
        if isinstance(value, bytes):
            value = str(value)[1:]
        return str(value)


class PushInt(Opcode):
    value: int

    def __init__(self, value: int):
        super().__init__("push_int")
        self.value = value

    @property
    def arg_str(self) -> str:
        return str(self.value)


class PushFloat(Opcode):
    value: int

    def __init__(self, value: int | float):
        super().__init__("push_float")
        if isinstance(value, float):
            frac = value - int(value)
            assert frac == 0, "attempted to push a non-integer value as a float"
        self.value = value

    @property
    def arg_str(self) -> str:
        return str(int(self.value))


class PushTrue(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PushTrue.INSTANCE is None
        super().__init__("push_true")


PushTrue.INSTANCE = PushTrue()


class PushFalse(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PushFalse.INSTANCE is None
        super().__init__("push_false")


PushFalse.INSTANCE = PushFalse()


class PushNil(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PushNil.INSTANCE is None
        super().__init__("push_nil")


PushNil.INSTANCE = PushNil()
