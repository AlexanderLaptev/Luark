from lark import Transformer, v_args

from luark.compiler.ast import Block, Chunk, EmptyStatement


@v_args(inline=True)
class LuarkTransformer(Transformer):
    def start(self, chunk):
        return chunk

    def chunk(self, block):
        return Chunk(block)

    @v_args(inline=False)
    def block(self, statements):
        return Block(statements)

    @v_args(meta=True)
    def empty_statement(self, meta, children):
        return EmptyStatement(meta)
