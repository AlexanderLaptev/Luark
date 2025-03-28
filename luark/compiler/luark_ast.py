import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable

from lark.ast_utils import Ast, AsList
from lark.visitors import Transformer, Discard

from luark.compiler.errors import InternalCompilerError
from luark.compiler.program import Program, Prototype


# TODO: refactor expression types

class _BlockState:
    def __init__(self):
        self.locals: dict[str, int] = {}
        self.aux_locals: list[int] = []  # auxiliary locals are used by the compiler
        self.breaks: list[int] = []


ConstType = int | float | str


class _ProtoState:
    def __init__(self, func_name: str = None, ):
        self.fixed_params: int = 0
        self.is_variadic: bool = False

        self.func_name: str = func_name
        self.pc: int = 0
        self.blocks: list[_BlockState] = []

        self.num_upvalues: int = 1
        self.num_consts: int = 0
        self.num_locals: int = 0

        self.upvalues: dict[str, int] = {"_ENV": 0}  # TODO: pass _ENV only when needed
        self.consts: dict[ConstType, int] = {}
        self.opcodes: list[str] = []

    @property
    def block(self) -> _BlockState:
        return self.blocks[-1]

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

    def get_local_index(self, own_name: str) -> int:
        if own_name in self.block.locals:
            return self.block.locals[own_name]
        index = self.num_locals
        self.num_locals += 1
        self.block.locals[own_name] = index
        return index

    def add_aux_local(self) -> int:
        index = self.num_locals
        self.block.aux_locals.append(index)
        self.num_locals += 1
        return index

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
        prototype.upvalues = self.upvalues
        return prototype


class _ProgramState:
    def __init__(self):
        self.protos: list[_ProtoState] = []
        self.stack: list[_ProtoState] = []

        self.num_lambdas: int = 0

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

    def assign(self, name: str):
        self._resolve(name, False)

    def read(self, name: str):
        self._resolve(name, True)

    def _resolve(self, name: str, get: bool):
        current_proto = self.proto
        visited_protos = []  # these protos may need an upvalue passed down to them
        for proto in reversed(self.stack):
            visited_protos.append(proto)
            upvalue = self.proto != proto  # upvalues are locals from an enclosing function
            for block in reversed(proto.blocks):
                if name in block.locals:
                    if upvalue:
                        # A local variable in an outer function. Create an
                        # upvalue and drill it through the proto stack.
                        for vp in visited_protos:
                            vp.get_upvalue_index(name)
                        upvalue_index = current_proto.get_upvalue_index(name)
                        opcode = "load_upvalue" if get else "store_upvalue"
                        current_proto.add_opcode(f"{opcode} {upvalue_index}")
                    else:
                        # A local variable in the same function.
                        index = block.locals[name]
                        opcode = "load_local" if get else "store_local"
                        current_proto.add_opcode(f"{opcode} {index}")

                    return

        # If we could not find the local either in the same function or
        # in any of the enclosing ones, treat the variable as a global.
        env_index = current_proto.get_upvalue_index("_ENV")
        name_index = current_proto.get_const_index(name)
        current_proto.add_opcode(f"get_upvalue {env_index}")
        current_proto.add_opcode(f"push_const {name_index}")
        current_proto.add_opcode("get_table" if get else "set_table")

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
    def evaluate(self, state: _ProgramState, *args, **kwargs):
        raise NotImplementedError


class MultiresExpression:
    pass


def eval_multires_expr(
        state: _ProgramState,
        expr: MultiresExpression,
        size: int,
):
    if isinstance(expr, FuncCall):
        expr.evaluate(state, size)
    elif isinstance(expr, Varargs):
        state.proto.add_opcode(f"get_varargs {size}")
    else:
        raise InternalCompilerError("Illegal multires expression type.")


def adjust_expr_list(
        state: _ProgramState,
        name_count: int,
        expr_list: list[Expression | MultiresExpression],
):
    difference = name_count - len(expr_list)
    if difference > 0:  # names > exprs
        for i in range(len(expr_list) - 1):
            eval_multires_expr(state, expr_list[i], 1)

        last = expr_list[-1]
        if isinstance(last, MultiresExpression):
            eval_multires_expr(state, last, difference + 1)
        else:
            for _ in range(difference + 1):
                state.proto.add_opcode("push_nil")
    else:  # names == exprs OR names < exprs
        for i in range(name_count):
            expr = expr_list[i]
            if isinstance(expr, MultiresExpression):
                eval_multires_expr(state, expr, 1)
            else:
                expr.evaluate(state)


@dataclass
class String(Ast, Expression):
    value: str

    def evaluate(self, state: _ProgramState, *args, **kwargs):
        index = state.proto.get_const_index(self.value)
        state.proto.add_opcode(f"push_const {index}")


@dataclass
class Number(Ast, Expression):
    value: int | float

    def evaluate(self, state: _ProgramState, *args, **kwargs):
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
    def evaluate(self, state: _ProgramState, *args, **kwargs):
        state.proto.add_opcode("push_nil")


NilValue.instance = NilValue()


