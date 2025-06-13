import typing
from dataclasses import dataclass

from typing_extensions import TypeVar

from luark.program import Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner

if typing.TYPE_CHECKING:
    from luark.vm.exception import NilPointerException

T = TypeVar('T')


@dataclass
class AnyType:
    pass


@dataclass
class Float(AnyType):
    value: float


@dataclass
class Integer(AnyType):
    value: int


@dataclass
class String(AnyType):
    value: bytes

    @property
    def length(self) -> int:
        return len(self.value)


@dataclass
class Boolean(AnyType):
    value: bool


@dataclass
class Nil(AnyType):
    pass


class Table(AnyType):
    table: dict[AnyType, AnyType]  # todo: maybe change to something better

    def __init__(self):
        self.table = {}

    @property
    def length(self) -> int:
        return len(self.table)

    def get(self, key: AnyType) -> AnyType:
        assert_not_nil(key)
        return self.table[key]

    def set(self, key: AnyType, value: AnyType):
        assert_not_nil(key)
        self.table[key] = value
        return


class Callable(AnyType):
    def call(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        pass


@dataclass
class Function(Callable):
    prototype: Prototype

    def call(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.push_prototype(self.prototype)


@dataclass
class NativeFunction(Callable):
    function: typing.Callable[[ProgramRunner, PrototypeRunner], None]

    def call(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        self.function(program_runner, prototype_runner)
        prototype_runner.step()


def assert_not_nil(value: AnyType):
    if value is Nil:
        raise NilPointerException()
