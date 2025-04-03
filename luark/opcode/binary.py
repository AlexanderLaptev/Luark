from typing import Self

from luark.opcode import Opcode


class BinaryOperation(Opcode):
    CONCATENATE: Self

    OR: Self
    AND: Self
    LESS_THAN: Self
    GREATER_THAN: Self
    LESS_OR_EQUAL: Self
    GREATER_OR_EQUAL: Self
    EQUAL: Self
    NOT_EQUAL: Self

    ADD: Self
    SUBTRACT: Self
    MULTIPLY: Self
    DIVIDE: Self
    FLOOR_DIVIDE: Self
    MODULO_DIVIDE: Self
    EXPONENTIATE: Self

    BITWISE_OR: Self
    BITWISE_XOR: Self
    BITWISE_AND: Self
    BITWISE_LEFT_SHIFT: Self
    BITWISE_RIGHT_SHIFT: Self

    _frozen: bool = False

    def __init__(self, operation: int):
        assert not BinaryOperation._frozen
        super().__init__("binop")
        self.operation: int = operation

    @property
    def arg_str(self) -> str:
        return f"{self.operation}"


BinaryOperation.CONCATENATE = BinaryOperation(0)

BinaryOperation.OR = BinaryOperation(1)
BinaryOperation.AND = BinaryOperation(2)
BinaryOperation.LESS_THAN = BinaryOperation(3)
BinaryOperation.GREATER_THAN = BinaryOperation(4)
BinaryOperation.LESS_OR_EQUAL = BinaryOperation(5)
BinaryOperation.GREATER_OR_EQUAL = BinaryOperation(6)
BinaryOperation.EQUAL = BinaryOperation(7)
BinaryOperation.NOT_EQUAL = BinaryOperation(8)

BinaryOperation.ADD = BinaryOperation(9)
BinaryOperation.SUBTRACT = BinaryOperation(10)
BinaryOperation.MULTIPLY = BinaryOperation(11)
BinaryOperation.DIVIDE = BinaryOperation(12)
BinaryOperation.FLOOR_DIVIDE = BinaryOperation(13)
BinaryOperation.MODULO_DIVIDE = BinaryOperation(14)
BinaryOperation.EXPONENTIATE = BinaryOperation(15)

BinaryOperation.BITWISE_OR = BinaryOperation(16)
BinaryOperation.BITWISE_XOR = BinaryOperation(17)
BinaryOperation.BITWISE_AND = BinaryOperation(18)
BinaryOperation.BITWISE_LEFT_SHIFT = BinaryOperation(19)
BinaryOperation.BITWISE_RIGHT_SHIFT = BinaryOperation(20)

BinaryOperation._frozen = True
