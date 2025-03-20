import sys
from os import PathLike
from pathlib import Path

from lark import Lark, ast_utils

import luark
import luark.compiler.luark_ast
from luark.compiler.errors import InternalCompilerError
from luark.compiler.luark_ast import LuarkTransformer, Chunk
from luark.compiler.program import Program


class Compiler:
    def __init__(self, debug: bool = False):
        self.debug = debug
        path = Path(luark.compiler.compiler.__file__).parent / "grammar.lark"
        with open(path) as file:
            self.grammar = file.read()
        self.lark = Lark(grammar=self.grammar, parser="lalr", debug=self.debug)
        self.transformer = ast_utils.create_transformer(
            sys.modules[luark.compiler.luark_ast.__name__],
            LuarkTransformer(),
        )

    def compile_source(self, source: str) -> Program:
        tree = self.lark.parse(source)
        if self.debug:
            print(tree.pretty())

        chunk: Chunk = self.transformer.transform(tree)
        if not isinstance(chunk, Chunk):
            raise InternalCompilerError("Attempted to compile something other than a chunk.")
        program: Program = chunk.emit()

        return program

    def compile_file(self, path: str | PathLike) -> Program:
        with open(path) as file:
            source = file.read()
        return self.compile_source(source)
