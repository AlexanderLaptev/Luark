from __future__ import annotations

import typing
from abc import ABC, abstractmethod

if typing.TYPE_CHECKING:
    from luark.compiler.compiler_state import CompilerState


class Opcode(ABC):
    @abstractmethod
    def __str__(self):
        pass

    def get_comment(self, state: CompilerState) -> str:
        return ""

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass
