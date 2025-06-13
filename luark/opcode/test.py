from typing import Self

from luark.opcode import Opcode
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Boolean, Nil, Integer, Float


class Test(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert Test.INSTANCE is None
        super().__init__("test")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value = program_runner.value_stack.pop()

        if isinstance(value, Nil):
            prototype_runner.step(1)
            return

        if isinstance(value, Boolean):
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
        if isinstance(value, Nil):
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

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        iterator = prototype_runner.local_variables[self.control_index]
        end = prototype_runner.local_variables[self.control_index + 1]
        interval = prototype_runner.local_variables[self.control_index + 2]

        assert isinstance(iterator, Float | Integer)
        assert isinstance(interval, Float | Integer)
        assert isinstance(end, Float | Integer)

        next_iterator_value = iterator.value + interval.value

        if interval.value > 0 and next_iterator_value >= end.value:  # stop
            prototype_runner.step(1)
            return
        if interval.value < 0 and next_iterator_value <= end.value:  # stop
            prototype_runner.step(1)
            return

        # continue
        # if isinstance(next_iterator_value, int):
        #     prototype_runner.local_variables[self.control_index] = Integer(next_iterator_value)
        # else:
        #     prototype_runner.local_variables[self.control_index] = Float(next_iterator_value)
        prototype_runner.step(2)
