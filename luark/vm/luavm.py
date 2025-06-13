from dataclasses import dataclass

from luark.program import Program, Prototype
from luark.vm.types import AnyType


@dataclass
class PrototypeRunner:
    prototype: Prototype
    program_counter: int
    local_variables: list[AnyType]

    def step(self, offest: int = 1):
        self.program_counter += offest


class ProgramRunner:
    def __init__(self, program: Program):
        self.value_stack: list[AnyType] = []
        self.env: dict[int, AnyType]
        self.call_stack: list[PrototypeRunner] = []
        self.program: Program = program
        self.push_prototype(program.prototypes[0])

    def push_prototype(self, prototype: Prototype):
        self.call_stack.append(
            PrototypeRunner(
                prototype=prototype,
                program_counter=0,
                local_variables=[AnyType()] * prototype.num_locals
            )
        )

    def pop_prototype(self):
        self.call_stack.pop()


class LuaVM:
    def __init__(self, program: Program):
        self.runner: ProgramRunner = ProgramRunner(program=program)

    def loop(self):
        while len(self.runner.call_stack) > 0:
            current: PrototypeRunner = self.runner.call_stack[-1]
            opcode = current.prototype.opcodes[current.program_counter]
            opcode.run(program_runner=self.runner, prototype_runner=current)
