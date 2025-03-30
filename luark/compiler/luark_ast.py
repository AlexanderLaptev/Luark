import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

from lark.ast_utils import Ast, AsList
from lark.visitors import Transformer, Discard

from luark.compiler.errors import InternalCompilerError, CompilationError
from luark.compiler.program import Program, Prototype, LocalVar, LocalVarIndex


# TODO: refactor type hints
# TODO: refactor multires expressions
# TODO: code cleanup
# TODO: add upvalue metadata
# TODO: use evaluate_single() everywhere


class _BlockState:
    current_locals: LocalVarIndex

    def __init__(self):
        self.current_locals = LocalVarIndex()
        self.breaks: list[int] = []
        self.labels: dict[str, int] = {}
        self.gotos = {}
        self.tbc_locals: list[int] = []


ConstType = int | float | str


class _ProtoState:
    locals: LocalVarIndex
    locals_pool: list[int]
    linear_mode: bool

    func_name: str
    fixed_params: int
    is_variadic: bool

    _pc: int

    num_upvalues: int
    num_consts: int
    num_locals: int

    block_stack: list[_BlockState]
    upvalues: dict[str, int]
    consts: dict[ConstType, int]
    opcodes: list[str]

    def __init__(self, func_name: str = None):
        self.locals = LocalVarIndex()
        self.locals_pool = []
        self.linear_mode = False

        self.func_name = func_name
        self.fixed_params = 0
        self.is_variadic = False

        self._pc = 0

        self.num_upvalues = 0
        self.num_consts = 0
        self.num_locals = 0

        self.block_stack = []
        self.upvalues = {}
        self.consts = {}
        self.opcodes = []

    @property
    def block(self) -> _BlockState:
        return self.block_stack[-1]

    @property
    def pc(self):
        return self._pc

    def get_upvalue_index(self, name: str) -> int:
        if name in self.upvalues:
            return self.upvalues[name]
        index = self.num_upvalues
        self.num_upvalues += 1
        self.upvalues[name] = index
        return index

    def get_const_index(self, value: ConstType) -> int:
        if value in self.consts:
            return self.consts[value]
        index = self.num_consts
        self.num_consts += 1
        self.consts[value] = index
        return index

    def _next_local_index(self) -> int:
        if self.linear_mode or not self.locals_pool:
            index = self.num_locals
            self.num_locals += 1
            return index
        else:
            return self.locals_pool.pop()

    def new_local(self, name: str) -> int:
        index = self._next_local_index()
        self.block.current_locals.add(LocalVar(name, index, self._pc))
        return index

    def get_local_index(self, name: str) -> int:
        if self.block.current_locals.has_name(name):
            var = self.block.current_locals.get_by_name(name)[-1]
            return var.index
        else:
            return self.new_local(name)

    def new_temporary(self) -> int:
        var = LocalVar(None, self._next_local_index(), self._pc)
        self.block.current_locals.add(var)
        return var.index

    def release_local(self, index: int):
        self.locals_pool.append(index)

    def add_label(self, name: str):
        if name not in self.block.labels:
            self.block.labels[name] = self.pc
        else:
            raise CompilationError(f"Label '{name}' is already defined.")

    def get_label_target(self, name: str):
        if name in self.block.labels:
            return self.block.labels[name]
        else:
            raise CompilationError(f"Label '{name}' is not defined.")

    def add_opcode(self, opcode):
        self.opcodes.append(opcode)
        self._pc += 1

    def reserve_opcodes(self, count: int) -> int:
        pc = self._pc
        for _ in range(count):
            # noinspection PyTypeChecker
            self.opcodes.append(None)
            self._pc += 1
        return pc

    def add_jump(self, to: int, from_: int = None):
        if not from_:
            from_ = self._pc
        self.add_opcode(f"jump {to - from_}")

    def set_jump(self, jump_pc: int, target: int = None):
        if not target:
            target = self._pc + 1
        self.opcodes[jump_pc] = f"jump {target - jump_pc}"

    def pop_opcode(self):
        self.opcodes.pop()
        self._pc -= 1

    def add_goto(self, label: str):
        self.block.gotos[self.pc] = (label, len(self.block.current_locals))
        self.add_opcode(None)

    def compile(self) -> Prototype:
        prototype = Prototype()
        prototype.func_name = self.func_name
        prototype.opcodes = self.opcodes
        prototype.num_locals = self.num_locals
        prototype.locals = self.locals
        prototype.consts = list(self.consts.keys())
        prototype.upvalues = list(self.upvalues.keys())
        prototype.fixed_params = self.fixed_params
        prototype.is_variadic = self.is_variadic
        return prototype


