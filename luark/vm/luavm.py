from dataclasses import dataclass

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.types import AnyType


@dataclass
class PrototypeRunner:
    prototype: Prototype
    program_counter: int


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
                program_counter=0
            )
        )


class LuaVM:
    def __init__(self):
        self.call_stack = []
        self.env = {}
