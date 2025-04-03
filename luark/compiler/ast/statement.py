from abc import ABC, abstractmethod

from luark.compiler.ast.ast_node import AstNode
from luark.compiler.compiler_state import CompilerState


class Statement(ABC, AstNode):
    @abstractmethod
    def compile(self, state: CompilerState) -> None:
        pass
