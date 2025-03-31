from luark.compiler import LocalVarIndex, ConstValue, LocalVar, CompiledPrototype
from luark.compiler.ast.block_state import BlockState
from luark.compiler.errors import CompilationError, InternalCompilerError


class PrototypeState:
    locals: LocalVarIndex
    locals_pool: list[int]
    linear_mode: bool

    func_name: str
    fixed_params: int
    is_variadic: bool

    _pc: int

    num_upvalues: int
    num_consts: int
    num_locals: int

    block_stack: list[BlockState]
    upvalues: dict[str, int]
    consts: dict[ConstValue, int]
    opcodes: list[str]

    breaks: list[list[int]]

    def __init__(self, func_name: str = None):
        self.locals = LocalVarIndex()
        self.locals_pool = []
        self.linear_mode = False

        self.func_name = func_name
        self.fixed_params = 0
        self.is_variadic = False

        self._pc = 0

        self.num_upvalues = 0
        self.num_consts = 0
        self.num_locals = 0

        self.block_stack = []
        self.upvalues = {}
        self.consts = {}
        self.opcodes = []

        self.breaks = []

    @property
    def block(self) -> BlockState:
        return self.block_stack[-1]

    @property
    def pc(self):
        return self._pc

    def get_upvalue_index(self, name: str) -> int:
        if name in self.upvalues:
            return self.upvalues[name]
        index = self.num_upvalues
        self.num_upvalues += 1
        self.upvalues[name] = index
        return index

    def get_const_index(self, value: ConstValue) -> int:
        if value in self.consts:
            return self.consts[value]
        index = self.num_consts
        self.num_consts += 1
        self.consts[value] = index
        return index

    def _next_local_index(self) -> int:
        if self.linear_mode or not self.locals_pool:
            index = self.num_locals
            self.num_locals += 1
            return index
        else:
            return self.locals_pool.pop()

    def new_local(self, name: str) -> int:
        index = self._next_local_index()
        self.block.current_locals.add(LocalVar(name, index, self._pc))
        return index

    def get_local_index(self, name: str) -> int:
        if self.block.current_locals.has_name(name):
            var = self.block.current_locals.get_by_name(name)[-1]
            return var.index
        else:
            return self.new_local(name)

    def get_local(self, index: int) -> LocalVar:
        return self.block.current_locals.get_by_index(index)

    def new_temporary(self) -> int:
        var = LocalVar(None, self._next_local_index(), self._pc)
        self.block.current_locals.add(var)
        return var.index

    def release_local(self, index: int):
        self.locals_pool.append(index)

    def add_label(self, name: str):
        if name not in self.block.labels:
            self.block.labels[name] = self.pc
        else:
            raise CompilationError(f"Label '{name}' is already defined.")

    def get_label_target(self, name: str):
        if name in self.block.labels:
            return self.block.labels[name]
        else:
            raise CompilationError(f"Label '{name}' is not defined.")

    def add_opcode(self, opcode):
        if opcode is None:
            raise InternalCompilerError("Attempted to add a None opcode.")
        self.opcodes.append(opcode)
        self._pc += 1

    def reserve_opcodes(self, count: int) -> int:
        pc = self._pc
        for _ in range(count):
            # noinspection PyTypeChecker
            self.opcodes.append(None)
            self._pc += count
        return pc

    def add_jump(self, to: int, from_: int = None):
        if not from_:
            from_ = self._pc
        self.add_opcode(f"jump {to - from_}")

    def set_jump(self, jump_pc: int, target: int = None):
        if not target:
            target = self._pc
        self.opcodes[jump_pc] = f"jump {target - jump_pc}"

    def pop_opcode(self):
        self.opcodes.pop()
        self._pc -= 1

    def add_goto(self, label: str):
        self.block.gotos[self.pc] = (label, len(self.block.current_locals))
        self.reserve_opcodes(1)

    def compile(self) -> CompiledPrototype:
        prototype = CompiledPrototype()
        prototype.func_name = self.func_name
        prototype.opcodes = self.opcodes
        prototype.num_locals = self.num_locals
        prototype.locals = self.locals
        prototype.consts = list(self.consts.keys())
        prototype.upvalues = list(self.upvalues.keys())
        prototype.fixed_params = self.fixed_params
        prototype.is_variadic = self.is_variadic
        return prototype
