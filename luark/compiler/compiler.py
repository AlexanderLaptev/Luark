import pkgutil
from os import PathLike

from lark import Lark, UnexpectedInput

from luark.compiler.ast.chunk import Chunk
from luark.compiler.ast.transformer import LuarkTransformer
from luark.compiler.compiler_state import CompilerState
from luark.program import Program


class Compiler:
    _GRAMMAR_FILE_NAME = "grammar.lark"
    _LARK_PARAMS = {
        "parser": "lalr",
        "cache": True,
        "propagate_positions": True,
    }

    _lark: Lark = None
    _transformer: LuarkTransformer

    def __init__(self, debug: bool = False):
        self.debug = debug
        if self._lark is None:
            self._init_lark()

    def compile_string(self, source: str) -> Program:
        tree = self._lark.parse(
            source,
            start="start",
            on_error=self._on_error
        )
        if self.debug:
            print(tree.pretty())

        chunk: Chunk = self._transformer.transform(tree)
        state = CompilerState()
        program = chunk.compile(state)
        return program

    def compile_file(self, file_path: int | str | bytes | PathLike[str] | PathLike[bytes]) -> Program:
        source: str
        with open(file_path, "r") as source_file:
            source = source_file.read()
        return self.compile_string(source)

    def _on_error(self, error: UnexpectedInput) -> bool | None:
        pass

    def _init_lark(self) -> None:
        grammar = pkgutil.get_data(
            "luark.compiler",
            Compiler._GRAMMAR_FILE_NAME,
        ).decode("utf-8")

        self._transformer = LuarkTransformer()
        self._lark = Lark(
            grammar,
            **Compiler._LARK_PARAMS,
            debug=self.debug,
        )
