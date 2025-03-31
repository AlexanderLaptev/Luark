from luark.compiler.ast.expressions import Expression, MultiresExpression, Varargs
from luark.compiler.ast.function_calls import FuncCall
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.errors import InternalCompilerError


def evaluate_single(state: _ProgramState, expr: Expression | MultiresExpression):
    if isinstance(expr, FuncCall):  # function/method calls
        expr.evaluate(state, 2)
    elif isinstance(expr, Varargs):
        expr.evaluate(state, 1)
    elif isinstance(expr, Expression):  # standard singleres expression
        expr.evaluate(state)
    else:
        raise InternalCompilerError("Expected expression, got something else.")


def adjust_static(
        state: _ProgramState,
        count: int,
        expr_list: list[Expression | MultiresExpression],
):
    """
    Used in:
    1. Assignments.
    2. Local assignments.
    3. Generic for loops.

    Other adjustments are done dynamically by the VM at runtime.
    If the last expression is multires, the
    adjustment must be performed dynamically.
    We still need to specify how many values
    we expect to receive in the end.
    """

    if count == 0:
        raise InternalCompilerError("Attempted to statically adjust to count of 0")

    difference = count - len(expr_list)
    if difference > 0:  # append nils
        if expr_list:
            if isinstance(expr_list[-1], MultiresExpression):
                expr: MultiresExpression = expr_list[-1]
                expr.evaluate(state, 2 + difference)
            else:
                for _ in range(difference):
                    state.proto.add_opcode("push_nil")
                evaluate_single(state, expr_list[-1])
        else:
            for _ in range(difference):
                state.proto.add_opcode("push_nil")

        for i in range(len(expr_list) - 1):
            expr = expr_list[i]
            evaluate_single(state, expr)
    else:
        # Even if there are more values then expected,
        # we still have to evaluate them all and simply
        # discard them later.

        for i in range(len(expr_list) - 1):
            expr = expr_list[i]
            evaluate_single(state, expr)

        last = expr_list[-1]
        if isinstance(last, MultiresExpression):
            # Tell the VM to discard all values if
            # we're already beyond the list of names.
            return_count = 2 if (difference == 0) else 1
            last.evaluate(state, return_count)
        else:
            evaluate_single(state, last)

        for _ in range(-difference):  # diff is < 0 here, so negate it
            state.proto.add_opcode("pop")  # discard extra values
