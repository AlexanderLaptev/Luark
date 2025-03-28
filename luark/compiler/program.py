class Prototype:
    def __init__(self, func_name: str = None):
        self.func_name = func_name
        self.fixed_params: int = 0
        self.is_variadic: bool = False
        self.opcodes: list[str] = []
        self.consts: list[int | float | str] = []
        self.num_locals: int = 0
        self.upvalues: list[str] = []

    def __str__(self) -> str:
        out = [f"\tlocals: {self.num_locals}", "\tupvalues:"]
        for i, upvalue in enumerate(self.upvalues):
            out.append(f"\t\t{i}\t\t{upvalue}")
        out.append("\tconsts:")
        for i, const in enumerate(self.consts):
            value = const if not isinstance(const, str) else f'"{const}"'
            out.append(f"\t\t{i}\t\t{value}")
        out.append("\topcodes:")
        for i, opcode in enumerate(self.opcodes):
            out.append(f"\t\t{i}\t\t{opcode}")
        return "\n".join(out)


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
            out.append(f"[{i}]function {proto.func_name}{arg_string}:")
            out.append(str(proto))
        return "\n".join(out)