class _ProgramState:
    protos: list[_ProtoState]
    proto_stack: list[_ProtoState]
    num_lambdas: int

    class _ResolveAction(Enum):
        LOAD = auto()
        STORE = auto()

    def __init__(self):
        self.protos = []
        self.proto_stack = []
        self.num_lambdas = 0

    @property
    def proto(self) -> _ProtoState:
        return self.proto_stack[-1]

    def push_proto(self, func_name: str = None) -> tuple[_ProtoState, int]:
        proto_state = _ProtoState(func_name)
        index = len(self.protos)
        self.protos.append(proto_state)
        self.proto_stack.append(proto_state)
        return proto_state, index

    def pop_proto(self):
        self.proto_stack.pop()

    def get_proto(self, index: int) -> _ProtoState:
        return self.protos[index]

    def push_block(self) -> _BlockState:
        block = _BlockState()
        self.proto.block_stack.append(block)
        return block

    def pop_block(self):
        proto = self.proto
        block = proto.block_stack.pop()
        end = self.proto.pc - 1
        for var in block.current_locals:
            var.end = end
            proto.release_local(var.index)
        self.proto.locals.merge(block.current_locals)

    def read(self, name: str):
        self._resolve(name, self._ResolveAction.LOAD)

    def assign(self, name: str):
        self._resolve(name, self._ResolveAction.STORE)

    def _resolve(self, name: str, action: _ResolveAction):
        current_proto = self.proto
        visited_protos = []  # these protos may need an upvalue passed down to them
        for proto in reversed(self.proto_stack):
            visited_protos.append(proto)
            upvalue = self.proto != proto  # upvalues are locals from an enclosing function
            for block in reversed(proto.block_stack):
                if block.current_locals.has_name(name):
                    if upvalue:
                        # A local variable in an outer function. Create an
                        # upvalue and drill it through the proto stack.
                        for vp in visited_protos:
                            vp.get_upvalue_index(name)
                        upvalue_index = current_proto.get_upvalue_index(name)

                        opcode: str
                        if action == self._ResolveAction.LOAD:
                            opcode = "load_upvalue"
                        else:
                            opcode = "store_upvalue"

                        current_proto.add_opcode(f"{opcode} {upvalue_index}")
                    else:
                        # A local variable in the same function.
                        index = block.current_locals.get_by_name(name)[-1].index

                        opcode: str
                        if action == self._ResolveAction.LOAD:
                            opcode = "load_local"
                        else:
                            opcode = "store_local"

                        current_proto.add_opcode(f"{opcode} {index}")
                    return

        # If we could not find the local either in the same function or
        # in any of the enclosing ones, treat the variable as a global.
        env_index: int
        for proto in self.proto_stack:
            env_index = proto.get_upvalue_index("_ENV")
        name_index = current_proto.get_const_index(name)
        # noinspection PyUnboundLocalVariable
        current_proto.add_opcode(f"get_upvalue {env_index}")
        current_proto.add_opcode(f"push_const {name_index}")

        opcode: str
        if action == self._ResolveAction.LOAD:
            opcode = "get_table"
        else:
            opcode = "set_table"
        current_proto.add_opcode(opcode)

    def compile(self) -> Program:
        program = Program()
        for proto in self.protos:
            program.prototypes.append(proto.compile())
        return program

    def next_lambda_index(self) -> int:
        index = self.num_lambdas
        self.num_lambdas += 1
        return index


class Statement(ABC):
    @abstractmethod
    def emit(self, state: _ProgramState):
        raise NotImplementedError


class Expression(ABC):
    @abstractmethod
    def evaluate(self, state: _ProgramState):
        raise NotImplementedError


class MultiresExpression(ABC):
    @abstractmethod
    def evaluate(self, state: _ProgramState, return_count: int):
        pass


