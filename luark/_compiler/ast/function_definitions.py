from dataclasses import dataclass

from lark.ast_utils import Ast, AsList

from luark.compiler.ast.assignment import AssignStmt
from luark.compiler.ast.block import Block
from luark.compiler.ast.expressions import Varargs, Expression, MultiresExpression
from luark.compiler.ast.expr_list_utils import evaluate_single
from luark.compiler.ast.local_assignment import LocalAssignStmt, AttribName
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.ast.statement import Statement
from luark.compiler.ast.variables import Var, DotAccess
from luark.compiler.errors import InternalCompilerError, CompilationError


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
        if not body.statements or not isinstance(body.statements[-1], ReturnStmt):
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
        if state.proto:
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
        exprs = self.exprs[::-1] if self.exprs else []
        if exprs:
            for i in range(len(exprs) - 1):
                expr = exprs[i]
                evaluate_single(state, expr)

            last = exprs[-1]
            if isinstance(last, MultiresExpression):
                last.evaluate(state, 0)
                state.proto.add_opcode("return 0")
            else:
                evaluate_single(state, last)
                state.proto.add_opcode(f"return {1 + len(exprs)}")
        else:
            state.proto.add_opcode("return 1")
