from dataclasses import dataclass

from lark.ast_utils import Ast, WithMeta
from lark.tree import Meta


@dataclass
class AstNode(Ast, WithMeta):
    meta: Meta
