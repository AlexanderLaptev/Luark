from abc import ABC, abstractmethod
from dataclasses import dataclass

from lark.ast_utils import AsList

from luark.compiler.ast.ast_node import AstNode
from luark.compiler.compiler_state import CompilerState
from luark.opcode.binary import BinaryOperation
from luark.opcode.pop import Pop
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

    def evaluate(self, state: CompilerState, adjust_to_count: int = None) -> None:
        if adjust_to_count:
            self._adjust(state, adjust_to_count)
            return

        for expression in reversed(self.expressions):
            expression.evaluate(state)

    def _adjust(self, state: CompilerState, count: int) -> None:
        """
        Adjusts the expression list statically to the specified length.
        Static adjustments are performed by:
        1. Assignments.
        2. Local assignments.
        3. Generic for loops.

        Other adjustments are done dynamically by the VM at runtime.
        If the last expression is multires, the
        adjustment must be performed dynamically.
        We still need to specify how many values
        we expect to receive in the end.
        """

        assert count != 0, "cannot statically adjust to 0 values"

        difference = count - len(self.expressions)
        if difference > 0:  # append nils
            if self.expressions:
                if isinstance(self.expressions[-1], MultiresExpression):
                    # noinspection PyTypeChecker
                    expr: MultiresExpression = self.expressions[-1]
                    expr.evaluate(state, 2 + difference)
                else:
                    for _ in range(difference):
                        state.add_opcode(PushNil.INSTANCE)
                    self.expressions[-1].evaluate(state)
            else:
                for _ in range(difference):
                    state.add_opcode(PushNil.INSTANCE)

            for expr in reversed(self.expressions[:-1]):
                expr.evaluate(state)
        else:
            # Even if there are more values then expected,
            # we still have to evaluate them all and simply
            # discard them later.
            last: Expression = self.expressions[-1]
            if isinstance(last, MultiresExpression):
                # Tell the VM to discard all values if
                # we're already beyond the list of names.
                return_count = 2 if (difference == 0) else 1
                last.evaluate(state, return_count)
            else:
                last.evaluate(state)

            for expr in reversed(self.expressions[:-1]):
                expr.evaluate(state)

            for _ in range(-difference):  # diff is <= 0 here, so negate it
                state.add_opcode(Pop.INSTANCE)  # discard extra values
