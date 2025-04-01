from dataclasses import dataclass

from luark.compiler.ast.block import Block
from luark.compiler.ast.function_definitions import (
    FunctionBody,
    FunctionDefinition, ParameterList
)
from luark.compiler.compiler_state import CompilerState


@dataclass
class Chunk:
    block: Block

    def compile(self, state: CompilerState):
        state.begin_chunk()

        param_list = ParameterList.of_varargs()
        func_body = FunctionBody(param_list, self.block)
        func_def = FunctionDefinition(func_body, "$main")
        func_def.evaluate(state)

        state.end_chunk()
