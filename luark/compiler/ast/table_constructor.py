from dataclasses import dataclass

from lark.ast_utils import AsList

from luark.compiler.ast import AstNode, MultiresExpression
from luark.compiler.ast.expressions import Expression
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import InternalCompilerError
from luark.opcode.local import LoadLocal, StoreLocal
from luark.opcode.push import PushConst
from luark.opcode.table import CreateTable, SetTable, StoreList
from luark.opcode.varargs import MarkStack


@dataclass
class ExpressionField(AstNode):
    key: Expression
    value: Expression


@dataclass
class NameField(AstNode):
    name: str
    value: Expression


@dataclass
class TableConstructor(Expression, AsList):
    fields: list[ExpressionField | NameField | Expression] | None = None

    def evaluate(self, state: CompilerState) -> None:
        state.add_opcode(CreateTable.INSTANCE)
        table_local = state.add_temporaries(1)
        state.add_opcode(StoreLocal(table_local))

        if self.fields:
            last_index = len(self.fields) - 1
            for i, field in enumerate(self.fields):
                if isinstance(field, ExpressionField):
                    field.value.evaluate(state)
                    state.add_opcode(LoadLocal(table_local))
                    field.key.evaluate(state)
                    state.add_opcode(SetTable.INSTANCE)
                elif isinstance(field, NameField):
                    field.value.evaluate(state)
                    state.add_opcode(LoadLocal(table_local))
                    const_index = state.get_const_index(field.name)
                    state.add_opcode(PushConst(const_index))
                    state.add_opcode(SetTable.INSTANCE)
                elif isinstance(field, MultiresExpression):
                    size = 0 if (i == last_index) else 1
                    if size == 0:
                        state.add_opcode(MarkStack.INSTANCE)
                    field.evaluate(state, size)
                    state.add_opcode(LoadLocal(table_local))
                    state.add_opcode(StoreList(size))
                elif isinstance(field, Expression):
                    field.evaluate(state)
                    state.add_opcode(LoadLocal(table_local))
                    state.add_opcode(StoreList(1))
                else:
                    raise InternalCompilerError(f"illegal type of field: {type(field)}")

        state.release_locals(table_local)
