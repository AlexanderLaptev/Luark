from luark.opcode import Opcode
from luark.program import Program, Prototype


def _format_local(index: int, proto: Prototype) -> str:
    local = proto.locals.by_index(index)
    return f"{local.name}[{index}]"


class LoadLocal(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("load_local")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype) -> str:
        return _format_local(self.index, proto)


class StoreLocal(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("store_local")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype) -> str:
        return _format_local(self.index, proto)


class MarkTBC(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("mark_tbc")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype) -> str:
        return _format_local(self.index, proto)
