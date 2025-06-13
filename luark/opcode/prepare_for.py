from luark.opcode import Opcode
from luark.vm.exception import BaseRuntimeException, TypeException
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Float, Integer


class PrepareForNumeric(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("prepare_for_num")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        step = program_runner.value_stack.pop()
        end = program_runner.value_stack.pop()
        control = program_runner.value_stack.pop()

        if (not isinstance(step, Integer) and not isinstance(step, Float)
                or not isinstance(end, Integer) and not isinstance(end, Float)
                or not isinstance(control, Integer) and not isinstance(control, Float)):
            raise TypeException(prototype_runner)

        if step.value == 0:
            raise BaseRuntimeException("zero step in numeric for loop")

        prototype_runner.local_variables[self.control_index] = control
        prototype_runner.local_variables[self.control_index + 1] = end
        prototype_runner.local_variables[self.control_index + 2] = step

        prototype_runner.step()


class PrepareForGeneric(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("prepare_for_gen")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)
