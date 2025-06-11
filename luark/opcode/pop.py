from typing import Self

from luark.opcode import Opcode
from luark.vm.luavm import ProgramRunner, PrototypeRunner


class Pop(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert Pop.INSTANCE is None
        super().__init__("pop")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.pop()
        prototype_runner.step()


Pop.INSTANCE = Pop()
