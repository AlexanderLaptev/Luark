from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner


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
        if self.count == 0:
            program_runner.value_stack.extend(prototype_runner.varargs)
        else:
            program_runner.value_stack.extend(prototype_runner.varargs[:self.count:-1])
        prototype_runner.step()


class BeginArgs(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert BeginArgs.INSTANCE is None
        super().__init__("begin_args")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.push_mark()
        prototype_runner.step()


class PrepareVarargs(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert PrepareVarargs.INSTANCE is None
        super().__init__("prep_varargs")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        prototype_runner.step()
        if not program_runner.marks:
            return

        mark = program_runner.pop_mark()
        expected = prototype_runner.prototype.fixed_param_count - prototype_runner.prototype.fixed_param_count
        actual = len(program_runner.value_stack) - mark + 1
        extra = max(0, expected - actual)

        if prototype_runner.prototype.is_variadic:
            prototype_runner.varargs = program_runner.value_stack[-extra:]
            del program_runner.value_stack[-extra:]
        else:
            for _ in range(extra):
                program_runner.value_stack.pop()


BeginArgs.INSTANCE = BeginArgs()
PrepareVarargs.INSTANCE = PrepareVarargs()
