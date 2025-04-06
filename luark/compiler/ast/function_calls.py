from dataclasses import dataclass

from luark.compiler.ast import AstNode, MultiresExpression
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.string import String
from luark.compiler.ast.table_constructor import TableConstructor
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import InternalCompilerError
from luark.opcode.call import Call
from luark.opcode.local import LoadLocal, StoreLocal
from luark.opcode.push import PushConst
from luark.opcode.table import GetTable
from luark.opcode.varargs import MarkStack


@dataclass
class FunctionCallParameters(AstNode):
    parameters: ExpressionList | TableConstructor | String | None = None


@dataclass
class FunctionCall(MultiresExpression):
    primary: Expression
    parameters: FunctionCallParameters
    is_method: bool = False

    def evaluate(self, state: CompilerState, return_count: int = 2) -> None:
        self.primary.evaluate(state)
        self._evaluate(state, return_count)

    def _evaluate(self, state: CompilerState, return_count: int) -> None:
        self_index: int | None = None
        if self.is_method:
            self_index = state.add_temporaries(1)
            self.primary.evaluate(state)
            state.add_opcode(StoreLocal(self_index))

        params = self.parameters.parameters
        expressions = []
        if params:
            if isinstance(params, TableConstructor | String):
                expressions.append(params)
            elif isinstance(params, ExpressionList):
                expressions = params.expressions.copy()
            else:
                raise InternalCompilerError(f"illegal func params type: {type(params)}")

        if not expressions:
            param_count = 1
            if self.is_method:
                state.add_opcode(LoadLocal(self_index))
                param_count = 2
            state.add_opcode(Call(param_count, return_count))
            return

        state.add_opcode(MarkStack.INSTANCE)
        if self.is_method:
            state.add_opcode(LoadLocal(self_index))
            state.release_locals(self_index)
        for expr in expressions[:-1]:
            expr.evaluate(state)

        last = expressions[-1]
        param_count: int
        if isinstance(last, MultiresExpression):
            last.evaluate(state, 0)
            param_count = 0  # unknown count
        else:
            last.evaluate(state)
            param_count = 1 + len(expressions)
            if self.is_method:
                param_count += 1
        state.add_opcode(Call(param_count, return_count))


class MethodCall(FunctionCall):
    method_name: str

    def __init__(
            self,
            primary: Expression,
            method_name: str,
            parameters: FunctionCallParameters
    ):
        super().__init__(primary, parameters, True)
        self.method_name = method_name

    def evaluate(self, state: CompilerState, return_count: int = 1) -> None:
        self.primary.evaluate(state)
        const_index = state.get_const_index(self.method_name)
        state.add_opcode(PushConst(const_index))
        state.add_opcode(GetTable.INSTANCE)
        super()._evaluate(state, return_count)


@dataclass
class FunctionCallStatement(Statement):
    function_call: FunctionCall

    def compile(self, state: CompilerState) -> None:
        self.function_call.evaluate(state, 1)
