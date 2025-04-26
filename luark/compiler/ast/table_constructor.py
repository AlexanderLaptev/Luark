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
            i = 0
            while i < len(self.fields):
                field = self.fields[i]
                if isinstance(field, ExpressionField):
                    field.value.evaluate(state)
                    state.add_opcode(LoadLocal(table_local))
                    field.key.evaluate(state)
                    state.add_opcode(SetTable.INSTANCE)
                    i += 1
                elif isinstance(field, NameField):
                    field.value.evaluate(state)
                    state.add_opcode(LoadLocal(table_local))
                    const_index = state.get_const_index(field.name)
                    state.add_opcode(PushConst(const_index))
                    state.add_opcode(SetTable.INSTANCE)
                    i += 1
                elif isinstance(field, MultiresExpression):
                    size = 0 if (i == last_index) else 1
                    if size == 0:
                        state.add_opcode(MarkStack.INSTANCE)
                    field.evaluate(state, size)
                    state.add_opcode(LoadLocal(table_local))
                    state.add_opcode(StoreList(size))
                    i += 1
                elif isinstance(field, Expression):
                    size = 1
                    field.evaluate(state)

                    peek = i + 1
                    while peek < len(self.fields):
                        peek_field = self.fields[peek]
                        if isinstance(peek_field, Expression):
                            peek_field.evaluate(state)
                            size += 1
                            peek += 1
                        else:
                            break

                    state.add_opcode(LoadLocal(table_local))
                    state.add_opcode(StoreList(size))
                    i += size
                else:
                    raise InternalCompilerError(f"illegal type of field: {type(field)}")

        state.add_opcode(LoadLocal(table_local))
        state.release_locals(table_local)