class TrueValue(Expression):
    def evaluate(self, state: _ProgramState, *args, **kwargs):
        state.proto.add_opcode("push_true")


TrueValue.instance = TrueValue()


class FalseValue(Expression):
    def evaluate(self, state: _ProgramState, *args, **kwargs):
        state.proto.add_opcode("push_false")


FalseValue.instance = FalseValue()


@dataclass
class BinaryOpExpression(Expression):
    opcode: str
    left: Expression
    right: Expression

    def evaluate(self, state: _ProgramState, *args, **kwargs):
        self.left.evaluate(state)
        self.right.evaluate(state)
        state.proto.add_opcode(self.opcode)


class Varargs(Ast, MultiresExpression):
    pass


class AttribName(Ast):
    def __init__(self, name: str, attribute: str = None):
        # TODO!
        # Only <const> and <close> are allowed by the spec.
        if attribute:
            raise NotImplementedError

        self.name = name
        self.attribute = attribute


@dataclass
class LocalAssignStmt(Ast, Statement):
    names: list[AttribName]
    exprs: list[Expression] = None

    def emit(self, state: _ProgramState):
        adjust_expr_list(state, len(self.names), self.exprs)
        for attr_name in self.names[::-1]:
            local_index = state.proto.num_locals
            state.proto.block.locals[attr_name.name] = local_index
            state.proto.add_opcode(f"store_local {local_index}")
            state.proto.num_locals += 1


@dataclass
class Var(Ast, Expression):
    name: str

    def evaluate(self, state: _ProgramState, *args, **kwargs):
        state.read(self.name)


@dataclass
class DotAccess(Ast, Expression):
    expression: Expression
    name: str

    def evaluate(self, state: _ProgramState, *args, **kwargs):
        proto = state.proto
        self.expression.evaluate(state)
        index = proto.get_const_index(self.name)
        proto.add_opcode(f"push_const {index}")
        proto.add_opcode("get_table")


@dataclass
class TableAccess(Ast, Expression):
    table: Expression
    key: Expression

    def evaluate(self, state: _ProgramState, *args, **kwargs):
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

        aux = []
        for var in self.var_list:
            if isinstance(var, Var):
                continue
            elif isinstance(var, DotAccess):
                index = proto.add_aux_local()
                var.expression.evaluate(state)
                proto.add_opcode(f"local_store {index}")
                aux.append(index)
            elif isinstance(var, TableAccess):
                table_index = proto.add_aux_local()
                key_index = proto.add_aux_local()

                var.table.evaluate(state)
                proto.add_opcode(f"store_local {table_index}")
                var.key.evaluate(state)
                proto.add_opcode(f"store_local {key_index}")

                aux.append(table_index)
                aux.append(key_index)
            else:
                raise InternalCompilerError("Unsupported assignment.")

        adjust_expr_list(state, len(self.var_list), self.expr_list)

        aux_index = len(aux) - 1
        for var in self.var_list[::-1]:
            if isinstance(var, Var):
                state.assign(var.name)
            elif isinstance(var, DotAccess):
                local_index: int = aux[aux_index]
                aux_index -= 1

                const_index: int = proto.get_const_index(var.name)
                proto.add_opcode(f"load_local {local_index}")
                proto.add_opcode(f"push_const {const_index}")
                proto.add_opcode("set_table")
            elif isinstance(var, TableAccess):
                key_index = aux[aux_index]
                aux_index -= 1
                table_index = aux[aux_index]
                aux_index -= 1

                proto.add_opcode(f"load_local {table_index}")
                proto.add_opcode(f"load_local {key_index}")
                proto.add_opcode("set_table")
            # not adding else because we already did above


@dataclass
class Block(Ast, AsList):
    statements: list[Statement]

    def emit(self, state: _ProgramState):
        block = _BlockState()
        state.proto.blocks.append(block)  # TODO: consider refactoring
        for statement in self.statements:
            statement.emit(state)
        state.proto.blocks.pop()
        return block


@dataclass
class FuncName(Ast, AsList):
    names: list[str]


class MethodName(Ast, AsList):
    def __init__(self, children: list[str]):
        self.names: list[str] = children[:-1]
        self.method_name: str = children[-1]


class VarargList(Ast, AsList):
    def __init__(self, children):
        self.names: list[str] = children


class FuncBody(Ast):
    def __init__(self, params, block):
        self.params: list[str] | VarargList | Varargs = params
        self.block: Block = block


