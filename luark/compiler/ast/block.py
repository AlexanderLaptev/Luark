from dataclasses import dataclass, field

from luark.compiler.ast.statement import Statement


@dataclass
class Block:
    """
    A block is a collection of statements. The last statement may be a return statement.
    """
    statements: list[Statement] = field(default_factory=list)
