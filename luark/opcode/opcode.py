from abc import ABC, abstractmethod


class Opcode(ABC):
    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass
