from dataclasses import dataclass

from lark import Token
from lark.tree import Meta

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import CompilationError, InternalCompilerError

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


def parse_string(meta: Meta, source: str) -> bytes:
    string = source[1:-1]  # strip quotes

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
                if c in ESCAPE_SEQUENCES:
                    out_bytes.append(ESCAPE_SEQUENCES[c])
                    i += 1
                else:
                    i += 1  # after sequence char
                    if c == "x":
                        value = int(string[i:i + 2], 16)
                        out_bytes.append(
                            value.to_bytes(1, byteorder="big", signed=False)
                        )
                    elif c == "u":
                        if string[i] != "{":
                            raise CompilationError
                        i += 1  # first inside braces

                        brace = string.find("}", i)
                        if brace < 0:
                            raise CompilationError

                        value = int(string[i:brace])
                        if value >= 2 ** 31:
                            raise CompilationError

                        byte_size = (value.bit_length() + 7) // 8
                        out_bytes.append(
                            value.to_bytes(
                                byte_size,
                                byteorder="big",
                                signed=False
                            )
                        )
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
                            raise CompilationError

                        out_bytes.append(
                            value.to_bytes(1, byteorder="big", signed=False)
                        )
            else:
                out_bytes.append(c.encode("utf-8"))
                i += 1
    except Exception:
        raise CompilationError(
            f"Illegal string literal (line {meta.line}): '{string}'."
        )

    return b"".join(out_bytes)


def parse_multistring(source: str) -> bytes:
    size = source.find("[", 1) + 1
    return source[size:-size].removeprefix("\n").encode("utf-8")


@dataclass
class String(CompileTimeConstant):
    meta: Meta
    value: bytes

    def __init__(self, meta: Meta, token: Token):
        self.meta = meta
        if token.type == "STRING":
            self.value = parse_string(token)
        elif token.type == "MULTISTRING":
            self.value = parse_multistring(token)
        else:
            raise InternalCompilerError(
                f"Illegal string literal token: {token.type}."
            )

    def evaluate(self, state: CompilerState) -> None:
        pass
        # index = state.get_const_index(self.value)
