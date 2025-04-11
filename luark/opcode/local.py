from luark.opcode import Opcode
from luark.program import Program, Prototype


class LocalOpcode(Opcode):
    index: int

    def __init__(self, name: str, index: int):
        super().__init__(name)
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        local = proto.locals.by_index(self.index)
        name = local.name if local.name is not None else "(temp)"
        return f"{name}[{self.index}]"


class LoadLocal(LocalOpcode):
    def __init__(self, index: int):
        super().__init__("load_local", index)


class StoreLocal(LocalOpcode):
    def __init__(self, index: int):
        super().__init__("store_local", index)


class MarkTBC(LocalOpcode):
    def __init__(self, index: int):
        super().__init__("mark_tbc", index)
