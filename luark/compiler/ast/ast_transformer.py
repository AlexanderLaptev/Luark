from lark import Discard, v_args

from luark.compiler.ast import Chunk, FunctionName, ParameterList, Varargs
from luark.compiler.ast.constants import FalseValue, NilValue, TrueValue
from luark.compiler.ast.expression_transformer import ExpressionTransformer
from luark.compiler.ast.local_assignment_statement import AttributedName
from luark.compiler.ast.variable import Variable
from luark.compiler.exceptions import InternalCompilerError


# noinspection PyPep8Naming
@v_args(inline=True)
class AstTransformer(ExpressionTransformer):
    def start(self, chunk: Chunk):
        return chunk

    # noinspection PyShadowingBuiltins
    @v_args(meta=False, inline=False)
    def var_list(self, vars: list[Variable]) -> list[Variable]:
        return vars

    def true(self) -> TrueValue:
        return TrueValue.INSTANCE

    def false(self) -> FalseValue:
        return FalseValue.INSTANCE

    def nil(self) -> NilValue:
        return NilValue.INSTANCE

    def empty_statement(self) -> Discard:
        return Discard

    @v_args(inline=False)
    def attributed_name_list(
            self,
            names: list[AttributedName]
    ) -> list[AttributedName]:
        return names

    @v_args(inline=False)
    def function_name(self, names: list[str]) -> FunctionName:
        return FunctionName(names, is_method=False)

    @v_args(inline=False)
    def method_name(self, names: list[str]) -> FunctionName:
        return FunctionName(names, is_method=True)

    @v_args(inline=False)
    def parameter_list(self, children: list) -> ParameterList:
        names = []
        has_varargs = False
        for child in children:
            if isinstance(child, str):
                names.append(child)
            elif isinstance(child, Varargs):
                if has_varargs:
                    raise InternalCompilerError("extra varargs in parameter list")
                has_varargs = True
            else:
                raise InternalCompilerError(f"illegal type in parameter list: {type(child)}")
        return ParameterList(names, has_varargs)

    def DECIMAL_INT(self, number: str) -> int:
        return int(number, 10)

    def DECIMAL_FLOAT(self, number: str) -> float:
        return float(number)

    def HEX_INT(self, number: str) -> int:
        number = number.casefold()
        left, *(right) = number.split("p")
        result = int(left, 16)
        if right:
            exponent = int(right, 10)
            result *= 2 ** exponent
        return result

    def HEX_FLOAT(self, number: str) -> float:
        return float.fromhex(number)

    # noinspection PyShadowingBuiltins
    def ID(self, id: str) -> str:
        return str(id)
