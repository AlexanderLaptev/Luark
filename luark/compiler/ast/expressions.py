from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from luark.compiler.compiler_state import CompilerState


class Expression(ABC):
    @abstractmethod
    def evaluate(self, state: CompilerState) -> None:
        pass


class MultiresExpression(Expression):
    @abstractmethod
    def evaluate(
            self,
            state: CompilerState,
            return_count: int | Literal["all"] = 1
    ) -> None:
        pass


class CompileTimeConstant(Expression):
    @abstractmethod
    def evaluate(self, state: CompilerState) -> None:
        pass


@dataclass
class ExpressionList:
    expressions: list[Expression] = field(default_factory=list)

    def evaluate(self, state: CompilerState, adjust_to: int = None) -> None:
        raise NotImplementedError