def evaluate_single(state: _ProgramState, expr: Expression | MultiresExpression):
    if isinstance(expr, MultiresExpression):  # function/method calls and varargs
        expr.evaluate(state, 2)
    elif isinstance(expr, Expression):  # standard singleres expression
        expr.evaluate(state)
    else:
        raise InternalCompilerError("Expected expression, got something else.")


# Used in:
# 1. Assignments.
# 2. Local assignments.
# 3. Generic for loops.
# Other adjustments are done dynamically by the VM at runtime.
def adjust_static(
        state: _ProgramState,
        count: int,
        expr_list: list[Expression | MultiresExpression],
):
    # If the last expression is multires, the
    # adjustment must be performed dynamically.
    # We still need to specify how many values
    # we expect to receive in the end.

    difference = count - len(expr_list)
    if difference > 0:  # append nils
        for expr in expr_list:
            evaluate_single(state, expr)
        for _ in range(difference):
            state.proto.add_opcode("push_nil")
    else:
        # Even if there are more values then expected,
        # we still have to evaluate them all and simply
        # discard them later.

        for i in range(len(expr_list) - 1):
            expr = expr_list[i]
            evaluate_single(state, expr)

        last = expr_list[-1]
        if isinstance(last, MultiresExpression):
            # Tell the VM to discard all values if
            # we're already beyond the list of names.
            return_count = 2 if (difference == 0) else 1
            last.evaluate(state, return_count)
        else:
            last.evaluate(state)

        for _ in range(-difference):  # diff is < 0 here, so negate it
            state.proto.add_opcode("pop")  # discard extra values


@dataclass
class String(Ast, Expression):
    value: str

    def evaluate(self, state: _ProgramState):
        index = state.proto.get_const_index(self.value)
        state.proto.add_opcode(f"push_const {index}")


@dataclass
class Number(Ast, Expression):
    value: int | float

    def evaluate(self, state: _ProgramState):
        if isinstance(self.value, int):
            state.proto.add_opcode(f"push_int {self.value}")
        elif isinstance(self.value, float):
            frac = self.value - int(self.value)
            if frac == 0.0:
                state.proto.add_opcode(f"push_float {int(self.value)}")
            else:
                index = state.proto.get_const_index(self.value)
                state.proto.add_opcode(f"push_const {index}")


class NilValue(Expression):
    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode("push_nil")


NilValue.instance = NilValue()


class TrueValue(Expression):
    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode("push_true")


TrueValue.instance = TrueValue()


class FalseValue(Expression):
    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode("push_false")


FalseValue.instance = FalseValue()


@dataclass
class BinaryOpExpression(Expression):
    opcode: str
    left: Expression
    right: Expression

    def evaluate(self, state: _ProgramState):
        self.left.evaluate(state)
        self.right.evaluate(state)
        state.proto.add_opcode(self.opcode)


@dataclass
class UnaryExpression(Expression):
    opcode: str

    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode(self.opcode)


class Varargs(Ast, MultiresExpression):
    def evaluate(self, state: _ProgramState, return_count: int):
        state.proto.add_opcode(f"get_varargs {return_count}")


class AttribName(Ast):
    def __init__(self, name: str, attribute: str | None = None):
        self.name = name
        self.attribute = attribute


# TODO: implement to-be-closed variables
@dataclass
class LocalAssignStmt(Ast, Statement):
    names: list[AttribName]
    exprs: list[Expression]

    def emit(self, state: _ProgramState):
        has_tbc_var: bool = False

        adjust_static(state, len(self.names), self.exprs)
        for attr_name in self.names[::-1]:
            local_index = state.proto.new_local(attr_name.name)
            # Only <const> and <close> are allowed by the spec.
            if attr_name.attribute:
                if attr_name.attribute == "close":
                    if has_tbc_var:
                        raise CompilationError("Var list already contains a to-be-closed variable.")
                    has_tbc_var = True
                    state.proto.block.tbc_locals.append(local_index)
                elif attr_name.attribute == "const":
                    state.proto.block.current_locals.get_by_name(attr_name.name).is_const = True
                else:
                    raise CompilationError(f"Unsupported attribute: <{attr_name.attribute}>.")

            state.proto.add_opcode(f"store_local {local_index}")


