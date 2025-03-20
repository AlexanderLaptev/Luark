from dataclasses import dataclass

from lark.ast_utils import Ast, AsList
from lark.visitors import Transformer

from luark.compiler.program import Program


class Statement(Ast):
    def emit(self, program: Program):
        pass


@dataclass
class Block(Ast, AsList):
    statements: list

    def emit(self, program: Program):
        for statement in self.statements:
            statement.emit(program)


@dataclass
class Chunk(Ast):
    block: Block

    def emit(self):
        program = Program()
        return program


# noinspection PyPep8Naming
class LuarkTransformer(Transformer):
    def start(self, children):
        return children[-1]
