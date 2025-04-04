from luark.opcode import Opcode
from luark.program import Program, Prototype


class Closure(Opcode):
    index: int

    def __init__(self, offset: int):
        super().__init__("closure")
        self.index = offset

    @property
    def arg_str(self) -> str:
        return str(self.index)

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        proto = program.prototypes[self.index]
        name = proto.function_name
        params = [str(proto.fixed_param_count)]
        if proto.is_variadic:
            params.append("...")
        params = ", ".join(params)
        return f"function {name}({params}) [{self.index}]"
