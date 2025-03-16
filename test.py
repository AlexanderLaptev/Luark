import time

from lark import Lark

# with open("grammar.lark") as f1, open("grammar_test.lua") as f2:
with open("grammar.lark") as f1, open("test.lua") as f2:
    s_grammar = f1.read()
    s_input = f2.read()


lark = Lark(s_grammar, parser="lalr")
start = time.time()
tree = lark.parse(s_input)
end = time.time()
print(tree.pretty())
print(f'Done in {round(end - start, 3)} seconds.')
