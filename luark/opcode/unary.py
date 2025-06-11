from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Integer, Float, Boolean, String, Table


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
        value = program_runner.value_stack.pop()
        match self.operation:
            case 0:  # negate
                if not (value is Integer or value is Float):
                    raise TypeException()
                assert isinstance(value, Integer | Float)
                self._negate(value, program_runner, prototype_runner)
            case 1:  # not
                if not (value is Boolean):
                    raise TypeException()
                assert isinstance(value, Boolean)
                self._not(value, program_runner, prototype_runner)
            case 2:  # length
                if not (value is String or value is Table):
                    raise TypeException()
                assert isinstance(value, String | Table)
                self._length(value, program_runner, prototype_runner)
            case 3:  # bwnot
                if not (value is Integer):
                    raise TypeException()
                assert isinstance(value, Integer)
                self._bitwise_not(value, program_runner, prototype_runner)

    @staticmethod
    def _negate(value: Integer | Float, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value.value = -value.value
        program_runner.value_stack.append(value)
        prototype_runner.step()

    @staticmethod
    def _not(value: Boolean, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value.value = not value.value
        program_runner.value_stack.append(value)
        prototype_runner.step()

    @staticmethod
    def _length(value: String | Table, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.value_stack.append(Integer(value.length))
        prototype_runner.step()

    @staticmethod
    def _bitwise_not(value: Integer, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value.value = ~value.value
        program_runner.value_stack.append(value)
        prototype_runner.step()

UnaryOperation.NEGATE = UnaryOperation(0, "negate")
UnaryOperation.NOT = UnaryOperation(1, "not")
UnaryOperation.LENGTH = UnaryOperation(2, "length")
UnaryOperation.BITWISE_NOT = UnaryOperation(3, "bwnot")

UnaryOperation._frozen = True
