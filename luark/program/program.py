from __future__ import annotations

import pickle
from dataclasses import dataclass
from typing import TypeAlias

from luark.compiler.exceptions import InternalCompilerError
from luark.opcode import Opcode

ConstantPoolType: TypeAlias = int | float | bytes  # all the types that can be put in a constant pool


@dataclass
class LocalVariable:
    name: str
    index: int
    start: int
    end: int | None = None
    is_const: bool = False


class LocalVariableStore:
    def __init__(self):
        self._locals: list[LocalVariable] = []
        self._lookup: dict[str, LocalVariable] = {}

    def add(self, local: LocalVariable):
        self._locals.append(local)
        self._lookup[local.name] = local

    def by_index(self, index: int) -> LocalVariable:
        for local in self._locals:
            if local.index == index:
                return local
        raise InternalCompilerError(f"local variable with index {index} not found")

    def by_name(self, name: str) -> LocalVariable:
        return self._lookup[name]

    def merge(self, other: LocalVariableStore):
        for local in other:
            self.add(local)

    def __len__(self):
        return len(self._locals)

    def __iter__(self):
        return iter(self._locals)


class Prototype:
    opcodes: list[Opcode]
    constant_pool: list[ConstantPoolType]
    locals: LocalVariableStore
    num_locals: int


class Program:
    prototypes: list[Prototype]

    def __init__(self):
        self.prototypes: list[Prototype] = []

    def serialize(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def deserialize(program: bytes) -> Program:
        return pickle.loads(program)
