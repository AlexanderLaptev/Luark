from lark import Lark


class LuaCompiler:
    def __init__(self):
        with open("grammar.lark") as f:
            grammar = f.read()
        self.lark = Lark(grammar, parser="earley")

    def compile(self, source: str):
        self.lark.parse(source)
