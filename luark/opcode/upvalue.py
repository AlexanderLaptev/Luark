from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import AnyType


class UpvalueOpcode(Opcode):
    index: int

    def __init__(self, name: str, index: int):
        super().__init__(name)
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        upvalue = proto.upvalues[self.index]
        assert self.index == upvalue.index
        return f"{upvalue.name}[{self.index}]"


class LoadUpvalue(UpvalueOpcode):
    def __init__(self, index: int):
        super().__init__("load_upvalue", index)

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        env = program_runner.env
        value: AnyType = env.get(self.index)
        program_runner.value_stack.append(value)


class StoreUpvalue(UpvalueOpcode):
    def __init__(self, index: int):
        super().__init__("store_upvalue", index)


class CloseUpvalue(UpvalueOpcode):
    def __init__(self, index: int):
        super().__init__("close_upvalue", index)
