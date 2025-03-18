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


class CompiledProgram:
    def __init__(self):
        self.prototype = Prototype()

    def __str__(self):
        return self.prototype.__str__()




