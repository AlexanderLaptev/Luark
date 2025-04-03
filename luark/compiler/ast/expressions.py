import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal

from luark.compiler.ast.ast_node import AstNode
from luark.compiler.compiler_state import CompilerState
from luark.opcode import Opcode


class Expression(ABC, AstNode):
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
class UnaryExpression(Expression):
    operand: Expression
    opcode: Opcode

    def evaluate(self, state: CompilerState) -> None:
        self.operand.evaluate(state)
        state.add_opcode(self.opcode)


@dataclass
class BinaryExpression(Expression):
    left: Expression
    right: Expression
    opcode: Opcode

    def evaluate(self, state: CompilerState) -> None:
        self.left.evaluate(state)
        self.right.evaluate(state)
        state.add_opcode(self.opcode)


@dataclass
class ExpressionList:
    expressions: list[Expression] = field(default_factory=list)

    def evaluate(self, state: CompilerState, adjust_to: int = None) -> None:
        if adjust_to:  # TODO
            warnings.warn("expression list adjustments are not yet supported")

        for expression in self.expressions:
            expression.evaluate(state)
