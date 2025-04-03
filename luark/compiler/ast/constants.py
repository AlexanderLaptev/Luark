from typing import Self

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.opcode.push import PushFalse


class TrueValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


# noinspection PyTypeChecker
TrueValue.INSTANCE = TrueValue(None)


class FalseValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        state.add_opcode(PushFalse())


# noinspection PyTypeChecker
FalseValue.INSTANCE = FalseValue(None)


class NilValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


# noinspection PyTypeChecker
NilValue.INSTANCE = NilValue(None)
