from typing import Self

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.opcode.push import PushFalse, PushNil, PushTrue


class TrueValue(CompileTimeConstant):
    INSTANCE: Self = None

    def evaluate(self, state: CompilerState) -> None:
        state.add_opcode(PushTrue.INSTANCE)


# noinspection PyTypeChecker
TrueValue.INSTANCE = TrueValue(None)


class FalseValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        state.add_opcode(PushFalse.INSTANCE)


# noinspection PyTypeChecker
FalseValue.INSTANCE = FalseValue(None)


class NilValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        state.add_opcode(PushNil.INSTANCE)


# noinspection PyTypeChecker
NilValue.INSTANCE = NilValue(None)
