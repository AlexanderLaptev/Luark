from dataclasses import dataclass
from typing import TypeAlias

from lark.ast_utils import Ast, AsList

from luark.compiler.ast.expressions import Expression, MultiresExpression
from luark.compiler.ast.expr_list_utils import evaluate_single
from luark.compiler.ast.program_state import _ProgramState


@dataclass
class ExprField(Ast):
    key: Expression
    value: Expression


@dataclass
class NameField(Ast):
    name: str
    value: Expression


Field: TypeAlias = Expression | ExprField | NameField


@dataclass
class TableConstructor(Ast, AsList, Expression):
    fields: list[Field] | None

    def evaluate(self, state: _ProgramState):
        proto = state.proto
        proto.add_opcode("create_table")
        table_local = proto.new_temporary()
        proto.add_opcode(f"store_local {table_local}")

        if self.fields:
            for i, field in enumerate(self.fields):
                if isinstance(field, ExprField):
                    evaluate_single(state, field.value)
                    proto.add_opcode(f"load_local {table_local}")
                    evaluate_single(state, field.key)
                    proto.add_opcode("set_table")
                elif isinstance(field, NameField):
                    evaluate_single(state, field.value)
                    proto.add_opcode(f"load_local {table_local}")
                    const_index = proto.get_const_index(field.name)
                    proto.add_opcode(f"push_const {const_index}")
                elif isinstance(field, MultiresExpression):
                    size = 0 if i == len(self.fields) - 1 else 2
                    field.evaluate(state, size)
                    proto.add_opcode(f"load_local {table_local}")
                    if size > 0:
                        proto.add_opcode("store_list 1")
                    else:
                        proto.add_opcode("store_list 0")
                elif isinstance(field, Expression):
                    evaluate_single(state, field)
                    proto.add_opcode(f"load_local {table_local}")
                    proto.add_opcode("store_list 1")
