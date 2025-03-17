import sys
from os import PathLike

from lark import Lark, ast_utils, Tree

import luark_ast


class LuaCompiler:
    def __init__(self, debug: bool = False):
        with open("grammar.lark") as f:
            grammar = f.read()
        self._lark = Lark(grammar, parser="lalr")
        module = sys.modules[luark_ast.__name__]
        self._transformer = ast_utils.create_transformer(module, luark_ast.ToAst())
        self.debug = debug

    def compile_source(self, source: str):
        tree: Tree = self._lark.parse(source)
        tree = self._transformer.transform(tree)
        if self.debug:
            print(tree.pretty())
        tree.children[0].evaluate()

    def compile_file(self, path: str | PathLike[str]):
        with open(path) as f:
            src = f.read()
        self.compile_source(src)
