from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException, UnsupportedOperation
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import AnyType, Boolean, Float, Integer, String


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

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        result: AnyType
        second: AnyType = program_runner.value_stack.pop()
        first: AnyType = program_runner.value_stack.pop()
        match self.operation:
            case 0:
                result = self._concat(first, second, prototype_runner)
            case 1:
                result = self._or(first, second, prototype_runner)
            case 2:
                result = self._and(first, second, prototype_runner)
            case 3:
                result = self._less_than(first, second, prototype_runner)
            case 4:
                result = self._greater_than(first, second, prototype_runner)
            case 5:
                result = self._less_or_equal_than(first, second, prototype_runner)
            case 6:
                result = self._greater_or_equal_than(first, second, prototype_runner)
            case 7:
                result = self._equal(first, second, prototype_runner)
            case 8:
                result = self._not_equal(first, second, prototype_runner)
            case 9:
                result = self._add(first, second, prototype_runner)
            case 10:
                result = self._subtract(first, second, prototype_runner)
            case 11:
                result = self._multiply(first, second, prototype_runner)
            case 12:
                result = self._divide(first, second, prototype_runner)
            case 13:
                result = self._floor_divide(first, second, prototype_runner)
            case 14:
                result = self._modulo_divide(first, second, prototype_runner)
            case 15:
                result = self._exponentiate(first, second, prototype_runner)
            case 16:
                result = self._bitwise_or(first, second, prototype_runner)
            case 17:
                result = self._bitwise_xor(first, second, prototype_runner)
            case 18:
                result = self._bitwise_and(first, second, prototype_runner)
            case 19:
                result = self._bitwise_left_shift(first, second, prototype_runner)
            case 20:
                result = self._bitwise_right_shift(first, second, prototype_runner)
            case _:
                raise UnsupportedOperation(prototype_runner)

        program_runner.value_stack.append(result)
        prototype_runner.step()
        pass

    @staticmethod
    def _concat(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        return String(str(first).encode() + str(second).encode())

    @staticmethod
    def _or(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if not isinstance(first, Boolean) or not isinstance(second, Boolean):
            raise TypeException(prototype_runner)
        return Boolean(first.value or second.value)

    @staticmethod
    def _and(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if not isinstance(first, Boolean) or not isinstance(second, Boolean):
            raise TypeException(prototype_runner)
        return Boolean(first.value and second.value)

    # todo: I dont convert Int to Float (or back) yet.
    @staticmethod
    def _less_than(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Boolean(first.value < second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Boolean(first.value < second.value)
        if isinstance(first, String) and isinstance(second, String):
            return Boolean(first.value < second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _greater_than(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Boolean(first.value > second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Boolean(first.value > second.value)
        if isinstance(first, String) and isinstance(second, String):
            return Boolean(first.value > second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _less_or_equal_than(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Boolean(first.value <= second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Boolean(first.value <= second.value)
        if isinstance(first, String) and isinstance(second, String):
            return Boolean(first.value <= second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _greater_or_equal_than(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Boolean(first.value >= second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Boolean(first.value >= second.value)
        if isinstance(first, String) and isinstance(second, String):
            return Boolean(first.value >= second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _equal(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Boolean(first.value == second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Boolean(first.value == second.value)
        if isinstance(first, String) and isinstance(second, String):
            return Boolean(first.value == second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _not_equal(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Boolean(first.value != second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Boolean(first.value != second.value)
        if isinstance(first, String) and isinstance(second, String):
            return Boolean(first.value != second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _add(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Float(first.value + second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value + second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _subtract(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Float(first.value - second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value - second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _multiply(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Float(first.value * second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value * second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _divide(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Float(first.value / second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Float(first.value / second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _floor_divide(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Float):
            return Float(first.value // second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value // second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _modulo_divide(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value % second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _exponentiate(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Float) and isinstance(second, Integer):
            return Float(first.value ** second.value)
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value ** second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _bitwise_or(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value | second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _bitwise_xor(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value ^ second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _bitwise_and(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value & second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _bitwise_left_shift(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value << second.value)
        raise TypeException(prototype_runner)

    @staticmethod
    def _bitwise_right_shift(first: AnyType, second: AnyType, prototype_runner: PrototypeRunner):
        if isinstance(first, Integer) and isinstance(second, Integer):
            return Integer(first.value >> second.value)
        raise TypeException(prototype_runner)


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
