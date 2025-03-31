from enum import Enum, auto

from luark.compiler import CompiledProgram
from luark.compiler.ast.block_state import BlockState
from luark.compiler.ast.prototype_state import PrototypeState
from luark.compiler.errors import CompilationError


class _ProgramState:
    protos: list[PrototypeState]
    proto_stack: list[PrototypeState]
    num_lambdas: int

    class _ResolveAction(Enum):
        LOAD = auto()
        STORE = auto()

    def __init__(self):
        self.protos = []
        self.proto_stack = []
        self.num_lambdas = 0

    @property
    def proto(self) -> PrototypeState | None:
        if self.proto_stack:
            return self.proto_stack[-1]
        else:
            return None

    def push_proto(self, func_name: str = None) -> tuple[PrototypeState, int]:
        proto_state = PrototypeState(func_name)
        index = len(self.protos)
        self.protos.append(proto_state)
        self.proto_stack.append(proto_state)
        return proto_state, index

    def pop_proto(self):
        self.proto_stack.pop()

    def get_proto(self, index: int) -> PrototypeState:
        return self.protos[index]

    def push_block(self) -> BlockState:
        block = BlockState()
        self.proto.block_stack.append(block)
        return block

    def pop_block(self):
        proto = self.proto
        block = proto.block_stack.pop()
        end = self.proto.pc - 1
        for var in block.current_locals:
            var.end = end
            proto.release_local(var.index)
        self.proto.locals.merge(block.current_locals)

    def read(self, state: "_ProgramState", name: str):
        self._resolve(name, state, self._ResolveAction.LOAD)

    def assign(self, state: "_ProgramState", name: str):
        self._resolve(name, state, self._ResolveAction.STORE)

    def _resolve(self, name: str, state: "_ProgramState", action: _ResolveAction):
        current_proto = self.proto
        visited_protos = []  # these protos may need an upvalue passed down to them
        for proto in reversed(self.proto_stack):
            visited_protos.append(proto)
            upvalue = self.proto != proto  # upvalues are locals from an enclosing function
            for block in reversed(proto.block_stack):
                if name in block.const_locals:  # check consts first
                    block.const_locals[name].evaluate(state)
                    return
                if block.current_locals.has_name(name):  # then check locals (and upvalues)
                    if upvalue:
                        # A local variable in an outer function. Create an
                        # upvalue and drill it through the proto stack.
                        for vp in visited_protos:
                            vp.get_upvalue_index(name)
                        upvalue_index = current_proto.get_upvalue_index(name)

                        opcode: str
                        if action == self._ResolveAction.LOAD:
                            opcode = "load_upvalue"
                        else:
                            opcode = "store_upvalue"

                        current_proto.add_opcode(f"{opcode} {upvalue_index}")
                    else:
                        # A local variable in the same function.
                        var = block.current_locals.get_by_name(name)[-1]
                        local_index = var.index

                        if var.is_const:
                            if var.const_value:  # compile time constant
                                const_index = current_proto.get_const_index(var.const_value)
                                current_proto.add_opcode(f"push_const {const_index}")
                            else:  # runtime constant
                                if action == self._ResolveAction.STORE:
                                    raise CompilationError(f"Cannot reassign constant variable '{name}'.")
                                current_proto.add_opcode(f"load_local {local_index}")
                            return

                        opcode: str
                        if action == self._ResolveAction.LOAD:
                            opcode = "load_local"
                        else:
                            opcode = "store_local"

                        current_proto.add_opcode(f"{opcode} {local_index}")
                    return

        # If we could not find the local either in the same function or
        # in any of the enclosing ones, treat the variable as a global.
        env_index: int
        for proto in self.proto_stack:
            env_index = proto.get_upvalue_index("_ENV")
        name_index = current_proto.get_const_index(name)
        # noinspection PyUnboundLocalVariable
        current_proto.add_opcode(f"get_upvalue {env_index}")
        current_proto.add_opcode(f"push_const {name_index}")

        opcode: str
        if action == self._ResolveAction.LOAD:
            opcode = "get_table"
        else:
            opcode = "set_table"
        current_proto.add_opcode(opcode)

    def compile(self) -> CompiledProgram:
        program = CompiledProgram()
        for proto in self.protos:
            program.prototypes.append(proto.compile())
        return program

    def next_lambda_index(self) -> int:
        index = self.num_lambdas
        self.num_lambdas += 1
        return index
