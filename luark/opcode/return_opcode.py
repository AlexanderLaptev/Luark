from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner


class Return(Opcode):
    def __init__(self, return_count: int):
        super().__init__("return")
        self.return_count = return_count

    @property
    def arg_str(self) -> str:
        return str(self.return_count)

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        returns = "*" if (self.return_count == 0) else self.return_count - 1
        return f"r:{returns}"

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        # todo: also some magic with arguments adjustment
        program_runner.pop_prototype()
