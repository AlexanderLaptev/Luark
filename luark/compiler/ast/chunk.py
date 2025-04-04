from lark.tree import Meta

from luark.compiler.ast.ast_node import AstNode
from luark.compiler.ast.block import Block
from luark.compiler.ast.function_definitions import (
    FunctionBody,
    FunctionDefinition, ParameterList
)
from luark.compiler.compiler_state import CompilerState


class Chunk(AstNode):
    def __init__(self, meta: Meta, block: Block):
        self.meta = meta
        self.block = block
        param_list = ParameterList([], True)
        func_body = FunctionBody(meta, param_list, self.block)
        self.func_def = FunctionDefinition(meta, func_body, "<$main>")

    def compile(self, state: CompilerState):
        # We compile the chunk as a variadic function with the same body.
        self.func_def.evaluate(state, create_closure=False)
        return state.compile()
