from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype


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

    def __init__(self, operation: int, operation_name: str):
        assert not BinaryOperation._frozen
        super().__init__("binop")
        self.operation: int = operation
        self.operation_name = operation_name

    @property
    def arg_str(self) -> str:
        return f"{self.operation}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        return self.operation_name


BinaryOperation.CONCATENATE = BinaryOperation(0, "concat")

BinaryOperation.OR = BinaryOperation(1, "or")
BinaryOperation.AND = BinaryOperation(2, "and")
BinaryOperation.LESS_THAN = BinaryOperation(3, "lt")
BinaryOperation.GREATER_THAN = BinaryOperation(4, "gt")
BinaryOperation.LESS_OR_EQUAL = BinaryOperation(5, "le")
BinaryOperation.GREATER_OR_EQUAL = BinaryOperation(6, "ge")
BinaryOperation.EQUAL = BinaryOperation(7, "eq")
BinaryOperation.NOT_EQUAL = BinaryOperation(8, "neq")

BinaryOperation.ADD = BinaryOperation(9, "add")
BinaryOperation.SUBTRACT = BinaryOperation(10, "sub")
BinaryOperation.MULTIPLY = BinaryOperation(11, "mul")
BinaryOperation.DIVIDE = BinaryOperation(12, "div")
BinaryOperation.FLOOR_DIVIDE = BinaryOperation(13, "fdiv")
BinaryOperation.MODULO_DIVIDE = BinaryOperation(14, "mod")
BinaryOperation.EXPONENTIATE = BinaryOperation(15, "exp")

BinaryOperation.BITWISE_OR = BinaryOperation(16, "bor")
BinaryOperation.BITWISE_XOR = BinaryOperation(17, "bxor")
BinaryOperation.BITWISE_AND = BinaryOperation(18, "band")
BinaryOperation.BITWISE_LEFT_SHIFT = BinaryOperation(19, "lsh")
BinaryOperation.BITWISE_RIGHT_SHIFT = BinaryOperation(20, "rsh")

BinaryOperation._frozen = True
