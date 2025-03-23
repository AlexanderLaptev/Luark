class Prototype:
    def __init__(self, func_name: str = None):
        self.func_name = func_name
        self.opcodes: list[str] = []
        self.consts: list[int | float | str] = []
        self.num_locals: int = 0

    def __str__(self) -> str:
        out = [f"locals: {self.num_locals}", "consts:"]
        for i, const in enumerate(self.consts):
            value = const if not isinstance(const, str) else f'"{const}"'
            out.append(f"\t{i}\t\t{value}")
        out.append("opcodes:")
        for i, opcode in enumerate(self.opcodes):
            out.append(f"\t{i}\t\t{opcode}")
        return "\n".join(out)


class Program:
    def __init__(self):
        # By convention, the first prototype is the entry point.
        self.prototypes: list[Prototype] = []

    def __str__(self) -> str:
        out: list[str] = []
        for proto in self.prototypes:
            out.append(f"function {proto.func_name}():")
            out.append(str(proto))
        return "\n".join(out)
