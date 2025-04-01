from luark.compiler.ast.block import Block
from luark.compiler.ast.function_definitions import (
    FunctionBody,
    FunctionDefinition, ParameterList
)
from luark.compiler.ast.varargs import Varargs
from luark.compiler.compiler_state import CompilerState


class Chunk:
    def __init__(self, block: Block):
        self.block = block
        param_list = ParameterList([Varargs()])
        func_body = FunctionBody(param_list, self.block)
        self.func_def = FunctionDefinition(func_body, "<$main>")

    def compile(self, state: CompilerState):
        # We compile the chunk as a variadic function with the same body.
        self.func_def.evaluate(state)
