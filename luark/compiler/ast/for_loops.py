from dataclasses import dataclass

from lark.ast_utils import AsList
from lark.tree import Meta

from luark.compiler.ast import Block
from luark.compiler.ast.expressions import Expression, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import InternalCompilerError


# noinspection PyAbstractClass
class ForLoop(Statement, AsList):
    pass


@dataclass
class NumericForLoop(ForLoop):
    control_variable_name: str
    initial_expression: Expression
    limit_expression: Expression
    step_expression: Expression | None
    body: Block

    def __init__(self, meta: Meta, children: list):
        self.meta = meta
        self.control = children[0]
        self.initial = children[1]
        self.limit = children[2]

        self.step = None
        if len(children) == 4:
            self.body = children[3]
        elif len(children) == 5:
            self.step = children[3]
            self.body = children[4]
        else:
            raise InternalCompilerError(f"invalid children ({len(children)}) for numeric for loop")

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError


@dataclass
class GenericForLoop(ForLoop):
    name_list: list[str]
    expression_list: ExpressionList
    body: Block

    def __init__(self, meta: Meta, children: list):
        self.name_list = children[:-2]
        self.expression_list = children[-2]
        self.body = children[-1]

    def compile(self, state: CompilerState) -> None:
        raise NotImplementedError