@dataclass
class Var(Ast, Expression):
    name: str

    def evaluate(self, state: _ProgramState):
        state.read(self.name)


@dataclass
class DotAccess(Ast, Expression):
    expression: Expression
    name: str

    def evaluate(self, state: _ProgramState):
        proto = state.proto
        self.expression.evaluate(state)
        index = proto.get_const_index(self.name)
        proto.add_opcode(f"push_const {index}")
        proto.add_opcode("get_table")


@dataclass
class TableAccess(Ast, Expression):
    table: Expression
    key: Expression

    def evaluate(self, state: _ProgramState):
        proto = state.proto
        self.table.evaluate(state)
        self.key.evaluate(state)
        proto.add_opcode("get_table")


VarType = Var | DotAccess | TableAccess


class AssignStmt(Ast, Statement):
    def __init__(self, var_list, expr_list=None):
        self.var_list: list[VarType] = var_list
        self.expr_list: list[Expression] = expr_list

    def emit(self, state: _ProgramState):
        proto = state.proto

        # Cache variables used in dot/table accesses to
        # ensure the assignment does not affect them.
        temp_indices = []
        for var in self.var_list:
            # TODO: use OOP here?
            if isinstance(var, Var):
                # A normal var only referes to a name
                # and thus doesn't need to be cached.
                continue
            elif isinstance(var, DotAccess):
                index = proto.new_temporary()
                temp_indices.append(index)
                var.expression.evaluate(state)
                proto.add_opcode(f"store_local {index}")
            elif isinstance(var, TableAccess):
                # TODO: optimize table access with consts (don't cache)
                table_index = proto.new_temporary()
                key_index = proto.new_temporary()
                temp_indices.append(table_index)
                temp_indices.append(key_index)

                evaluate_single(state, var.table)
                proto.add_opcode(f"store_local {table_index}")
                evaluate_single(state, var.key)
                proto.add_opcode(f"store_local {key_index}")
            else:
                raise InternalCompilerError("Unsupported assignment.")

        adjust_static(state, len(self.var_list), self.expr_list)

        temp_index = len(temp_indices) - 1  # ensure we read the indices in reverse order
        for var in self.var_list[::-1]:
            if isinstance(var, Var):
                state.assign(var.name)
            elif isinstance(var, DotAccess):
                local_index: int = temp_indices[temp_index]
                temp_index -= 1

                const_index: int = proto.get_const_index(var.name)
                proto.add_opcode(f"load_local {local_index}")
                proto.add_opcode(f"push_const {const_index}")
                proto.add_opcode("set_table")
            elif isinstance(var, TableAccess):
                # Again, reverse order.
                key_index = temp_indices[temp_index]
                temp_index -= 1
                table_index = temp_indices[temp_index]
                temp_index -= 1

                proto.add_opcode(f"load_local {table_index}")
                proto.add_opcode(f"load_local {key_index}")
                proto.add_opcode("set_table")

        for index in temp_indices:
            proto.release_local(index)


@dataclass
class Block(Ast, AsList, Statement):
    statements: list[Statement]

    def emit(self, state: _ProgramState):
        for statement in self.statements:
            if isinstance(statement, Block):
                state.push_block()
                statement.emit(state)
                state.pop_block()
            elif isinstance(statement, FuncCall):
                statement.evaluate(state, 0)
            else:
                statement.emit(state)


@dataclass
class FuncName(Ast, AsList):
    names: list[str]

    def to_lvalue(self) -> Var | DotAccess:
        if len(self.names) == 1:
            return Var(self.names[0])
        elif len(self.names) > 1:
            result = DotAccess(Var(self.names[0]), self.names[1])
            for i in range(2, len(self.names)):
                result = DotAccess(result, self.names[i])
            return result
        else:
            raise InternalCompilerError("Illegal function name: empty name list.")


class MethodName(FuncName):
    pass


class ParamList(Ast, AsList):
    names: list[str]
    has_varargs: bool

    def __init__(self, children: list):
        self.names = []
        self.has_varargs = False

        for child in children:
            if isinstance(child, str):
                self.names.append(child)
            elif isinstance(child, Varargs):
                self.has_varargs = True
            elif isinstance(child, list):
                self.names = child

    def add_self(self):
        self.names.insert(0, "self")


