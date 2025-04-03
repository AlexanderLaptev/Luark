import os.path
import pkgutil
from os import PathLike
from typing import Literal

from lark import Lark, Token, Tree, UnexpectedInput, UnexpectedToken
from lark.exceptions import VisitError

from luark.compiler.ast.chunk import Chunk
from luark.compiler.ast.transformer import LuarkTransformer
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import CompilationError, InternalCompilerError
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

    def __init__(self, debug: Literal["tree", "code", "all", "none"] = "none"):
        self.debug_tree = False
        self.debug_code = False
        match debug:
            case "tree":
                self.debug_tree = True
            case "code":
                self.debug_code = True
            case "all":
                self.debug_tree = True
                self.debug_code = True
        if self._lark is None:
            self._init_lark()

    def compile_string(
            self,
            source: str,
            file_name: str = "<input>"
    ) -> Program:
        try:
            tree = self._lark.parse(source, start="start")
        except UnexpectedToken as e:
            raise CompilationError(f"{file_name}:{e.line}: unexpected token {e.token.type}")
        except UnexpectedInput as e:
            raise CompilationError(f"{file_name}:{e.line}: syntax error at column {e.column}")

        if self.debug_tree:
            print(tree.pretty())

        try:
            chunk: Chunk = self._transformer.transform(tree)
            state = CompilerState()
            program = chunk.compile(state)
            if self.debug_code:
                print(program)
            return program
        except (CompilationError, InternalCompilerError):
            raise
        except VisitError as e:
            if isinstance(e.orig_exc, CompilationError):
                line: str = "?"
                if isinstance(e.obj, Tree):
                    line = str(e.obj.meta.line)
                elif isinstance(e.obj, Token):
                    line = str(e.obj.line)

                raise CompilationError(f"{file_name}:{line}:", e.orig_exc)
            else:
                raise InternalCompilerError(e.orig_exc)
        except Exception as e:
            raise InternalCompilerError(e)

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
            debug=self.debug_tree,
        )
