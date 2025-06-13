from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import AnyType


class LocalOpcode(Opcode):
    index: int

    def __init__(self, name: str, index: int):
        super().__init__(name)
        self.index = index

    @property
    def arg_str(self) -> str:
        return f"{self.index}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        local = proto.locals.by_index(self.index)
        name = local.name if local.name is not None else "(temp)"
        return f"{name}[{self.index}]"


class LoadLocal(LocalOpcode):
    def __init__(self, index: int):
        super().__init__("load_local", index)

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value: AnyType = prototype_runner.local_variables[self.index]
        program_runner.value_stack.append(value)
        prototype_runner.step()


class StoreLocal(LocalOpcode):
    def __init__(self, index: int):
        super().__init__("store_local", index)

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value: AnyType = program_runner.value_stack.pop()
        prototype_runner.local_variables[self.index] = value
        prototype_runner.step()


class MarkTBC(LocalOpcode):
    def __init__(self, index: int):
        super().__init__("mark_tbc", index)
