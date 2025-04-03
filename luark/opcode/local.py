from luark.opcode import Opcode


class LoadLocal(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("load_local")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"


class StoreLocal(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("store_local")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"


class MarkTBC(Opcode):
    index: int

    def __init__(self, index: int):
        super().__init__("mark_tbc")
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"