@dataclass
class FuncBody(Ast):
    params: ParamList | None
    block: Block


class FuncDef(Ast, Expression):
    def __init__(self, body: FuncBody, name: str = None):
        self.body = body
        self.name = name

    # TODO: define varargs order
    def evaluate(self, state: _ProgramState):
        if not self.name:
            my_number = state.next_lambda_index()
            self.name = f"$lambda#{my_number}"

        proto, proto_index = state.push_proto(self.name)
        block = state.push_block()

        body = self.body.block
        params = self.body.params

        if params:
            proto.fixed_params = len(params.names)
            proto.is_variadic = params.has_varargs

            for name in params.names:
                local_index = proto.get_local_index(name)
                proto.add_opcode(f"store_local {local_index}")

        body.emit(state)
        if body.statements and not isinstance(body.statements[-1], ReturnStmt):
            proto.add_opcode("return 1")

        # Close all goto's
        # TODO: review
        for pc, data in block.gotos.items():
            name, locals_count = data
            if proto.num_locals != locals_count:
                raise CompilationError("Cannot jump into a scope of a local variable.")
            target = proto.get_label_target(name)
            proto.set_jump(pc, target)

        state.pop_block()
        state.pop_proto()
        if state.proto_stack:  # TODO: refactor chunk compilation to skip creating closure
            state.proto.add_opcode(f"closure {proto_index}")


@dataclass
class FuncDefStmt(Ast, Statement):
    name: FuncName | MethodName
    body: FuncBody

    def emit(self, state: _ProgramState):
        if isinstance(self.name, MethodName):
            if self.body.params:
                self.body.params.add_self()
            else:
                params = ParamList([])
                params.add_self()
                self.body.params = params

        full_name = '.'.join(self.name.names)
        lvalue = self.name.to_lvalue()
        func_def = FuncDef(self.body, full_name)
        assign_stmt = AssignStmt([lvalue], [func_def])
        assign_stmt.emit(state)


@dataclass
class LocalFuncDefStmt(Ast, Statement):
    name: str
    body: FuncBody

    def emit(self, state: _ProgramState):
        func_def = FuncDef(self.body, self.name)
        assign_stmt = LocalAssignStmt([AttribName(self.name)], [func_def])
        assign_stmt.emit(state)


class ReturnStmt(Ast, Statement):
    def __init__(self, exprs: list[Expression] = None):
        self.exprs: list[Expression] | None = exprs

    def emit(self, state: _ProgramState):
        last_index = len(self.exprs) - 1
        for i, expr in enumerate(self.exprs):
            if isinstance(expr, MultiresExpression):
                size = 0 if (i == last_index) else 2
                expr.evaluate(state, size)
            else:
                expr.evaluate(state)

        return_count: int = len(self.exprs) + 1
        if isinstance(self.exprs[last_index], MultiresExpression):
            return_count = 0
        state.proto.add_opcode(f"return {return_count}")


@dataclass
class ExprField(Ast):
    key: Expression
    value: Expression


@dataclass
class NameField(Ast):
    name: str
    value: Expression


Field = Expression | ExprField | NameField


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
                    field.value.evaluate(state)
                    proto.add_opcode(f"load_local {table_local}")
                    field.key.evaluate(state)
                    proto.add_opcode("set_table")
                elif isinstance(field, NameField):
                    field.value.evaluate(state)
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
                    field.evaluate(state)
                    proto.add_opcode(f"load_local {table_local}")
                    proto.add_opcode("store_list 1")


class FuncCallParams(Ast):
    exprs: list[Expression]

    def __init__(self, child):
        if not child:
            self.exprs = []
        else:
            if isinstance(child, list):
                self.exprs = child
            else:
                self.exprs = [child]


