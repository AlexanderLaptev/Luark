from luark.opcode import Opcode


class GetTable(Opcode):
    def __init__(self):
        super().__init__("get_table")


class SetTable(Opcode):
    def __init__(self):
        super().__init__("set_table")
