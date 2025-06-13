from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner


class Jump(Opcode):
    offset: int

    def __init__(self, offset: int):
        super().__init__("jump")
        self.offset = offset

    @property
    def arg_str(self) -> str:
        return str(self.offset)

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        return f"to {pc + self.offset}"

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        prototype_runner.step(self.offset)