class FuncCall(Ast, MultiresExpression):
    primary: Expression
    params: FuncCallParams

    def __init__(self, primary: Expression, params: FuncCallParams):
        self.primary = primary
        self.params = params

    def evaluate(self, state: _ProgramState, return_count: int = 1):
        index = self._eval_primary(state)

        param_count: int = self._get_param_count()
        last = len(self.params.exprs) - 1
        self._push_self(state, index)
        for i in range(len(self.params.exprs)):
            expr = self.params.exprs[i]
            if i == last:
                if isinstance(expr, Varargs):
                    param_count = 0
                    state.proto.add_opcode("get_varargs 0")
                else:
                    expr.evaluate(state)
            else:
                if isinstance(expr, Varargs):
                    state.proto.add_opcode("get_varargs 1")
                else:
                    expr.evaluate(state)

        state.proto.add_opcode(f"call {param_count} {return_count}")

    # noinspection PyTypeChecker
    def _eval_primary(self, state: _ProgramState) -> int:
        self.primary.evaluate(state)
        return None

    def _push_self(self, state: _ProgramState, index: int | None):
        pass

    def _get_param_count(self):
        return len(self.params.exprs) + 1


class MethodCall(FuncCall):
    def __init__(self, primary: Expression, name: str, params: FuncCallParams):
        super().__init__(primary, params)
        self.name = name

    def _eval_primary(self, state: _ProgramState):
        obj_index = state.proto.new_temporary()
        self.primary.evaluate(state)
        state.proto.add_opcode(f"store_local {obj_index}")

    def _push_self(self, state: _ProgramState, index: int | None):
        state.proto.add_opcode(f"load_local {index}")


@dataclass
class WhileStmt(Ast, Statement):
    expr: Expression
    block: Block

    def emit(self, state: _ProgramState):
        proto = state.proto
        start = proto.pc
        self.expr.evaluate(state)
        proto.add_opcode("test")
        jump_pc = proto.pc
        proto.add_opcode(None)

        body_block = state.push_block()
        self.block.emit(state)
        state.pop_block()

        proto.add_jump(start)
        block_end = proto.pc

        proto.set_jump(jump_pc, block_end)
        for br in body_block.breaks:
            proto.set_jump(br, block_end)


@dataclass
class RepeatStmt(Ast, Statement):
    block: Block
    expr: Expression

    def emit(self, state: _ProgramState):
        state.push_block()
        start = state.proto.pc
        self.block.emit(state)
        self.expr.evaluate(state)
        state.proto.add_opcode("test")
        end = state.proto.pc
        state.proto.add_jump(start, end)
        state.pop_block()


class BreakStmt(Ast, Statement):
    def emit(self, state: _ProgramState):
        pc = state.proto.pc
        state.proto.add_opcode(None)
        state.proto.block.breaks.append(pc)


@dataclass
class ElseIf(Ast):
    condition: Expression
    block: Block


class IfStmt(Ast, AsList, Statement):
    def __init__(self, children: list):
        self.end_jumps: list[int] = []

        if isinstance(children[0], Expression):
            self.condition: Expression = children[0]
        else:
            raise InternalCompilerError("Illegal 'if' statement: non-expression in condition.")
        if isinstance(children[1], Block):
            self.block: Block = children[1]
        else:
            raise InternalCompilerError("Illegal 'if' statement: non-block body.")

        self.elseifs: list[ElseIf] = []
        self.elze: Block | None = children[-1]
        for i in range(2, len(children) - 1):
            self.elseifs.append(children[i])

    def emit(self, state: _ProgramState):
        proto = state.proto

        skip_end_jump = not self.elze and len(self.elseifs) == 0
        self._emit_branch(state, self.condition, self.block, skip_end_jump)
        for i, el in enumerate(self.elseifs):
            self._emit_branch(state, el.condition, el.block, i == len(self.elseifs) - 1)
        if self.elze:
            state.push_block()
            self.elze.emit(state)
            state.pop_block()

        for jump_pc in self.end_jumps:  # TODO: remove "jump 1" when "else" block is missing
            proto.set_jump(jump_pc)

    def _emit_branch(
            self,
            state: _ProgramState,
            condition: Expression,
            block: Block,
            skip_end_jump: bool
    ):
        proto = state.proto
        condition.evaluate(state)
        proto.add_opcode("test")
        jump_pc = proto.pc
        proto.add_opcode(None)

        state.push_block()
        block.emit(state)
        state.pop_block()

        if not skip_end_jump:
            self.end_jumps.append(proto.pc)
            proto.add_opcode(None)
        proto.set_jump(jump_pc)


