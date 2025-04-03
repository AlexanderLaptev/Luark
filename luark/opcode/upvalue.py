from luark.opcode import Opcode
from luark.program import Program, Prototype


def _format_upvalue(index: int, proto: Prototype) -> str:
    upvalue = proto.upvalues[index]
    return f"{upvalue.name}[{upvalue.index}]"


class LoadUpvalue(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("load_upvalue")
        self.index = index

    @property
    def arg_str(self) -> str:
        return str(self.index)

    def comment_str(self, program: Program, proto: Prototype) -> str:
        return _format_upvalue(self.index, proto)


class StoreUpvalue(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("store_upvalue")
        self.index = index

    @property
    def arg_str(self) -> str:
        return str(self.index)

    def comment_str(self, program: Program, proto: Prototype) -> str:
        return _format_upvalue(self.index, proto)
