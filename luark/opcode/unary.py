from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException, UnsupportedOperation
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import AnyType, Boolean, Float, Integer, String, Table


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
                if not isinstance(value, Integer | Float):
                    raise TypeException(prototype_runner)
                result = self._negate(value)
            case 1:  # not
                if not isinstance(value, Boolean):
                    raise TypeException(prototype_runner)
                result = self._not(value)
            case 2:  # length
                if not isinstance(value, String | Table):
                    raise TypeException(prototype_runner)
                result = self._length(value)
            case 3:  # bwnot
                if not isinstance(value, Integer):
                    raise TypeException(prototype_runner)
                result = self._bitwise_not(value)
            case _:
                raise UnsupportedOperation(prototype_runner)
        program_runner.value_stack.append(result)
        prototype_runner.step()

    @staticmethod
    def _negate(value: Integer | Float):
        if isinstance(value, Integer):
            return Integer(-value.value)
        if isinstance(value, Float):
            return Float(-value.value)

    @staticmethod
    def _not(value: Boolean):
        return Boolean(not value.value)

    @staticmethod
    def _length(value: String | Table):
        return Integer(value.length)

    @staticmethod
    def _bitwise_not(value: Integer):
        return Integer(~ value.value)


UnaryOperation.NEGATE = UnaryOperation(0, "negate")
UnaryOperation.NOT = UnaryOperation(1, "not")
UnaryOperation.LENGTH = UnaryOperation(2, "length")
UnaryOperation.BITWISE_NOT = UnaryOperation(3, "bwnot")

UnaryOperation._frozen = True
