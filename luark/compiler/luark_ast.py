import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from lark.ast_utils import Ast, AsList
from lark.visitors import Transformer, Discard

from luark.compiler.errors import InternalCompilerError
from luark.compiler.program import Program, Prototype


class _BlockState:
    def __init__(self):
        self.locals: dict[str, int] = {}
        self.aux_locals: list[int] = []


class _ProtoState:
    def __init__(self, func_name: str = None):
        self.func_name: str = func_name
        self.pc: int = 0
        self.num_locals: int = 0
        self.blocks: list[_BlockState] = []
        self.opcodes: list[str] = []
        self.consts: list[int | float | str] = []
        self.upvalues: list[str] = ["_ENV"]

    @property
    def block(self) -> _BlockState:
        return self.blocks[-1]

    def get_const_index(self, value) -> int:
        for i in range(len(self.consts)):
            if self.consts[i] == value:
                return i

        index = len(self.consts)
        self.consts.append(value)
        return index

    def get_local_index(self, name: str) -> int:
        if name in self.block.locals:
            return self.block.locals[name]
        else:
            index = self.num_locals
            self.num_locals += 1
            self.block.locals[name] = index
            return index

    def get_upvalue_index(self, name: str) -> int:
        for i in range(len(self.upvalues)):
            if self.upvalues[i] == name:
                return i

        index = len(self.consts)
        self.consts.append(name)
        return index

    def add_aux_local(self) -> int:
        index = self.num_locals
        self.block.aux_locals.append(index)
        self.num_locals += 1
        return index

    def load_global(self, name: str):
        env_index = self.get_upvalue_index("_ENV")
        self.add_opcode(f"get_upvalue {env_index}")
        name_index = self.get_const_index(name)
        self.add_opcode(f"push_const {name_index}")
        self.add_opcode(f"get_table")

    def store_global(self, name: str):
        env_index = self.get_upvalue_index("_ENV")
        self.add_opcode(f"get_upvalue {env_index}")
        name_index = self.get_const_index(name)
        self.add_opcode(f"push_const {name_index}")
        self.add_opcode(f"set_table")

    def add_opcode(self, opcode):
        self.opcodes.append(opcode)
        self.pc += 1

    def compile(self) -> Prototype:
        self.add_opcode("return")
        prototype = Prototype()
        prototype.func_name = self.func_name
        prototype.opcodes = self.opcodes
        prototype.num_locals = self.num_locals
        prototype.consts = self.consts
        return prototype

    def get_local(self, own_name: str) -> int:
        if own_name in self.block.locals:
            return self.block.locals[own_name]
        else:
            index = self.num_locals
            self.num_locals += 1
            self.block.locals[own_name] = index
            return index


class _ProgramState:
    def __init__(self):
        self.protos: list[_ProtoState] = []
        self.stack: list[_ProtoState] = []

    @property
    def proto(self) -> _ProtoState:
        return self.stack[-1]

    def push_proto(self, func_name: str = None) -> int:
        proto_state = _ProtoState(func_name)
        index = len(self.protos)
        self.protos.append(proto_state)
        self.stack.append(proto_state)
        return index

    def pop_proto(self):
        self.stack.pop()

    def compile(self) -> Program:
        program = Program()
        for proto in self.protos:
            program.prototypes.append(proto.compile())
        program.prototypes[0].func_name = "$main"
        return program


class Statement(ABC):
    @abstractmethod
    def emit(self, state: _ProgramState):
        raise NotImplementedError


class Expression(ABC):
    @abstractmethod
    def evaluate(self, state: _ProgramState):
        raise NotImplementedError


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


class AttribName(Ast):
    def __init__(self, name: str, attribute: str = None):
        # TODO!
        # Only <const> and <close> are allowed by the spec.
        if attribute:
            raise NotImplementedError

        self.name = name
        self.attribute = attribute


@dataclass
class LocalStmt(Ast, Statement):
    def __init__(self, names: list[AttribName], exprs: list[Expression] = None):
        self.names: list[AttribName] = names

        self.exprs: list[Expression]
        if exprs:
            nil_count = max(len(names) - len(exprs), 0)
            exprs.extend([NilValue.instance] * nil_count)
            self.exprs = exprs
        else:
            self.exprs = [NilValue.instance] * len(names)

    def emit(self, state: _ProgramState):
        for expr in self.exprs:
            expr.evaluate(state)
        for aname in self.names[::-1]:
            local_index = state.proto.num_locals
            state.proto.block.locals[aname.name] = local_index
            state.proto.add_opcode(f"store_local {local_index}")
            state.proto.num_locals += 1


@dataclass
class Var(Ast, Expression):
    name: str

    def evaluate(self, state: _ProgramState):
        # 1. check locals
        # 2. check upvalues
        # 3. check globals
        proto = state.proto
        block = proto.block
        if self.name in block.locals:
            index = block.locals[self.name]
            proto.add_opcode(f"load_local {index}")
        else:
            raise NotImplementedError  # TODO!


@dataclass
class DotAccess(Ast, Expression):
    expression: Expression
    name: str

    def evaluate(self, state: _ProgramState):
        raise NotImplementedError


class TableAccess(Ast, Expression):
    table: Expression
    key: Expression

    def evaluate(self, state: _ProgramState):
        raise NotImplementedError


