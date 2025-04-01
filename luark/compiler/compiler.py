import os.path
import pkgutil
import sys
from os import PathLike

from lark import Lark, UnexpectedInput

from luark.compiler.ast.chunk import Chunk
from luark.compiler.ast.transformer import LuarkTransformer
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import CompilationError
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

    def compile_string(
            self,
            source: str,
            file_name: str = "<input>"
    ) -> Program:
        try:
            tree = self._lark.parse(
                source,
                start="start",
            )
        except UnexpectedInput as e:  # TODO: enhance error handling
            self._log_error(e, source, file_name)
            raise CompilationError(e)

        if self.debug:
            print(tree.pretty())

        chunk: Chunk = self._transformer.transform(tree)
        state = CompilerState()
        program = chunk.compile(state)
        return program

    def compile_file(
            self,
            file_path: int | str | bytes | PathLike[str] | PathLike[bytes]
    ) -> Program:
        source: str
        with open(file_path, "r") as source_file:
            source = source_file.read()
        return self.compile_string(source, os.path.basename(file_path))

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

    def _log_error(
            self,
            error: UnexpectedInput,
            source: str,
            file_name: str
    ) -> None:
        index = error.column - 1
        context = source[index:index + 5].strip() + "..."
        print(
            f"{file_name}:{error.line}: syntax error at column {error.column} near '{context}'",
            file=sys.stderr
        )
