from abc import ABC, abstractmethod

from luark.compiler.ast.program_state import _ProgramState


class Statement(ABC):
    @abstractmethod
    def emit(self, state: _ProgramState):
        pass
