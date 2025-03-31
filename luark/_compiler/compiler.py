import sys
from os import PathLike
from pathlib import Path

from lark import Lark, ast_utils

import luark
import luark.compiler.ast.luark_ast
from luark.compiler.errors import InternalCompilerError
from luark.compiler.ast.base_transformer import LuarkTransformer
from luark.compiler.ast.chunk import Chunk
from luark.compiler.program import CompiledProgram


class Compiler:
    def __init__(self, debug: bool = False):
        self.debug = debug
        path = Path(luark.compiler.compiler.__file__).parent / "grammar.lark"
        with open(path) as file:
            self.grammar = file.read()
        self.lark = Lark(grammar=self.grammar, parser="lalr", cache=True, debug=self.debug, propagate_positions=True)
        self.transformer = ast_utils.create_transformer(
            sys.modules[luark.compiler.ast.luark_ast.__name__],
            LuarkTransformer(),
        )

    def compile_source(self, source: str) -> CompiledProgram:
        tree = self.lark.parse(source)
        if self.debug:
            print(tree.pretty())

        chunk: Chunk = self.transformer.transform(tree)
        if not isinstance(chunk, Chunk):
            raise InternalCompilerError("Attempted to compile something other than a chunk.")
        program: CompiledProgram = chunk.emit()
        if self.debug:
            print(program)

        return program

    def compile_file(self, path: str | PathLike) -> CompiledProgram:
        with open(path) as file:
            source = file.read()
        return self.compile_source(source)
