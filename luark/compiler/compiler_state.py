from dataclasses import dataclass
from enum import Enum, auto
from typing import TypeAlias

from luark.compiler.exceptions import InternalCompilerError

ConstType: TypeAlias = int | float | bytes


@dataclass
class _LocalVariable:
    class Type(Enum):
        REGULAR = auto()
        RUNTIME_CONST = auto()
        COMPILE_CONST = auto()
        TO_BE_CLOSED = auto()

    name: str
    type: Type


class _BlockState:
    def __init__(self):
        self.locals: list[_LocalVariable] = []


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


class CompilerState:
    from luark.opcode import Opcode

    def __init__(self):
        self._consts: dict[ConstType, int] = {}

        self._protos: list[_PrototypeState] = []
        self._stack: list[_PrototypeState] = []
        self._current_proto: _PrototypeState | None = None

        self._num_lambdas = 0

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

    def begin_block(self) -> None:
        block_state = _BlockState()
        self._current_proto.block_stack.append(block_state)

    def end_block(self) -> None:
        self._current_proto.block_stack.pop()

    def next_lambda_index(self) -> int:
        result = self._num_lambdas
        self._num_lambdas += 1
        return result

    def add_opcode(self, opcode: Opcode) -> None:
        raise NotImplementedError

    def get_const_index(self, value: ConstType) -> int:
        if value in self._consts:
            return self._consts[value]
        else:
            index = len(self._consts)
            self._consts[value] = index
            return index

    def get_const(self, index: int) -> ConstType:
        for k, v in self._consts.items():
            if v == index:
                return k
        raise InternalCompilerError(f"unable to find constant {index}")
