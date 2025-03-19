from luark.utils import Index


class Prototype:
    def __init__(self, parent=None):
        self.consts = Index()
        self.opcodes: list[str] = []
        self.locals: list[str] = []

    def __str__(self):
        result = ["constants:"]
        for i, c in enumerate(self.consts):
            name = str(c)
            if isinstance(c, str):
                name = '"' + name + '"'
            result.append(f"\t{i}\t\t{name}")
        result.append("instructions:")
        for i, o in enumerate(self.opcodes):
            result.append(f"\t{i}\t\t{o}")
        return "\n".join(result)

    def get_const(self, const):
        return self.consts.get_or_add(const)

    def add_opcode(self, opcode):
        self.opcodes.append(opcode)

    def set_opcode(self, pc: int, opcode):
        self.opcodes[pc] = opcode

    current_pc = property(lambda self: len(self.opcodes) - 1)

    def set_jump_here(self, pc: int):
        self.opcodes[pc] = f"jump {self.current_pc - pc + 1}"

    def add_jump_to(self, pc: int):
        self.add_opcode(f"jump {pc - self.current_pc - 1}")

    def remember(self) -> int:
        self.opcodes.append("")
        return self.current_pc


class CompiledProgram:
    def __init__(self):
        self.prototype = Prototype()

    def __str__(self):
        return self.prototype.__str__()