def emit_for_loop_body(
        state: _ProgramState,
        body: Block,
        block: _BlockState,
        loop_start_pc: int,
):
    proto = state.proto
    escape_jump_pc = proto.reserve_opcodes(1)
    body.emit(state)
    proto.add_jump(loop_start_pc)

    proto.set_jump(escape_jump_pc)
    for br in block.breaks:
        proto.set_jump(br)


@dataclass
class ForLoopNum(Ast, Statement):
    control_name: str
    initial_expr: Expression
    limit_expr: Expression
    step_expr: Expression | None
    body: Block

    def emit(self, state: _ProgramState):
        proto = state.proto
        block = state.push_block()

        proto.linear_mode = True
        control_index = proto.new_local(self.control_name)
        for _ in range(2):
            proto.new_temporary()
        proto.linear_mode = False

        evaluate_single(state, self.initial_expr)
        evaluate_single(state, self.limit_expr)
        if self.step_expr:
            evaluate_single(state, self.step_expr)
        else:
            proto.add_opcode("push_int 1")
        proto.add_opcode(f"prepare_for_num {control_index}")

        loop_start_pc = proto.pc
        proto.add_opcode(f"test_for {control_index}")
        emit_for_loop_body(state, self.body, block, loop_start_pc)
        state.pop_block()


@dataclass
class ForLoopGen(Ast, AsList, Statement):
    name_list: list[str]
    expr_list: list[Expression | MultiresExpression]
    body: Block

    def __init__(self, children: list):
        self.name_list = children[0:-2]
        self.expr_list = children[-2]
        self.body = children[-1]

    def emit(self, state: _ProgramState):
        proto = state.proto
        block = state.push_block()

        proto.linear_mode = True
        iterator_index = proto.new_temporary()
        state_index = proto.new_temporary()
        control_index = proto.get_local_index(self.name_list[0])
        closing_val_index = proto.new_temporary()
        proto.linear_mode = False

        name_indices = [control_index]
        for i in range(1, len(self.name_list)):
            name = self.name_list[i]
            index = proto.get_local_index(name)
            name_indices.append(index)

        adjust_static(state, 4, self.expr_list)
        proto.add_opcode(f"prepare_for_gen {control_index}")

        # TODO: check param and retval orders
        loop_start_pc = proto.pc
        proto.add_opcode(f"load_local {state_index}")
        proto.add_opcode(f"load_local {control_index}")
        proto.add_opcode(f"load_local {iterator_index}")
        proto.add_opcode(f"call 3 {len(self.name_list)}")

        for index in reversed(name_indices):
            proto.add_opcode(f"store_local {index}")

        proto.add_opcode(f"load_local {control_index}")
        proto.add_opcode(f"test_nil")
        emit_for_loop_body(state, self.body, block, loop_start_pc)
        state.pop_block()


@dataclass
class Label(Ast, Statement):
    name: str

    def emit(self, state: _ProgramState):
        state.proto.add_label(self.name)


# TODO: ensure correct analysis of local scope
@dataclass
class GotoStmt(Ast, Statement):
    label: str

    def emit(self, state: _ProgramState):
        state.proto.add_goto(self.label)


@dataclass
class Chunk(Ast):
    block: Block

    def emit(self) -> Program:
        program_state = _ProgramState()
        func_name = "$main"
        func_body = FuncBody(ParamList([Varargs()]), self.block)
        func_def = FuncDef(func_body, func_name)
        func_def.evaluate(program_state)
        program_state.get_proto(0).get_upvalue_index("_ENV")
        return program_state.compile()


