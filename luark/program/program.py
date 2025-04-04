from __future__ import annotations

import pickle
from dataclasses import dataclass
from typing import TypeAlias

import tabulate

from luark.compiler.exceptions import InternalCompilerError
from luark.opcode import Opcode

ConstantPoolType: TypeAlias = int | float | bytes  # all the types that can be put in a constant pool

tabulate.PRESERVE_WHITESPACE = True
tabulate.MIN_PADDING = 0


def _indent_lines(string: str, level: int = 1) -> str:
    indent = " " * 4
    lines = string.splitlines()
    for i, line in enumerate(lines):
        lines[i] = indent * level + line
    return "\n".join(lines)


def _tabulate(data):
    return tabulate.tabulate(data, headers="firstrow", tablefmt="plain", disable_numparse=True)


@dataclass(frozen=True)
class Upvalue:
    index: int
    name: str
    is_on_stack: bool


@dataclass
class LocalVariable:
    index: int
    start: int
    name: str | None = None
    end: int | None = None
    is_const: bool = False


class LocalVariableStore:
    def __init__(self):
        self._locals: list[LocalVariable] = []
        self._name_lookup: dict[str, list[LocalVariable]] = {}
        self._index_lookup: dict[int, LocalVariable] = {}

    def add(self, local: LocalVariable):
        self._locals.append(local)
        if local.name:
            if local.name not in self._name_lookup:
                self._name_lookup[local.name] = []
            self._name_lookup[local.name].append(local)
        self._index_lookup[local.index] = local

    def by_index(self, index: int) -> LocalVariable:
        for local in self._locals:
            if local.index == index:
                return local
        raise InternalCompilerError(f"local variable with index {index} not found")

    def by_name(self, name: str) -> LocalVariable:
        return self._name_lookup[name][-1]

    def by_name_all(self, name: str) -> list[LocalVariable]:
        return self._name_lookup[name]

    def has_name(self, name: str) -> bool:
        return name in self._name_lookup

    def merge(self, other: LocalVariableStore):
        for local in other:
            self.add(local)

    def __len__(self):
        return len(self._locals)

    def __iter__(self):
        return iter(self._locals)


class Prototype:
    function_name: str
    fixed_param_count: int
    is_variadic: bool

    opcodes: list[Opcode]
    constant_pool: list[ConstantPoolType]
    locals: LocalVariableStore
    upvalues: list[Upvalue]
    num_locals: int


class Program:
    prototypes: list[Prototype]

    def __init__(self):
        self.prototypes: list[Prototype] = []

    def __str__(self) -> str:
        output = []
        for i, proto in enumerate(self.prototypes):
            name = proto.function_name
            params = [str(proto.fixed_param_count)]
            if proto.is_variadic:
                params.append("...")
            params = ", ".join(params)

            output.append(f"function {name}({params}): [{i}]")
            output.append(_indent_lines(self._proto_str(proto)))
            output.append("end")
            output.append("")

        return "\n".join(output)

    def _proto_str(self, proto: Prototype) -> str:
        output = []

        table = []
        for i, opcode in enumerate(proto.opcodes):
            row = [i, opcode.name, opcode.arg_str, opcode.comment_str(self, proto, i)]
            if row[-1]:
                row[-1] = "; " + row[-1]
            for j in range(1, len(row)):
                row[j] = "  " + row[j]
            table.append(row)
        output.append(_tabulate(table))
        output.append("")

        if proto.constant_pool:
            output.append(f"consts({len(proto.constant_pool)}):")
            table = [["index", "type", "value"]]
            for i, const in enumerate(proto.constant_pool):
                stype: str = ""
                if isinstance(const, bytes):
                    const = str(const)[1:]
                    stype = "string"
                elif isinstance(const, int):
                    stype = "int"
                elif isinstance(const, float):
                    stype = "float"
                row = [i, stype, const]
                table.append(row)
            output.append(_indent_lines(_tabulate(table)))
            output.append("")

        if proto.locals:
            output.append(f"locals({len(proto.locals)}):")
            table = [["index", "name", "start", "end"]]
            for i, local in enumerate(proto.locals):
                name = local.name if local.name is not None else "(temp)"
                row = [i, name, local.start, local.end]
                table.append(row)
            output.append(_indent_lines(_tabulate(table)))
            output.append("")

        if proto.upvalues:
            output.append(f"upvalues({len(proto.upvalues)}):")
            table = [["index", "name", "on stack?"]]
            for i, upvalue in enumerate(proto.upvalues):
                row = [i, upvalue.name, str(upvalue.is_on_stack).lower()]
                table.append(row)
            output.append(_indent_lines(_tabulate(table)))

        return "\n".join(output)

    def serialize(self) -> bytes:
        return pickle.dumps(self)

    @staticmethod
    def deserialize(program: bytes) -> Program:
        return pickle.loads(program)
