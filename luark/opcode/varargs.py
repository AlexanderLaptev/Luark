from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import PrototypeRunner, ProgramRunner


class Varargs(Opcode):
    count: int

    def __init__(self, count: int):
        super().__init__("varargs")
        self.count = count

    @property
    def arg_str(self) -> str:
        return str(self.count)

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        return "all" if (self.count == 0) else f"{self.count} values"

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        prototype_runner.step()


class MarkStack(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert MarkStack.INSTANCE is None
        super().__init__("mark_stack")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        prototype_runner.step()


MarkStack.INSTANCE = MarkStack()