# noinspection PyPep8Naming
class LuarkTransformer(Transformer):
    def start(self, children):
        return children[-1]

    def dec_int(self, n):
        num: str = n[0]
        num: list[str] = num.casefold().split("e")
        if len(num) == 1:
            return Number(int(num[0]))
        elif len(num) == 2:
            return Number(int(num[0]) * 10 ** int(num[1]))
        else:
            raise InternalCompilerError(f"Illegal decimal integer literal: '{n}'")

    def dec_float(self, f):
        num: str = f[0]
        num: list[str] = num.casefold().split("e")
        if len(num) == 1:
            return Number(float(num[0]))
        elif len(num) == 2:
            return Number(float(num[0]) * 10 ** float(num[1]))
        else:
            raise InternalCompilerError(f"Illegal decimal float literal: '{f}'")

    def empty_stmt(self, _):
        return Discard

    def nil(self, _):
        return NilValue.instance

    def true(self, _):
        return TrueValue.instance

    def false(self, _):
        return FalseValue.instance

    def expr_list(self, exprs) -> list[Expression]:
        return exprs

    def var_list(self, varz) -> list[Var | DotAccess | TableAccess]:
        return varz

    def name_list(self, names) -> list[str]:
        return names

    def attrib_name_list(self, names) -> list[AttribName]:
        return names

    def ID(self, s):
        return str(s)

    # TODO: raise error on unknown escape sequences
    # TODO: support \xXX, \ddd, \u{XXX}
    def STRING(self, s):
        s = ''.join([s.strip() for s in s.split("\\z")])
        s = (str(s)[1:-1]
             .replace("\\a", "\a")
             .replace("\\b", "\b")
             .replace("\\f", "\f")
             .replace("\\n", "\n")
             .replace("\\r", "\r")
             .replace("\\t", "\t")
             .replace("\\v", "\v")
             .replace("\\\\", "\\")
             .replace("\\\"", "\"")
             .replace("\\\'", "\'")
             .replace("\\\n", "\n"))
        return s

    def MULTISTRING(self, s):
        s = str(s)
        size = s.find("[", 1) + 1
        return s[size:-size].removeprefix("\n")

    def _bin_num_op_expr(self, c: list, op: str, func: Callable):
        if (isinstance(c[0], Number)
                and isinstance(c[1], Number)):
            return Number(func(c[0].value, c[1].value))
        else:
            return BinaryOpExpression(op, *c)

    def or_expr(self, c):
        return BinaryOpExpression("or", *c)

    def and_expr(self, c):
        return BinaryOpExpression("and", *c)

    def comp_lt(self, c):
        return BinaryOpExpression("lt", *c)

    def comp_gt(self, c):
        return BinaryOpExpression("gt", *c)

    def comp_le(self, c):
        return BinaryOpExpression("le", *c)

    def comp_ge(self, c):
        return BinaryOpExpression("ge", *c)

    def comp_eq(self, c):
        return BinaryOpExpression("eq", *c)

    def comp_neq(self, c):
        return BinaryOpExpression("neq", *c)

    def bw_or_expr(self, c):
        return BinaryOpExpression("bor", *c)

    def bw_xor_expr(self, c):
        return BinaryOpExpression("bxor", *c)

    def bw_and_expr(self, c):
        return BinaryOpExpression("band", *c)

    def lsh_expr(self, c):
        return BinaryOpExpression("lsh", *c)

    def rsh_expr(self, c):
        return BinaryOpExpression("rsh", *c)

    def concat_expr(self, c):
        if (isinstance(c[0], String)
                and isinstance(c[1], String)):
            return String(c[0].value + c[1].value)
        else:
            return BinaryOpExpression("concat", *c)

    def add_expr(self, c):
        return self._bin_num_op_expr(c, "add", lambda x, y: x + y)

    def sub_expr(self, c):
        return self._bin_num_op_expr(c, "sub", lambda x, y: x - y)

    def mul_expr(self, c):
        return self._bin_num_op_expr(c, "mul", lambda x, y: x * y)

    def _divide(self, x: int | float, y: int | float):
        if y != 0:
            return x / y
        else:
            if x > 0:
                return float("inf")
            elif x == 0:
                return float("nan")
            else:
                return float("-inf")

    def div_expr(self, c):
        return self._bin_num_op_expr(c, "div", self._divide)

    def fdiv_expr(self, c):
        return self._bin_num_op_expr(c, "fdiv", lambda x, y: math.floor(x / y))

    def mod_expr(self, c):
        return self._bin_num_op_expr(c, "mod", lambda x, y: x % y)

    def unary_minus(self, c):
        if isinstance(c[0], Number):
            return Number(-c[0].value)
        else:
            return UnaryExpression("negate")

    def unary_not(self, _):
        return UnaryExpression("not")

    def unary_length(self, _):
        return UnaryExpression("len")

    def unary_bw_not(self, _):
        return UnaryExpression("bnot")

    def exp_expr(self, c):
        return self._bin_num_op_expr(c, "exp", lambda x, y: x ** y)