class FuncDef(Ast, Expression):
    def __init__(self, body: FuncBody, name: str = None):
        self.body: FuncBody = body
        self.name: str | None = name

    # TODO: define vararg behavior
    def evaluate(self, state: _ProgramState, *args, **kwargs):
        if not self.name:
            my_number = state.num_lambdas
            state.num_lambdas += 1
            self.name = f"$lambda#{my_number}"

        proto_index = state.push_proto(self.name)
        proto = state.proto
        block = _BlockState()
        proto.blocks.append(block)

        body = self.body.block
        params = self.body.params
        fixed_params: int = 0
        is_variadic: bool = False

        if isinstance(params, list) or (is_variadic := isinstance(params, VarargList)):
            if is_variadic:
                params = params.names

            fixed_params = len(params)
            for param in reversed(params):
                local_index = proto.get_local_index(param)
                proto.add_opcode(f"local_store {local_index}")

            if is_variadic:
                proto.add_opcode("pack_varargs")
        elif isinstance(params, Varargs):
            is_variadic = True
            proto.add_opcode("pack_varargs")
        else:
            raise InternalCompilerError("Illegal function definition: illegal type of parameters.")
        proto.fixed_params = fixed_params
        proto.is_variadic = is_variadic

        for statement in body.statements:
            statement.emit(state)

        proto.blocks.pop()
        state.pop_proto()
        state.proto.add_opcode(f"closure {proto_index}")


@dataclass
class FuncDefStmt(Ast, Statement):
    name: FuncName | MethodName | str
    body: FuncBody

    def emit(self, state: _ProgramState):
        if isinstance(self.name, MethodName):  # TODO
            raise NotImplementedError
        if isinstance(self.name, FuncName) and len(self.name.names) != 1:
            raise NotImplementedError

        own_name = self.name.names[-1] if isinstance(self.name, FuncName) else self.name
        func_def = FuncDef(self.body, own_name)
        func_def.evaluate(state)
        self.assign(state, own_name)

    def assign(self, state: _ProgramState, own_name: str):
        my_proto = state.proto
        env_index = my_proto.get_upvalue_index("_ENV")
        my_proto.add_opcode(f"get_upvalue {env_index}")
        name_index = my_proto.get_const_index(own_name)
        my_proto.add_opcode(f"push_const {name_index}")
        my_proto.add_opcode("set_table")


class LocalFuncDefStmt(FuncDefStmt):
    def assign(self, state: _ProgramState, own_name: str):
        my_proto = state.proto
        local = my_proto.get_local_index(own_name)
        my_proto.add_opcode(f"store_local {local}")


class ReturnStmt(Ast, Statement):
    def __init__(self, exprs: list[Expression] = None):
        self.exprs: list[Expression] | None = exprs

    def emit(self, state: _ProgramState):
        state.proto.add_opcode("return")


@dataclass
class FuncCall(Ast, Statement, Expression, MultiresExpression):
    primary: Expression
    params: list[Expression] | String = None  # TODO: table constructors

    def emit(self, state: _ProgramState):
        self.evaluate(state, 0)

    def evaluate(self, state: _ProgramState, *args, **kwargs):
        self.primary.evaluate(state)

        return_count: int = 1
        if args:
            if not isinstance(args[0], int):
                raise InternalCompilerError("Illegal function call: illegal return count.")
            return_count = args[0]

        param_count: int = 0
        if self.params:
            if isinstance(self.params, list):
                param_count = len(self.params)
                expr: Expression
                for expr in self.params:
                    expr.evaluate(state)
            elif isinstance(self.params, String):
                param_count = 1
                self.params.evaluate(state)
            else:
                raise InternalCompilerError("Illegal function call: illegal type of parameters.")

        state.proto.add_opcode(f"call {param_count} {return_count}")


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

        body = self.block.emit(state)
        proto.add_opcode(f"jump {start - proto.pc}")
        block_end = proto.pc

        proto.opcodes[jump_pc] = f"jump {block_end - jump_pc}"
        for br in body.breaks:
            proto.opcodes[br] = f"jump {block_end - br}"


@dataclass
class RepeatStmt(Ast, Statement):
    block: Block
    expr: Expression

    def emit(self, state: _ProgramState):
        block = _BlockState()
        state.proto.blocks.append(block)

        start = state.proto.pc
        for st in self.block.statements:
            st.emit(state)
        self.expr.evaluate(state)
        state.proto.add_opcode("test")
        end = state.proto.pc
        state.proto.add_opcode(f"jump {start - end}")

        state.proto.blocks.pop()


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
        self.elze: Block | None = None
        for i in range(2, len(children)):
            c = children[i]
            if isinstance(c, ElseIf):
                self.elseifs.append(c)
            elif isinstance(c, Block):
                if not self.elze:
                    self.elze = c
                else:
                    raise InternalCompilerError("Illegal 'if' statement: 'else' block already exists.")
            else:
                raise InternalCompilerError("Illegal 'if' statement: illegal child node type.")

    def emit(self, state: _ProgramState):
        proto = state.proto

        skip_end_jump = not self.elze and len(self.elseifs) == 0
        self._emit_branch(state, self.condition, self.block, skip_end_jump)
        for i, el in enumerate(self.elseifs):
            self._emit_branch(state, el.condition, el.block, i == len(self.elseifs) - 1)
        if self.elze:
            self.elze.emit(state)

        for jump in self.end_jumps:  # TODO: remove "jump 1" when "else" block is missing
            proto.opcodes[jump] = f"jump {proto.pc - jump}"

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
        block.emit(state)
        if not skip_end_jump:
            self.end_jumps.append(proto.pc)
            proto.add_opcode(None)
        proto.opcodes[jump_pc] = f"jump {proto.pc - jump_pc}"


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
