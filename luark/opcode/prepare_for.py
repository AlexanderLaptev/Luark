from luark.opcode import Opcode
from luark.vm.exception import TypeException
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Integer, Float


class PrepareForNumeric(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("prepare_for_num")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        interval = program_runner.value_stack.pop()
        end = program_runner.value_stack.pop()
        start = program_runner.value_stack.pop()

        if (not isinstance(interval, Integer) and not isinstance(interval, Float)
            or not isinstance(end, Integer) and not isinstance(end, Float)
            or not isinstance(start, Integer) and not isinstance(start, Float)):
            raise TypeException(prototype_runner)

        prototype_runner.local_variables[self.control_index] = start
        prototype_runner.local_variables[self.control_index + 1] = end
        prototype_runner.local_variables[self.control_index + 2] = interval

        prototype_runner.step(3)



class PrepareForGeneric(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("prepare_for_gen")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)
