import typing
from dataclasses import dataclass

from typing_extensions import TypeVar

from luark.program import Prototype

if typing.TYPE_CHECKING:
    from luark.vm.exception import NilPointerException

T = TypeVar('T')


@dataclass(frozen=True)
class AnyType:
    pass


@dataclass(frozen=True)
class Float(AnyType):
    value: float

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True)
class Integer(AnyType):
    value: int

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True)
class String(AnyType):
    value: bytes

    @property
    def length(self) -> int:
        return len(self.value)

    def __str__(self):
        return self.value.decode('utf-8', errors='replace')


@dataclass(frozen=True)
class Boolean(AnyType):
    value: bool

    def __str__(self):
        return str(self.value)


@dataclass(frozen=True)
class Nil(AnyType):

    def __str__(self):
        return "nil"

@dataclass(frozen=True)
class Table(AnyType):
    table: dict[AnyType, AnyType]  # todo: maybe change to something better

    # def __init__(self):
        # self.table = {}

    def __str__(self):
        return "{}" + ", ".join([f"{str(key)}: {str(value)}" for key, value in self.table.items()]) + "}"

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


@dataclass(frozen=True)
class Function(AnyType):
    prototype: Prototype


@dataclass(frozen=True)
class NativeFunction(AnyType):
    function: typing.Callable[..., None]

    def __str__(self):
        return self.function.__name__


def assert_not_nil(value: AnyType):
    if isinstance(value, Nil):
        raise NilPointerException()
