import typing
from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Boolean, Nil, Integer, Float, String
# if typing.TYPE_CHECKING:
#     pass


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

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value: bytes = prototype_runner.prototype.constant_pool[self.index]
        program_runner.value_stack.append(String(value))
        prototype_runner.step()



class PushInt(Opcode):
    value: int

    def __init__(self, value: int):
        super().__init__("push_int")
        self.value = value

    @property
    def arg_str(self) -> str:
        return str(self.value)

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.append(Integer(self.value))
        prototype_runner.step()


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

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.append(Float(self.value))
        prototype_runner.step()



class PushTrue(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PushTrue.INSTANCE is None
        super().__init__("push_true")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.append(Boolean(True))
        prototype_runner.step()


PushTrue.INSTANCE = PushTrue()


class PushFalse(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PushFalse.INSTANCE is None
        super().__init__("push_false")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.append(Boolean(False))
        prototype_runner.step()


PushFalse.INSTANCE = PushFalse()


class PushNil(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PushNil.INSTANCE is None
        super().__init__("push_nil")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.append(Nil())
        prototype_runner.step()


PushNil.INSTANCE = PushNil()
