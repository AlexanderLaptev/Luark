from typing import Self

from luark.opcode import Opcode


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
