from __future__ import annotations

import typing
from typing import Literal

from lark.tree import Meta

from luark.compiler.exceptions import CompilationError, InternalCompilerError
from luark.opcode.jump import Jump
from luark.opcode.local import LoadLocal, StoreLocal
from luark.opcode.push import PushConst
from luark.opcode.table import GetTable, SetTable
from luark.opcode.upvalue import LoadUpvalue, StoreUpvalue
from luark.program import Prototype
from luark.program.program import ConstantPoolType, LocalVariable, LocalVariableStore, Program, Upvalue

if typing.TYPE_CHECKING:
    from luark.compiler.ast.expressions import CompileTimeConstant


class _BlockState:
    def __init__(self):
        self.locals = LocalVariableStore()
        self.tbc_locals: list[LocalVariable] = []
        self.consts: dict[str, CompileTimeConstant] = {}
        self.break_stack: list[list[int]] = []


class _PrototypeState:
    def __init__(
            self,
            func_name: str,
            fixed_param_count: int,
            is_variadic: bool,
    ):
        from luark.opcode import Opcode

        self.func_name = func_name
        self.fixed_param_count = fixed_param_count
        self.is_variadic = is_variadic

        self.consts: dict[int | float | bytes, int] = {}
        self.opcodes: list[Opcode] = []
        self.blocks: list[_BlockState] = []
        self.block_stack: list[_BlockState] = []
        self.locals = LocalVariableStore()
        self.released_local_indices: set[int] = set()
        self.upvalues: dict[str, Upvalue] = {}
        self.program_counter = 0  # always points after the last opcode
        self.num_locals = 0


