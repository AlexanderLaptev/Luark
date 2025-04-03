from dataclasses import dataclass, field

from lark.ast_utils import AsList
from lark.tree import Meta

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState


@dataclass
class ElseIf:
    condition: Expression
    body: Block


@dataclass
class IfStatement(Statement, AsList):
    condition: Expression
    body: Block
    else_if_branches: list[ElseIf] = field(default_factory=list)
    else_branch: Block | None = None

    def __init__(self, meta: Meta, children: list):
        self.meta = meta
        self.condition = children[0]
        self.body = children[1]
        if isinstance(children[-1], Block):
            self.else_if_branches = children[2:-1]
            self.else_branch = children[-1]
        else:
            self.else_if_branches = children[2:]

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
