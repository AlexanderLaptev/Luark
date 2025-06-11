from dataclasses import dataclass

from typing_extensions import TypeVar

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

@dataclass
class Boolean(AnyType):
    value: bool

@dataclass
class Nil(AnyType):
    pass

