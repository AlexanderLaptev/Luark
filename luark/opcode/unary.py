from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype


class UnaryOperation(Opcode):
    NEGATE: Self
    NOT: Self
    LENGTH: Self
    BITWISE_NOT: Self

    _frozen: bool = False

    def __init__(self, operation: int, operation_name: str):
        assert not UnaryOperation._frozen
        super().__init__("unop")
        self.operation: int = operation
        self.operation_name = operation_name

    @property
    def arg_str(self) -> str:
        return f"{self.operation}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        return self.operation_name


UnaryOperation.NEGATE = UnaryOperation(0, "negate")
UnaryOperation.NOT = UnaryOperation(1, "not")
UnaryOperation.LENGTH = UnaryOperation(2, "length")
UnaryOperation.BITWISE_NOT = UnaryOperation(3, "bwnot")

UnaryOperation._frozen = True
