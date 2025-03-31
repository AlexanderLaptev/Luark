from dataclasses import dataclass

from lark.ast_utils import Ast

from luark.compiler import CompiledProgram
from luark.compiler.ast.block import Block
from luark.compiler.ast.expressions import Varargs
from luark.compiler.ast.function_definitions import FuncBody, ParamList, FuncDef
from luark.compiler.ast.program_state import _ProgramState


@dataclass
class Chunk(Ast):
    block: Block

    def emit(self) -> CompiledProgram:
        program_state = _ProgramState()
        func_name = "$main"
        func_body = FuncBody(ParamList([Varargs()]), self.block)
        func_def = FuncDef(func_body, func_name)
        func_def.evaluate(program_state)
        program_state.get_proto(0).get_upvalue_index("_ENV")
        return program_state.compile()