class AssignStmt(Ast, Statement):
    def __init__(self, var_list, expr_list=None):
        self.var_list: list[Var | DotAccess | TableAccess] = var_list

        self.expr_list: list[Expression]
        if expr_list:
            nil_count = max(len(var_list) - len(expr_list), 0)
            expr_list.extend([NilValue.instance] * nil_count)
            self.expr_list = expr_list
        else:
            self.expr_list = [NilValue.instance] * len(var_list)

    # TODO!
    def emit(self, state: _ProgramState):
        proto = state.proto

        aux = {}
        for var in self.var_list:
            if isinstance(var, Var):
                continue
            elif isinstance(var, DotAccess):
                index = proto.add_aux_local()
                var.expression.evaluate(state)
                proto.add_opcode(f"local_store {index}")
                aux[var] = index
            elif isinstance(var, TableAccess):
                table_index = proto.add_aux_local()
                key_index = proto.add_aux_local()
                var.table.evaluate(state)
                proto.add_opcode(f"store_local {table_index}")
                var.key.evaluate(state)
                proto.add_opcode(f"store_local {key_index}")
                aux[var] = (table_index, key_index)
            else:
                raise InternalCompilerError("Unsupported assignment.")

        for expr in self.expr_list:
            expr.evaluate(state)

        for var in self.var_list[::-1]:
            if isinstance(var, Var):
                # local, same block
                # local, outer block, same function
                # local, enclosing function -> upvalue
                # global (_ENV)
                self.assign_var(var, state)

    def assign_var(self, var, state: _ProgramState):
        my_proto = state.proto

        found = False
        for block in my_proto.blocks[::-1]:
            if var.name in block.locals:
                found = True
                index = block.locals[var.name]
                my_proto.add_opcode(f"store_local {index}")
                break
        if found:
            return

        # TODO: upvalues
        my_proto.store_global(var.name)


@dataclass
class Block(Ast, AsList):
    statements: list

    def emit(self, state: _ProgramState):
        state.proto.blocks.append(_BlockState())
        for statement in self.statements:
            statement.emit(state)
        state.proto.blocks.pop()


@dataclass
class FuncName(Ast, AsList):
    names: list[str]


class MethodName(Ast, AsList):
    def __init__(self, children: list[str]):
        self.names: list[str] = children[:-1]
        self.method_name: str = children[-1]


class Varargs(Ast):
    pass


class VarargList(Ast, AsList):
    def __init__(self, children):
        self.exprs: list[Expression] = children[:-1]


class FuncBody(Ast, AsList):
    def __init__(self, children):
        self.params: list[Expression] | VarargList | Varargs = children[:-1]
        self.block: Block = children[-1]


@dataclass
class FuncDefStmt(Ast, Statement):
    name: FuncName | MethodName | str
    body: FuncBody

    def emit(self, state: _ProgramState):
        if isinstance(self.name, MethodName):
            raise NotImplementedError
        if isinstance(self.name, FuncName) and len(self.name.names) != 1:
            raise NotImplementedError

        # TODO: implement params
        own_name = self.name.names[-1] if isinstance(self.name, FuncName) else self.name
        index = state.push_proto(own_name)
        self.body.block.emit(state)
        state.pop_proto()
        self.assign(state, own_name, index)

    def assign(self, state: _ProgramState, own_name: str, index: int):
        my_proto = state.proto
        my_proto.add_opcode(f"closure {index}")
        env_index = my_proto.get_upvalue_index("_ENV")
        my_proto.add_opcode(f"get_upvalue {env_index}")
        name_index = my_proto.get_const_index(own_name)
        my_proto.add_opcode(f"push_const {name_index}")
        my_proto.add_opcode("set_table")


class LocalFuncDef(FuncDefStmt):
    def assign(self, state: _ProgramState, own_name: str, index: int):
        my_proto = state.proto
        my_proto.add_opcode(f"closure {index}")
        local = my_proto.get_local(own_name)
        my_proto.add_opcode(f"store_local {local}")


@dataclass
class Chunk(Ast):
    block: Block

    def emit(self) -> Program:
        program_state = _ProgramState()
        program_state.push_proto()
        self.block.emit(program_state)
        program_state.pop_proto()
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
            raise Exception(f"Illegal decimal integer literal: '{n}'")  # TODO: replace exception class

    def dec_float(self, f):
        num: str = f[0]
        num: list[str] = num.casefold().split("e")
        if len(num) == 1:
            return Number(float(num[0]))
        elif len(num) == 2:
            return Number(float(num[0]) * 10 ** float(num[1]))
        else:
            raise Exception(f"Illegal decimal float literal: '{f}'")

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
        raise NotImplementedError
        # s = str(s)
        # size = s.find("[", 1) + 1
        # return s[size:-size]

    def concat_expr(self, c):
        if (isinstance(c[0], String)
                and isinstance(c[1], String)):
            return String(c[0].value + c[1].value)
        else:
            raise NotImplementedError

    def _bin_num_op_expr(self, c: list, op: str, func: Callable):
        if (isinstance(c[0], Number)
                and isinstance(c[1], Number)):
            return Number(func(c[0].value, c[1].value))
        else:
            return BinaryOpExpression(op, *c)

    # TODO: optimize `or true`, `and false`

    def add_expr(self, c):
        return self._bin_num_op_expr(c, "add", lambda x, y: x + y)

    def sub_expr(self, c):
        return self._bin_num_op_expr(c, "sub", lambda x, y: x - y)

    def mul_expr(self, c):
        return self._bin_num_op_expr(c, "mul", lambda x, y: x * y)

    def div_expr(self, c):
        return self._bin_num_op_expr(c, "div", lambda x, y: x / y)

    def fdiv_expr(self, c):
        return self._bin_num_op_expr(c, "fdiv", lambda x, y: math.floor(x / y))

    def mod_expr(self, c):
        return self._bin_num_op_expr(c, "mod", lambda x, y: x % y)

    def exp_expr(self, c):
        return self._bin_num_op_expr(c, "exp", lambda x, y: x ** y)

    def unary_minus(self, c):
        if isinstance(c[0], Number):
            return Number(-c[0].value)
        else:
            raise NotImplementedError
