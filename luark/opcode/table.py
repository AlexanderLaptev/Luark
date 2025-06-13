from typing import Self

from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Table


class CreateTable(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert CreateTable.INSTANCE is None
        super().__init__("create_table")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        value = Table()
        program_runner.value_stack.append(value)
        prototype_runner.step()


CreateTable.INSTANCE = CreateTable()


class GetTable(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert GetTable.INSTANCE is None
        super().__init__("get_table")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        key = program_runner.value_stack.pop()
        table = program_runner.value_stack.pop()

        if not isinstance(table, Table):
            raise TypeException(prototype_runner, message="Not a table")
        assert isinstance(table, Table)

        value = table.get(key)
        program_runner.value_stack.append(value)
        prototype_runner.step()


GetTable.INSTANCE = GetTable()


class SetTable(Opcode):
    INSTANCE: Self = None

    def __init__(self):
        assert SetTable.INSTANCE is None
        super().__init__("set_table")

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        key = program_runner.value_stack.pop()
        table = program_runner.value_stack.pop()
        value = program_runner.value_stack.pop()

        if not isinstance(table, Table):
            raise TypeException(prototype_runner, message="Not a table")
        assert isinstance(table, Table)

        table.set(key, value)
        prototype_runner.step()


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
