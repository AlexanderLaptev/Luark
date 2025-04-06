from luark.opcode import Opcode
from luark.program import Program, Prototype


class Call(Opcode):
    def __init__(self, param_count: int, return_count: int):
        super().__init__("call")
        self.param_count = param_count
        self.return_count = return_count

    @property
    def arg_str(self) -> str:
        return f"{self.param_count} {self.return_count}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        params = "*" if (self.param_count == 0) else self.param_count - 1
        returns = "*" if (self.return_count == 0) else self.return_count - 1
        return f"p:{params} r:{returns}"
