from dataclasses import dataclass

from lark.ast_utils import Ast, AsList
from lark.visitors import Transformer

from luark.compiler.program import Program, Prototype


class _State:
    def __init__(self, program: Program):
        self.program = program
        self.proto = program.main_proto


class Statement:
    def emit(self, state: _State):
        pass


@dataclass
class Block(Ast, AsList):
    statements: list

    def emit(self, state: _State):
        for statement in self.statements:
            statement.emit(state)


@dataclass
class Chunk(Ast):
    block: Block

    def emit(self):
        main_proto = Prototype()
        program = Program(main_proto)
        state = _State(program)
        self.block.emit(state)
        pass


# noinspection PyPep8Naming
class LuarkTransformer(Transformer):
    def start(self, children):
        return children[-1]
