from typing import Self

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.opcode.push import PushFalse


class TrueValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


TrueValue.INSTANCE = TrueValue()


class FalseValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        state.add_opcode(PushFalse())


FalseValue.INSTANCE = FalseValue()


class NilValue(CompileTimeConstant):
    INSTANCE: Self

    def evaluate(self, state: CompilerState) -> None:
        raise NotImplementedError


NilValue.INSTANCE = NilValue()
