from typing import TypeAlias

ConstType: TypeAlias = int | float | bytes


class _PrototypeState:
    def __init__(self):
        from luark.opcode import Opcode

        self.opcodes: list[Opcode] = []


class CompilerState:
    from luark.opcode import Opcode

    def __init__(self):
        self.consts: dict[ConstType, int] = {}
        self.protos: list[_PrototypeState] = []

    def begin_chunk(self) -> None:
        pass

    def end_chunk(self) -> None:
        pass

    def begin_proto(self) -> None:
        pass

    def end_proto(self) -> None:
        pass

    def add_opcode(self, opcode: Opcode) -> None:
        pass

    def get_const_index(self, value: ConstType) -> int:
        if value in self.consts:
            return self.consts[value]
        else:
            index = len(self.consts)
            self.consts[value] = index
            return index

    def get_const(self, index: int) -> ConstType:
        for k, v in self.consts.items():
            if v == index:
                return k
        raise IndexError
