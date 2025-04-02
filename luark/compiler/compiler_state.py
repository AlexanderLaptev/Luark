from __future__ import annotations

import typing
from dataclasses import dataclass
from typing import Literal, TypeAlias

from luark.compiler.exceptions import CompilationError, InternalCompilerError
from luark.opcode.local import LoadLocal, StoreLocal
from luark.opcode.upvalue import LoadUpvalue, StoreUpvalue

if typing.TYPE_CHECKING:
    from luark.compiler.ast.expressions import CompileTimeConstant

_ConstType: TypeAlias = int | float | bytes


@dataclass
class LocalVariable:
    name: str
    index: int
    start: int
    end: int | None = None
    is_const: bool = False


class _LocalVariableStore:
    def __init__(self):
        self._locals: list[LocalVariable] = []
        self._lookup: dict[str, LocalVariable] = {}

    def add(self, local: LocalVariable):
        self._locals.append(local)
        self._lookup[local.name] = local

    def by_index(self, index: int) -> LocalVariable:
        for local in self._locals:
            if local.index == index:
                return local
        raise InternalCompilerError(f"local variable with index {index} not found")

    def by_name(self, name: str) -> LocalVariable:
        return self._lookup[name]

    def __iter__(self):
        return iter(self._locals)


class _BlockState:
    def __init__(self):
        self.locals = _LocalVariableStore()
        self.tbc_locals: list[LocalVariable] = []
        self.consts: dict[str, CompileTimeConstant] = {}


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

        self.opcodes: list[Opcode] = []
        self.block_stack: list[_BlockState] = []
        self.program_counter = 0  # always points after the last opcode


class CompilerState:
    from luark.opcode import Opcode

    def __init__(self):
        self._consts: dict[int | float | bytes, int] = {}
        self._released_local_indices: set[int] = set()
        self._num_lambdas = 0
        self._num_locals = 0

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
        self._current_block = block_state

    def end_block(self) -> None:
        # When a block exits, all of its locals leave the lexical scope
        # and are therefore no longer visible
        for local in self._current_block.locals:
            local.end = self.program_counter

        self._current_proto.block_stack.pop()
        if self._current_proto.block_stack:
            self._current_block = self._current_proto.block_stack[-1]
        else:
            self._current_block = None

    def next_lambda_index(self) -> int:
        result = self._num_lambdas
        self._num_lambdas += 1
        return result

    def add_opcode(self, opcode: Opcode) -> None:
        self._current_proto.opcodes.append(opcode)
        self._current_proto.program_counter += 1

    def get_const_index(self, value: _ConstType) -> int:
        if value in self._consts:
            return self._consts[value]
        else:
            index = len(self._consts)
            self._consts[value] = index
            return index

    def new_local(self, name: str) -> LocalVariable:
        index = self._next_local_index()
        local = LocalVariable(name, index, self.program_counter)
        self._current_block.locals.add(local)
        return local

    def get_local(self, name: str) -> LocalVariable:
        return self._current_block.locals.by_name(name)

    def _next_local_index(self, reuse: bool = True) -> int:
        if reuse and self._released_local_indices:
            return self._released_local_indices.pop()
        else:
            index = self._num_locals
            self._num_locals += 1
            return index

    def add_const_local(self, name: str, expression: CompileTimeConstant):
        self._current_block.consts[name] = expression

    def resolve_variable(self, name: str, operation: Literal["read", "write"]):
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
                    if is_upvalue:
                        index = self.get_upvalue_index(name)
                        if operation == "read":
                            self.add_opcode(LoadUpvalue(index))
                        elif operation == "write":
                            self.add_opcode(StoreUpvalue(index))
                    else:
                        local = self.get_local(name)
                        index = local.index
                        if operation == "read":
                            self.add_opcode(LoadLocal(index))
                        elif operation == "write":
                            if local.is_const:
                                raise CompilationError(f"cannot reassign constant '{name}'")
                            self.add_opcode(StoreLocal(index))
                    return
