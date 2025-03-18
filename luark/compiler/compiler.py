import sys
from os import PathLike
from pathlib import Path

from lark import Lark, ast_utils, Tree

import luark
from luark.compiler import syntax_tree
from luark.compiler.program import CompiledProgram


class InternalCompilerError(RuntimeError):
    pass


class Compiler:
    def __init__(self, debug: bool = False):
        with open(Path(luark.__file__).parent / "compiler/grammar.lark") as f:
            grammar = f.read()
        self._lark = Lark(grammar, parser="lalr")
        module = sys.modules[syntax_tree.__name__]
        self._transformer = ast_utils.create_transformer(module, syntax_tree.ToAst())
        self.debug = debug

    def compile_source(self, source: str):
        tree: Tree = self._lark.parse(source)
        if self.debug:
            print(tree.pretty())

        tree = self._transformer.transform(tree)
        chunk = tree.children[-1]
        if not isinstance(chunk, syntax_tree.Chunk):
            raise InternalCompilerError("Trying to compile something other than a chunk.")
        result = CompiledProgram()
        chunk.evaluate(result)

        if self.debug:
            print(result)
        return result

    def compile_file(self, path: str | PathLike[str]):
        with open(path) as f:
            src = f.read()
        self.compile_source(src)
