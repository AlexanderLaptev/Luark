import typing
from typing import Self

from luark.opcode import Opcode
from luark.vm.luavm import ProgramRunner, PrototypeRunner

if typing.TYPE_CHECKING:
    from luark.vm.types import Boolean, Nil


class Test(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert Test.INSTANCE is None
        super().__init__("test")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value = program_runner.value_stack.pop()

        if value is Nil:
            prototype_runner.step(1)
            return

        if value is Boolean:
            assert isinstance(value, Boolean)
            if not value.value:
                prototype_runner.step(1)
                return

        prototype_runner.step(2)

Test.INSTANCE = Test()


class TestNil(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert TestNil.INSTANCE is None
        super().__init__("test_nil")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value = program_runner.value_stack.pop()
        if value is Nil:
            prototype_runner.step(2)
        else:
            prototype_runner.step(1)



TestNil.INSTANCE = TestNil()


class TestNumericFor(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("test_for")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)
