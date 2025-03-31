from dataclasses import dataclass
from typing import Self, TypeAlias

ConstValue: TypeAlias = int | float | str


@dataclass
class LocalVar:
    name: str | None
    index: int
    start: int
    end: int | None = None
    is_const: bool = False
    const_value: ConstValue | None = None


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


class CompiledPrototype:
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
            parts = opcode.split(" ")
            own_name = parts[0]
            result = f"\t\t{i}\t\t{opcode}"
            if own_name.endswith("local"):
                index = int(parts[1])
                name = self.locals.get_by_index(index).name
                if not name:
                    name = "(temp)"
                result += f"  // '{name}'"
            elif own_name == "push_const":
                index = int(parts[1])
                result += f"  // {self.consts[index]}"
            elif own_name == "get_upvalue":
                index = int(parts[1])
                result += f"  // '{self.upvalues[index]}'"
            elif own_name == "jump":
                target = i + int(parts[1])
                result += f"  // to {target}"
            elif own_name == "call":
                params = int(parts[1])
                returns = int(parts[2])
                params = "(all)" if (params == 0) else params - 1
                returns = "(all)" if (returns == 0) else returns - 1
                result += f"  // par:{params} ret:{returns}"
            out.append(result)
        return "\n".join(out)


class CompiledProgram:
    def __init__(self):
        # By convention, the first prototype is the entry point.
        self.prototypes: list[CompiledPrototype] = []

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
