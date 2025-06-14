from luark.opcode import Opcode
from luark.program import Program, Prototype
from luark.vm.exception import TypeException
from luark.vm.luavm import ProgramRunner, PrototypeRunner
from luark.vm.types import Function, NativeFunction, Nil


class Call(Opcode):
    def __init__(self, param_count: int, return_count: int):
        super().__init__("call")
        self.param_count = param_count
        self.return_count = return_count

    @property
    def arg_str(self) -> str:
        return f"{self.param_count} {self.return_count}"

    def comment_str(self, program: Program, proto: Prototype, pc: int) -> str:
        returns = "*" if (self.return_count == 0) else self.return_count - 1
        return f"p:{self.param_count} r:{returns}"

    def run(self, program_runner: ProgramRunner, prototype_runner: PrototypeRunner):
        program_runner.params = self.param_count
        program_runner.returns = self.return_count

        closure = program_runner.value_stack.pop()
        if isinstance(closure, Function):
            expected_args = closure.prototype.fixed_param_count
            mark = program_runner.peek_mark()
            actual_args = len(program_runner.value_stack) - mark

            # HACK: a hack to allow dynamic extensions
            nil_count = max(0, expected_args - actual_args)
            if nil_count > 0:
                nils = [Nil()] * nil_count
                program_runner.value_stack.insert(mark, *nils)

            program_runner.push_prototype(closure.prototype)
            prototype_runner.step()
        elif isinstance(closure, NativeFunction):
            closure.function(program_runner, prototype_runner)
            program_runner.pop_mark()
            prototype_runner.step()
        else:
            raise TypeException(prototype_runner=prototype_runner, message="Cannot call a non-callable object")
