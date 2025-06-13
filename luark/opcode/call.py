from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Function


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

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        function = program_runner.value_stack.pop()
        if function is not Function:
            raise TypeException(prototype_runner=prototype_runner, message="Can not call not a function object")
        # todo: do some magic with arguments adjustment and/or varargs
        assert isinstance(function, Function)
        program_runner.push_prototype(function.prototype)
