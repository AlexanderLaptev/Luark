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

    def comment_str(self, program: Program, proto: Prototype) -> str:
        value = proto.constant_pool[self.index]
        if isinstance(value, bytes):
            value = str(value)[1:]
        return str(value)


class PushTrue(Opcode):
    INSTANCE: Self

    def __init__(self):
        super().__init__("push_true")


PushTrue.INSTANCE = PushTrue()


class PushFalse(Opcode):
    INSTANCE: Self

    def __init__(self):
        super().__init__("push_false")


PushFalse.INSTANCE = PushFalse()


class PushNil(Opcode):
    INSTANCE: Self

    def __init__(self):
        super().__init__("push_nil")


PushNil.INSTANCE = PushNil()
