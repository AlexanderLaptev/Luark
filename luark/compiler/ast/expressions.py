from abc import ABC, abstractmethod
from dataclasses import dataclass

from lark.ast_utils import AsList

from luark.compiler.ast.ast_node import AstNode
from luark.compiler.compiler_state import CompilerState
from luark.opcode.binary import BinaryOperation
from luark.opcode.push import PushNil
from luark.opcode.unary import UnaryOperation


class Expression(ABC, AstNode):
    @abstractmethod
    def evaluate(self, state: CompilerState) -> None:
        pass


@dataclass
class Parentheses(Expression):
    inner: Expression

    def evaluate(self, state: CompilerState) -> None:
        self.inner.evaluate(state)


class MultiresExpression(Expression):
    @abstractmethod
    def evaluate(
            self,
            state: CompilerState,
            return_count: int = 2,
    ) -> None:
        pass


class CompileTimeConstant(Expression):
    @abstractmethod
    def evaluate(self, state: CompilerState) -> None:
        pass


# FIXME: fails on numbers (e.g. `local x = -5`)
@dataclass
class UnaryExpression(Expression):
    operand: Expression
    opcode: UnaryOperation

    def evaluate(self, state: CompilerState) -> None:
        self.operand.evaluate(state)
        state.add_opcode(self.opcode)


@dataclass
class BinaryExpression(Expression):
    left: Expression
    right: Expression
    opcode: BinaryOperation

    def evaluate(self, state: CompilerState) -> None:
        self.left.evaluate(state)
        self.right.evaluate(state)
        state.add_opcode(self.opcode)


@dataclass
class ExpressionList(AstNode, AsList):
    expressions: list[Expression]

    def evaluate(self, state: CompilerState, adjust_to: int | None = None) -> None:
        """
        Adjusts the expression list statically to the specified length. Static
        adjustments are performed by:
        1. Assignments.
        2. Local assignments.
        3. Generic for loops.
        4. Arguments of a function call.

        Other adjustments are done dynamically by the VM at runtime. If the last
        expression is multires, the adjustment must be performed dynamically.
        We still need to specify how many values we expect to receive in the end.
        """
        if not self.expressions:
            return

        last = self.expressions[-1]
        if adjust_to is None:
            if isinstance(last, MultiresExpression):
                last.evaluate(state, return_count=0)
            for expression in reversed(self.expressions[:-1]):
                expression.evaluate(state)
        else:
            assert adjust_to > 0
            if isinstance(last, MultiresExpression):
                difference = adjust_to - len(self.expressions)
                if difference >= 0:
                    difference = adjust_to - len(self.expressions) + 2
                    last.evaluate(state, return_count=difference)
                    for expression in reversed(self.expressions[:-1]):
                        expression.evaluate(state)
                else:
                    for expression in reversed(self.expressions[:adjust_to]):
                        expression.evaluate(state)
            else:
                nil_count = max(0, adjust_to - len(self.expressions))
                for _ in range(nil_count):
                    state.add_opcode(PushNil.INSTANCE)
                until = min(adjust_to, len(self.expressions))
                for expression in reversed(self.expressions[:until]):
                    expression.evaluate(state)

    @property
    def is_multires(self) -> bool:
        return self.expressions and isinstance(self.expressions[-1], MultiresExpression)
