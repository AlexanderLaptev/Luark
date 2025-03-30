from dataclasses import dataclass
from typing import Self


@dataclass
class LocalVar:
    name: str | None
    index: int
    start: int
    end: int | None = None
    is_const: bool = False

    def __str__(self) -> str:
        name = self.name if self.name else "(tmp)"
        return f"{name}#{self.index} - {self.start}:{self.end}"


class LocalVarIndex:
    index_lookup: dict[int, LocalVar]
    name_lookup: dict[str, list[LocalVar]]
    index: list[LocalVar]

    def __init__(self):
        self.name_lookup = {}
        self.index_lookup = {}
        self.index = []

    def __len__(self):
        return len(self.index)

    def __iter__(self):
        return iter(self.index)

    def __contains__(self, item):
        return item in self.index

    def add(self, var: LocalVar):
        self.index.append(var)
        self.index_lookup[var.index] = var
        if var.name:
            if var.name in self.name_lookup:
                self.name_lookup[var.name].append(var)
            else:
                self.name_lookup[var.name] = [var]

    def merge(self, other: Self):
        for var in other:
            self.add(var)

    def get_by_index(self, index: int) -> LocalVar:
        return self.index_lookup[index]

    def get_by_name(self, name: str) -> list[LocalVar]:
        return self.name_lookup[name]

    def has_index(self, index: int) -> bool:
        return index in self.index_lookup

    def has_name(self, name: str) -> bool:
        return name in self.name_lookup


class Prototype:
    locals: LocalVarIndex

    def __init__(self, func_name: str = None):
        self.func_name = func_name
        self.fixed_params: int = 0
        self.is_variadic: bool = False
        self.opcodes: list[str] = []
        self.consts: list[int | float | str] = []
        self.num_locals: int = 0
        self.upvalues: list[str] = []

    def __str__(self) -> str:
        out = [f"\tlocals({self.num_locals}):"]
        for var in self.locals:
            name = var.name if var.name else "(temp)"
            out.append(f"\t\t{name}[{var.index}] - {var.start}:{var.end}")

        out.append("\tupvalues:")
        for i, upvalue in enumerate(self.upvalues):
            out.append(f"\t\t{i}\t\t\"{upvalue}\"")

        out.append("\tconsts:")
        for i, const in enumerate(self.consts):
            value = const if not isinstance(const, str) else f'"{const}"'
            out.append(f"\t\t{i}\t\t{value}")

        out.append("\topcodes:")
        for i, opcode in enumerate(self.opcodes):
            result = self._opcode_to_str(i, opcode)
            out.append(result)
        return "\n".join(out)

    def _opcode_to_str(self, line: int, opcode: str):
        result = f"\t\t{line}\t\t" + opcode
        parts = opcode.split(" ")
        args = [int(x) for x in parts[1:]]
        command = parts[0]

        match command:
            case "push_const":
                const = self.consts[args[0]]
                if isinstance(const, str):
                    const = '"' + const + '"'
                result += f"\t\t// {const}"
            case "load_local" | "store_local":
                local = self.locals.get_by_index(args[0])
                result += f"\t\t// {local}"
            case "get_upvalue":
                upvalue = self.upvalues[args[0]]
                result += f"\t\t// {upvalue}"
        return result


class Program:
    def __init__(self):
        # By convention, the first prototype is the entry point.
        self.prototypes: list[Prototype] = []

    def __str__(self) -> str:
        out: list[str] = []
        for i, proto in enumerate(self.prototypes):
            arg_string = "("
            arg_string += str(proto.fixed_params)
            if proto.is_variadic:
                arg_string += ", ..."
            arg_string += ")"
            out.append(f"[{i}] function {proto.func_name}{arg_string}:")
            out.append(str(proto) + "\n")
        return "\n".join(out)
