from dataclasses import dataclass

from typing_extensions import TypeVar

T = TypeVar('T')

@dataclass
class AnyType:
    pass

@dataclass
class Number(AnyType):
    value: float

@dataclass
class String(AnyType):
    value: str

@dataclass
class Boolean(AnyType):
    value: bool

@dataclass
class Nil(AnyType):
    pass

