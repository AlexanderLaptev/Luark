from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException, UnsupportedOperation
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Integer, Float, Boolean, String, Table, AnyType


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

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        result: AnyType
        value = program_runner.value_stack.pop()
        match self.operation:
            case 0:  # negate
                assert isinstance(value, Integer | Float)
                result = self._negate(value)
            case 1:  # not
                assert isinstance(value, Boolean)
                result = self._not(value)
            case 2:  # length
                assert isinstance(value, String | Table)
                result = self._length(value)
            case 3:  # bwnot
                assert isinstance(value, Integer)
                result = self._bitwise_not(value)
            case _:
                raise UnsupportedOperation()
        program_runner.value_stack.append(result)
        prototype_runner.step()


    @staticmethod
    def _negate(value: Integer | Float):
        value.value = -value.value
        return value

    @staticmethod
    def _not(value: Boolean):
        value.value = not value.value
        return value

    @staticmethod
    def _length(value: String | Table):
        return Integer(value.length)

    @staticmethod
    def _bitwise_not(value: Integer):
        value.value = ~value.value
        return value


UnaryOperation.NEGATE = UnaryOperation(0, "negate")
UnaryOperation.NOT = UnaryOperation(1, "not")
UnaryOperation.LENGTH = UnaryOperation(2, "length")
UnaryOperation.BITWISE_NOT = UnaryOperation(3, "bwnot")

UnaryOperation._frozen = True
