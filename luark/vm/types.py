import typing
from dataclasses import dataclass

from typing_extensions import TypeVar

from luark.program import Prototype
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
    table: dict[AnyType, AnyType] # todo: maybe change to something better

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


@dataclass
class Function(AnyType):
    prototype: Prototype
    pass

def assert_not_nil(value: AnyType):
    if value is Nil:
        raise NilPointerException()