class CompilerState:
    from luark.opcode import Opcode

    def __init__(self):
        self._num_lambdas = 0

        self._protos: list[_PrototypeState] = []
        self._stack: list[_PrototypeState] = []
        self._current_proto: _PrototypeState | None = None
        self._current_block: _BlockState | None = None

    def begin_proto(
            self,
            function_name: str,
            fixed_param_count: int,
            is_variadic: bool,
    ) -> None:
        proto = _PrototypeState(function_name, fixed_param_count, is_variadic)
        self._protos.append(proto)
        self._stack.append(proto)
        self._current_proto = proto

    def end_proto(self) -> None:
        self._current_proto = self._stack.pop()

    @property
    def program_counter(self) -> int:
        return self._current_proto.program_counter

    def begin_block(self) -> None:
        block_state = _BlockState()
        self._current_proto.block_stack.append(block_state)
        self._current_proto.blocks.append(block_state)
        self._current_block = block_state

    def end_block(self) -> None:
        # When a block exits, all of its locals leave the lexical scope
        # and are therefore no longer visible
        for local in self._current_block.locals:
            local.end = self.program_counter

        self._current_proto.locals.merge(self._current_block.locals)

        self._current_proto.block_stack.pop()
        if self._current_proto.block_stack:
            self._current_block = self._current_proto.block_stack[-1]
        else:
            self._current_block = None

    def begin_loop(self) -> None:
        self._current_block.break_stack.append([])

    def end_loop(self) -> None:
        breaks = self._current_block.break_stack.pop()
        for br in breaks:
            self.set_jump(br)

    def next_lambda_index(self) -> int:
        result = self._num_lambdas
        self._num_lambdas += 1
        return result

    def add_opcode(self, opcode: Opcode | None) -> None:
        self._current_proto.opcodes.append(opcode)
        self._current_proto.program_counter += 1

    def reserve_opcode(self) -> int:
        pc = self._current_proto.program_counter
        self.add_opcode(None)
        return pc

    def add_jump(self, target: int = None):
        self.add_opcode(Jump(target - self._current_proto.program_counter))

    def set_jump(self, opcode_pc: int, target: int = None):
        pc = self._current_proto.program_counter
        if not target:
            target = pc
        self._current_proto.opcodes[opcode_pc] = Jump(target - opcode_pc)

    def add_break(self, meta: Meta):
        if not self._current_block.break_stack:
            raise CompilationError("break statement is not allowed outside of a loop", meta)
        pc = self._current_proto.program_counter
        self.reserve_opcode()
        self._current_block.break_stack[-1].append(pc)

    def get_const_index(self, value: ConstantPoolType | str) -> int:
        if isinstance(value, str):
            value = value.encode("utf-8")  # automatically encode strings in UTF-8
        if not isinstance(value, ConstantPoolType):
            raise InternalCompilerError(f"cannot put {value} of type {type(value)} into the constant pool")

        if value in self._current_proto.consts:
            return self._current_proto.consts[value]
        else:
            index = len(self._current_proto.consts)
            self._current_proto.consts[value] = index
            return index

    def add_locals(self, name: str | None, count: int = 1) -> LocalVariable:
        assert count > 0, "count must be positive"
        reuse = count == 1
        pc = self._current_proto.program_counter
        local = LocalVariable(self._next_local_index(reuse), pc, name)
        self._current_block.locals.add(local)
        for _ in range(count - 1):
            temp = LocalVariable(self._next_local_index(), pc, None)
            self._current_block.locals.add(temp)
        return local

    def add_temporaries(self, count: int) -> int:
        return self.add_locals(None, count).index

    def get_local(self, name: str) -> LocalVariable:
        return self._current_block.locals.by_name(name)

    def release_local(self, index: int) -> None:
        self._current_proto.released_local_indices.add(index)

    def _next_local_index(self, reuse: bool = True) -> int:
        if reuse and self._current_proto.released_local_indices:
            return self._current_proto.released_local_indices.pop()
        else:
            index = self._current_proto.num_locals
            self._current_proto.num_locals += 1
            return index

    def add_const_local(self, name: str, expression: CompileTimeConstant) -> None:
        self._current_block.consts[name] = expression

    def _get_upvalue(self, name: str) -> Upvalue:
        if name in self._current_proto.upvalues:
            return self._current_proto.upvalues[name]
        raise InternalCompilerError(f"could not find upvalue '{name}'")

    def _add_upvalue_chain(self, name: str, stack: list[_PrototypeState]):
        top = stack[0]
        if name in top.upvalues:
            return

        top.upvalues[name] = Upvalue(len(top.upvalues), name, True if name != "_ENV" else False)
        for proto in stack[1:]:
            proto.upvalues[name] = Upvalue(len(proto.upvalues), name, False)

    def resolve_variable(self, meta: Meta, name: str, operation: Literal["read", "write"]):
        if operation not in ("read", "write"):
            raise InternalCompilerError(f"illegal operation: {operation}")

        visited_protos = []
        for proto in reversed(self._stack):
            visited_protos.append(proto)
            is_upvalue = self._current_proto != proto

            for block in reversed(proto.block_stack):
                if name in block.consts:  # compile-time constant
                    if operation == "write":
                        raise InternalCompilerError(f"cannot assign compile-time constant '{name}'")
                    block.consts[name].evaluate(self)
                    return

                if name in block.locals:
                    if is_upvalue:  # upvalue
                        self._add_upvalue_chain(name, visited_protos)
                        index = self._get_upvalue(name).index

                        if operation == "read":
                            self.add_opcode(LoadUpvalue(index))
                        elif operation == "write":
                            self.add_opcode(StoreUpvalue(index))
                    else:  # local or runtime const
                        local = self.get_local(name)
                        index = local.index
                        if operation == "read":
                            self.add_opcode(LoadLocal(index))
                        elif operation == "write":
                            if local.is_const:
                                raise CompilationError(f"cannot reassign constant '{name}'", meta)
                            self.add_opcode(StoreLocal(index))
                    return

            # global variable
            self._add_upvalue_chain("_ENV", visited_protos)
            env_index = self._get_upvalue("_ENV").index
            name_index = self.get_const_index(name)
            self.add_opcode(LoadUpvalue(env_index))
            self.add_opcode(PushConst(name_index))
            if operation == "read":
                self.add_opcode(GetTable.INSTANCE)
            elif operation == "write":
                self.add_opcode(SetTable.INSTANCE)

    def compile(self) -> Program:
        protos: list[Prototype] = []
        for proto_state in self._protos:
            assert None not in proto_state.opcodes

            proto = Prototype()
            proto.function_name = proto_state.func_name
            proto.fixed_param_count = proto_state.fixed_param_count
            proto.is_variadic = proto_state.is_variadic
            proto.opcodes = proto_state.opcodes
            proto.constant_pool = list(proto_state.consts)
            proto.num_locals = proto_state.num_locals
            proto.locals = proto_state.locals
            proto.upvalues = list(proto_state.upvalues.values())
            protos.append(proto)

        program = Program()
        program.prototypes = protos

        return program
