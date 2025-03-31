from luark.compiler import LocalVarIndex
from luark.compiler.ast.expressions import Expression


class BlockState:
    current_locals: LocalVarIndex
    labels: dict[str, int]
    const_locals: dict[str, "Expression"]
    gotos: dict

    def __init__(self):
        self.current_locals = LocalVarIndex()
        self.labels = {}
        self.const_locals = {}  # compile time constants referenced by names from code
        self.gotos = {}
