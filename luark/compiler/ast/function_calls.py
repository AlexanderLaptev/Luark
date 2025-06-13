from dataclasses import dataclass
from typing import TypeAlias

from luark.compiler.ast import MultiresExpression
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.string import String
from luark.compiler.ast.table_constructor import TableConstructor
from luark.compiler.compiler_state import CompilerState
from luark.opcode.call import Call
from luark.opcode.local import LoadLocal, StoreLocal
from luark.opcode.varargs import BeginArgs

CallParameters: TypeAlias = ExpressionList | TableConstructor | String | None


@dataclass
class FunctionCall(MultiresExpression):
    primary: Expression
    method_name: str | None
    parameters: CallParameters

    def evaluate(self, state: CompilerState, return_count: int = 2) -> None:
        self_index: int | None
        param_count = 0

        self_index = state.add_temporaries(1)
        self.primary.evaluate(state)
        state.add_opcode(StoreLocal(self_index))

        state.add_opcode(BeginArgs.INSTANCE)
        if self.method_name is not None:
            state.add_opcode(LoadLocal(self_index))
            param_count += 1

        if (isinstance(self.parameters, TableConstructor)
                or isinstance(self.parameters, String)):
            self.parameters.evaluate(state)
            param_count += 1
        else:
            params = self.parameters
            if params is None:
                params = ExpressionList(self.meta, [])

            params.evaluate(state, adjust_to=None)
            # if params.is_multires:
            #     param_count = 0
            # else:
            param_count += params.singleres_count

        state.add_opcode(LoadLocal(self_index))
        state.add_opcode(Call(param_count, return_count))

        if self_index is not None:
            state.release_locals(self_index)


@dataclass
class FunctionCallStatement(Statement):
    function_call: FunctionCall

    def compile(self, state: CompilerState) -> None:
        self.function_call.evaluate(state, 1)
