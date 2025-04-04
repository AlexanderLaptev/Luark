from luark.opcode import Opcode


class PrepareForNumeric(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("prepare_for_num")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)


class PrepareForGeneric(Opcode):
    control_index: int

    def __init__(self, control_index: int):
        super().__init__("prepare_for_gen")
        self.control_index = control_index

    @property
    def arg_str(self) -> str:
        return str(self.control_index)
