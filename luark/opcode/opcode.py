from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from luark.program import Program, Prototype


class Opcode:
    name: str

    def __init__(self, name: str):
        self.name = name

    @property
    def arg_str(self) -> str:
        return ""

    def comment_str(self, program: Program, proto: Prototype) -> str:
        return ""
