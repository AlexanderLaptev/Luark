from abc import abstractmethod
from dataclasses import dataclass

from lark.tree import Meta

from luark.compiler.compiler_state import CompilerState


@dataclass
class Statement:
    meta: Meta

    @abstractmethod
    def compile(self, state: CompilerState) -> None:
        pass
