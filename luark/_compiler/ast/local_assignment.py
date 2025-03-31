from dataclasses import dataclass

from lark.ast_utils import Ast

from luark.compiler.ast.expressions import Expression, ConstExpr, NilValue
from luark.compiler.ast.expr_list_utils import adjust_static
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.ast.statement import Statement
from luark.compiler.errors import CompilationError


class AttribName(Ast):
    def __init__(self, name: str, attribute: str | None = None):
        self.name = name
        self.attribute = attribute


@dataclass
class LocalAssignStmt(Ast, Statement):
    attr_names: list[AttribName]
    exprs: list[Expression]

    def emit(self, state: _ProgramState):
        proto = state.proto
        block = proto.block
        exprs: list[Expression | None] = self.exprs.copy() if self.exprs else []
        tbc_index: int | None = None

        variables: list[int] = []
        runtime_consts: list[int] = []
        compile_time_consts: list[int] = []

        # Process attributes.
        for i in range(len(self.attr_names)):
            attr = self.attr_names[i].attribute
            match attr:
                case None | "close":  # variable
                    variables.append(i)
                    if attr == "close":  # TBC variable
                        if tbc_index is not None:
                            raise CompilationError("Multiple to-be-closed vars in a single var list.")
                        tbc_index = i
                case "const":  # compile or runtime const
                    if i < len(exprs):  # if there's an expression given for this name
                        expr = exprs[i]
                        if isinstance(expr, ConstExpr):
                            # noinspection PyTypeChecker
                            compile_time_consts.append(i)
                        else:
                            variables.append(i)
                            runtime_consts.append(i)
                    else:
                        compile_time_consts.append(i)
                case _:  # something else (illegal)
                    raise CompilationError(f"Unknown attribute <{attr}>.")

        # Handle compile time consts.
        for i in compile_time_consts:
            # Use the provided value if it exists, or use nil otherwise.
            expr = exprs[i] if (i < len(exprs)) else NilValue.instance
            name = self.attr_names[i].name

            block.const_locals[name] = expr
            if i < len(exprs):  # mark expression for exclusion later
                exprs[i] = None

        # Filter out compile time consts from the expression list.
        exprs: list[Expression] = [x for x in exprs if (x is not None)]
        if exprs:
            adjust_static(state, len(variables), exprs)

        # Assign values.
        for i in variables:
            name = self.attr_names[i].name
            index = proto.get_local_index(name)
            proto.add_opcode(f"store_local {index}")

            if i in runtime_consts:
                var = proto.get_local(index)
                var.is_const = True

        # Mark TBC.
        if tbc_index is not None:
            proto.add_opcode(f"mark_tbc {tbc_index}")
