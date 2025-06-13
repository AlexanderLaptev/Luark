from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from luark.program import Program, Prototype
    from luark.vm.luavm import ProgramRunner, PrototypeRunner


class Opcode:
    name: str

    def __init__(self, name: str):
        self.name = name

    @property
    def arg_str(self) -> str:
        return ""

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        return ""

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        from luark.vm.exception import UnsupportedOperation
        raise UnsupportedOperation(prototype_runner)
