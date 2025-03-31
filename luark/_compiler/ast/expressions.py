import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeAlias

from lark.ast_utils import Ast, WithMeta
from lark.tree import Meta

from luark.compiler.ast.expr_list_utils import evaluate_single
from luark.compiler.ast.program_state import _ProgramState
from luark.compiler.errors import CompilationError


class Expression(ABC):
    @abstractmethod
    def evaluate(self, state: _ProgramState):
        pass


class MultiresExpression(ABC):
    @abstractmethod
    def evaluate(self, state: _ProgramState, return_count: int):
        pass


@dataclass
class String(Ast, WithMeta, Expression):
    ESCAPE_SEQUENCES = {
        "a": b"\a",
        "b": b"\b",
        "f": b"\f",
        "n": b"\n",
        "r": b"\r",
        "t": b"\t",
        "v": b"\v",
        "\\": b"\\",
        "\"": b"\"",
        "\'": b"\'",
        "\n": b"\n",
    }

    meta: Meta
    value: str

    def evaluate(self, state: _ProgramState):
        index = state.proto.get_const_index(self.value)
        state.proto.add_opcode(f"push_const {index}")

    def _parse_string(self, string: str) -> bytes:
        string = string[1:-1]  # strip quotes

        lines = string.split("\\z")
        for i in range(1, len(lines)):
            lines[i] = lines[i].lstrip()
        string = "".join(lines)

        # noinspection PyBroadException
        try:
            out_bytes = []
            i = 0  # first char
            while i < len(string):
                c = string[i]
                if c == "\\":
                    i += 1  # after slash
                    c = string[i]
                    if c in self.ESCAPE_SEQUENCES:
                        out_bytes.append(self.ESCAPE_SEQUENCES[c])
                        i += 1
                    else:
                        i += 1  # after sequence char
                        if c == "x":
                            value = int(string[i:i + 2], 16)
                            out_bytes.append(value.to_bytes(1, byteorder="big", signed=False))
                        elif c == "u":
                            if string[i] != "{":
                                raise CompilationError()
                            i += 1  # first inside braces

                            brace = string.find("}", i)
                            if brace < 0:
                                raise CompilationError()

                            value = int(string[i:brace])
                            if value >= 2 ** 31:
                                raise CompilationError()

                            byte_size = (value.bit_length() + 7) // 8
                            out_bytes.append(value.to_bytes(byte_size, byteorder="big", signed=False))
                        elif str.isdigit(c):
                            left = i - 1
                            size = 1
                            for j in range(2):
                                if (i + j) >= len(string):
                                    break
                                if str.isdigit(string[i + j]):
                                    size += 1
                                else:
                                    break

                            value = int(string[left:left + size], 10)
                            if not 0 <= value <= 255:
                                raise CompilationError()

                            out_bytes.append(value.to_bytes(1, byteorder="big", signed=False))
                else:
                    out_bytes.append(c.encode("utf-8"))
                    i += 1
        except Exception:
            raise CompilationError(f"Illegal string literal (line {self.meta.line}): '{string}'.")

        return b"".join(out_bytes)


@dataclass
class Multistring(String):
    def _parse_string(self, string: str) -> bytes:
        multistr = str(self.value)
        size = multistr.find("[", 1) + 1
        return multistr[size:-size].removeprefix("\n").encode("utf-8")


@dataclass
class Number(Ast, Expression):
    value: int | float

    def evaluate(self, state: _ProgramState):
        if isinstance(self.value, int):
            state.proto.add_opcode(f"push_int {self.value}")
        elif isinstance(self.value, float):
            if math.isinf(self.value) or math.isnan(self.value):
                index = state.proto.get_const_index(self.value)
                state.proto.add_opcode(f"push_const {index}")
                return

            frac = self.value - int(self.value)
            if frac == 0.0:
                state.proto.add_opcode(f"push_float {int(self.value)}")
            else:
                index = state.proto.get_const_index(self.value)
                state.proto.add_opcode(f"push_const {index}")


class NilValue(Expression):
    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode("push_nil")


class TrueValue(Expression):
    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode("push_true")


class FalseValue(Expression):
    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode("push_false")


@dataclass
class BinaryOpExpression(Expression):
    opcode: str
    left: Expression
    right: Expression

    def evaluate(self, state: _ProgramState):
        evaluate_single(state, self.left)
        evaluate_single(state, self.right)
        state.proto.add_opcode(self.opcode)


@dataclass
class UnaryExpression(Expression):
    opcode: str

    def evaluate(self, state: _ProgramState):
        state.proto.add_opcode(self.opcode)


class Varargs(Ast, MultiresExpression):
    def evaluate(self, state: _ProgramState, return_count: int):
        if not state.proto.is_variadic:
            raise CompilationError("Cannot access varargs from a non-variadic function.")
        state.proto.add_opcode(f"get_varargs {return_count}")


NilValue.instance = NilValue()
TrueValue.instance = TrueValue()
FalseValue.instance = FalseValue()
ConstExpr: TypeAlias = String | Number | NilValue | TrueValue | FalseValue


@dataclass
class Primary(Ast, Expression):
    child: Expression

    def evaluate(self, state: _ProgramState):
        evaluate_single(state, self.child)
