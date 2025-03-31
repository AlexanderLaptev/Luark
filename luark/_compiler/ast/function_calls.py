from lark.ast_utils import Ast

from luark.compiler.ast.expressions import Expression, MultiresExpression
from luark.compiler.ast.expr_list_utils import evaluate_single
from luark.compiler.ast.program_state import _ProgramState


class FuncCallParams(Ast):
    exprs: list[Expression]

    def __init__(self, child):
        if not child:
            self.exprs = []
        else:
            if isinstance(child, list):
                self.exprs = child
            else:
                self.exprs = [child]


class FuncCall(Ast, MultiresExpression):
    primary: Expression
    params: FuncCallParams

    def __init__(self, primary: Expression, params: FuncCallParams):
        self.primary = primary
        self.params = params

    def evaluate(self, state: _ProgramState, return_count: int = 1):
        proto = state.proto
        param_count = self._eval_params(state)
        evaluate_single(state, self.primary)
        proto.add_opcode(f"call {param_count} {return_count}")

    def _eval_params(self, state):
        exprs = self.params.exprs
        param_count: int = 1 + len(exprs)
        if exprs:
            for i in range(len(exprs) - 1):
                expr = exprs[i]
                evaluate_single(state, expr)

            last = exprs[-1]
            if isinstance(last, MultiresExpression):
                last.evaluate(state, 0)
                param_count = 0
            else:
                evaluate_single(state, last)
        return param_count


class MethodCall(FuncCall):
    def __init__(self, primary: Expression, name: str, params: FuncCallParams):
        super().__init__(primary, params)
        self.name = name

    def evaluate(self, state: _ProgramState, return_count: int = 1):
        proto = state.proto

        evaluate_single(state, self.primary)
        self_index = proto.new_temporary()
        proto.add_opcode(f"store_local {self_index}")

        proto.add_opcode(f"load_local {self_index}")
        param_count = self._eval_params(state)
        evaluate_single(state, self.primary)
        proto.add_opcode(f"call {param_count} {return_count}")

        proto.release_local(self_index)
