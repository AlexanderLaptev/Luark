from abc import ABC, abstractmethod
from typing import Callable, Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import AnyType, Boolean, Float, Integer, String


class BinaryOperation(ABC, Opcode):
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

    def run(self, pr: ProgramRunner, pt: PrototypeRunner):
        result: AnyType
        second: AnyType = pr.value_stack.pop()
        first: AnyType = pr.value_stack.pop()
        self._run(pr, pt, first, second)
        pt.step()

    @abstractmethod
    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        pass


class ConcatenateOperation(BinaryOperation):
    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        pr.value_stack.append(String((str(first) + str(second)).encode("utf-8")))


class OrOperation(BinaryOperation):
    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        pr.value_stack.append(Boolean(bool(first) or bool(second)))


class AndOperation(BinaryOperation):
    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        pr.value_stack.append(Boolean(bool(first) and bool(second)))


class ComparisonOperation(BinaryOperation):
    def __init__(self, operation: int, name: str, comparator: Callable):
        super().__init__(operation, name)
        self.comparator = comparator

    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        if isinstance(first, Integer | Float) and isinstance(second, Integer | Float):
            pr.value_stack.append(Boolean(self.comparator(float(first.value), float(second.value))))
        elif isinstance(first, String) and isinstance(second, String):
            pr.value_stack.append(Boolean(self.comparator(str(first), str(second))))
        else:
            raise TypeError


class EqualityOperation(BinaryOperation):
    def __init__(self, operation: int, name: str, comparator: Callable):
        super().__init__(operation, name)
        self.comparator = comparator

    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        if type(first) != type(second):
            pr.value_stack.append(Boolean(False))
        else:
            pr.value_stack.append(Boolean(self.comparator(first.value, second.value)))


class ArithmeticOperation(BinaryOperation):
    def __init__(self, operation: int, name: str, calculator: Callable):
        super().__init__(operation, name)
        self.calculator = calculator

    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        if isinstance(first, Integer) and isinstance(second, Integer):
            pr.value_stack.append(Integer(self.calculator(first.value, second.value)))
        elif isinstance(first, Float) or isinstance(second, Float):
            pr.value_stack.append(Float(self.calculator(float(first.value), float(second.value))))
        else:
            raise TypeError


class BitwiseOperation(BinaryOperation):
    def __init__(self, operation: int, name: str, calculator: Callable):
        super().__init__(operation, name)
        self.calculator = calculator

    def _run(self, pr: ProgramRunner, pt: PrototypeRunner, first: AnyType, second: AnyType) -> None:
        if isinstance(first, Integer) and isinstance(second, Integer):
            pr.value_stack.append(Integer(self.calculator(first.value, second.value)))
        else:
            raise TypeError


BinaryOperation.CONCATENATE = ConcatenateOperation(0, "concat")

BinaryOperation.OR = OrOperation(1, "or")
BinaryOperation.AND = AndOperation(2, "and")
BinaryOperation.LESS_THAN = ComparisonOperation(3, "lt", lambda x, y: x < y)
BinaryOperation.GREATER_THAN = ComparisonOperation(4, "gt", lambda x, y: x > y)
BinaryOperation.LESS_OR_EQUAL = ComparisonOperation(5, "le", lambda x, y: x <= y)
BinaryOperation.GREATER_OR_EQUAL = ComparisonOperation(6, "ge", lambda x, y: x >= y)
BinaryOperation.EQUAL = EqualityOperation(7, "eq", lambda x, y: x == y)
BinaryOperation.NOT_EQUAL = EqualityOperation(8, "neq", lambda x, y: x != y)

BinaryOperation.ADD = ArithmeticOperation(9, "add", lambda x, y: x + y)
BinaryOperation.SUBTRACT = ArithmeticOperation(10, "sub", lambda x, y: x - y)
BinaryOperation.MULTIPLY = ArithmeticOperation(11, "mul", lambda x, y: x * y)
BinaryOperation.DIVIDE = ArithmeticOperation(12, "div", lambda x, y: x / y)
BinaryOperation.FLOOR_DIVIDE = ArithmeticOperation(13, "fdiv", lambda x, y: x // y)
BinaryOperation.MODULO_DIVIDE = ArithmeticOperation(14, "mod", lambda x, y: x % y)
BinaryOperation.EXPONENTIATE = ArithmeticOperation(15, "exp", lambda x, y: x ** y)

BinaryOperation.BITWISE_OR = ArithmeticOperation(16, "bor", lambda x, y: x | y)
BinaryOperation.BITWISE_XOR = ArithmeticOperation(17, "bxor", lambda x, y: x ^ y)
BinaryOperation.BITWISE_AND = ArithmeticOperation(18, "band", lambda x, y: x & y)
BinaryOperation.BITWISE_LEFT_SHIFT = ArithmeticOperation(19, "lsh", lambda x, y: x << y)
BinaryOperation.BITWISE_RIGHT_SHIFT = ArithmeticOperation(20, "rsh", lambda x, y: x >> y)

BinaryOperation._frozen = True
