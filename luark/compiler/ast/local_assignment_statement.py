from dataclasses import dataclass

from luark.compiler.ast.constants import NilValue
from luark.compiler.ast.expressions import CompileTimeConstant, ExpressionList
from luark.compiler.ast.statement import Statement
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import CompilationError
from luark.opcode.local import MarkTBC, StoreLocal


@dataclass
class AttributedName:
    name: str
    attribute: str


@dataclass
class LocalAssignmentStatement(Statement):
    attributed_names: list[AttributedName]
    expression_list: ExpressionList | None

    def compile(self, state: CompilerState) -> None:
        expressions: list = []
        if self.expression_list:
            expressions.extend(self.expression_list.expressions)
        tbc_index: int | None = None

        variables: list[int] = []
        runtime_consts: list[int] = []
        compile_time_consts: list[int] = []

        # Process attributes
        for i in range(len(self.attributed_names)):
            attribute = self.attributed_names[i].attribute
            match attribute:
                case None | "close":  # variable
                    variables.append(i)
                    if attribute == "close":  # TBC variable
                        if tbc_index is not None:
                            raise CompilationError("local var list already contains a to-be-closed variable", self.meta)
                        tbc_index = i
                case "const":  # compile or runtime const
                    if i < len(expressions):  # if there's an expression given for this name
                        expression = expressions[i]
                        if isinstance(expression, CompileTimeConstant):
                            compile_time_consts.append(i)
                        else:
                            variables.append(i)
                            runtime_consts.append(i)
                    else:
                        compile_time_consts.append(i)
                case _:  # something else (illegal)
                    raise CompilationError(f"unknown attribute: <{attribute}>", self.meta)

        # Handle compile time consts
        for i in compile_time_consts:
            # Use the provided value if it exists, or use nil otherwise
            expression: CompileTimeConstant
            if i < len(expressions):
                expression = expressions[i]
            else:
                expression = NilValue.INSTANCE
            name = self.attributed_names[i].name

            state.add_const_local(name, expression)
            if i < len(expressions):  # mark expression for exclusion later
                expressions[i] = None

        # Filter out compile time consts from the expression list
        expressions = [x for x in expressions if (x is not None)]
        ExpressionList(expressions).evaluate(state, len(variables))

        # Assign values
        for i in variables:
            name = self.attributed_names[i].name
            var = state.new_local(name)
            state.add_opcode(StoreLocal(var.index))

            if i in runtime_consts:
                var.is_const = True

        # Mark TBC
        if tbc_index is not None:
            state.add_opcode(MarkTBC(tbc_index))
