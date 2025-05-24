from abc import abstractmethod
from dataclasses import dataclass

from luark.compiler.ast.constants import CompileTimeConstant
from luark.compiler.ast.expressions import Expression
from luark.compiler.compiler_state import CompilerState
from luark.opcode.local import LoadLocal, StoreLocal
from luark.opcode.push import PushConst
from luark.opcode.table import GetTable, SetTable


class Lvalue(Expression):
    """
    An assignment target.
    """

    @abstractmethod
    def evaluate(self, state: CompilerState, temporaries: list = None) -> None:
        pass

    @abstractmethod
    def assign(self, state: CompilerState, temporaries: list):
        pass


@dataclass
class Variable(Lvalue):
    """
    A named variable. Can refer to a local variable, a constant value, a local
    from an enclosing function (*upvalue*), or a global variable (a field of
    the `_ENV` table, which is always passed as an upvalue to the main chunk).
    """

    name: str

    def evaluate(self, state: CompilerState, temporaries: list[int] = None) -> None:
        if temporaries is not None:
            return
        state.resolve_variable(self.meta, self.name, "read")

    def assign(self, state: CompilerState, temporaries: list):
        state.resolve_variable(self.meta, self.name, "write")


@dataclass
class DotAccess(Lvalue):
    """
    An expression of the form `table.key`. Can be evaluated to produce a result
    or can be assigned to from an assignment statement.
    """

    expression: Expression
    name: str

    def evaluate(self, state: CompilerState, temporaries: list[int] = None):
        if temporaries is not None:
            index = state.add_temporaries(1)
            temporaries.append(index)
            self.expression.evaluate(state)
            state.add_opcode(StoreLocal(index))
            state.release_locals(index)
        else:
            self.expression.evaluate(state)
            index = state.get_const_index(self.name)
            state.add_opcode(PushConst(index))
            state.add_opcode(GetTable.INSTANCE)

    def assign(self, state: CompilerState, temporaries: list[int]):
        local_index = temporaries.pop()
        const_index = state.get_const_index(self.name)
        state.add_opcode(LoadLocal(local_index))
        state.add_opcode(PushConst(const_index))
        state.add_opcode(SetTable.INSTANCE)


@dataclass
class TableAccess(Lvalue):
    """
    An expression of the form `table[expression]`. Can be evaluated to produce
    a result or can be assigned to from an assignment statement.
    """

    table: Expression
    key: Expression

    def evaluate(self, state: CompilerState, temporaries: list[int] = None) -> None:
        if temporaries is not None:
            table_index = state.add_temporaries(1)
            self.table.evaluate(state)
            state.add_opcode(StoreLocal(table_index))
            temporaries.append(table_index)

            if not isinstance(self.key, CompileTimeConstant):
                key_index = state.add_temporaries(1)
                self.key.evaluate(state)
                state.add_opcode(StoreLocal(key_index))
                temporaries.append(key_index)
                state.release_locals(key_index, 1)

            state.release_locals(table_index)
        else:
            self.table.evaluate(state)
            self.key.evaluate(state)
            state.add_opcode(GetTable.INSTANCE)

    def assign(self, state: CompilerState, temporaries: list):
        if isinstance(self.key, CompileTimeConstant):
            self.key.evaluate(state)
        else:
            key_index = temporaries.pop()
            state.add_opcode(LoadLocal(key_index))

        table_index = temporaries.pop()
        state.add_opcode(LoadLocal(table_index))
        state.add_opcode(SetTable.INSTANCE)
