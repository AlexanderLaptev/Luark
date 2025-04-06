from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype


class CreateTable(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert CreateTable.INSTANCE is None
        super().__init__("create_table")


CreateTable.INSTANCE = CreateTable()


class GetTable(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert GetTable.INSTANCE is None
        super().__init__("get_table")


GetTable.INSTANCE = GetTable()


class SetTable(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert SetTable.INSTANCE is None
        super().__init__("set_table")


SetTable.INSTANCE = SetTable()


class StoreList(Opcode):
    count: int

    def __init__(self, offset: int):
        super().__init__("store_list")
        self.count = offset

    @property
    def arg_str(self) -> str:
        return str(self.count)

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        return "all" if (self.count == 0) else str(self.count)
