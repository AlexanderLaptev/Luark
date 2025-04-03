from lark import Token
from lark.tree import Meta

from luark.compiler.ast.expressions import CompileTimeConstant
from luark.compiler.compiler_state import CompilerState
from luark.compiler.exceptions import CompilationError, InternalCompilerError
from luark.opcode.push import PushConst

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


def parse_string(source: str) -> bytes:
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
                i += 1  # consume slash
                c = string[i]
                if c in ESCAPE_SEQUENCES:
                    out_bytes.append(ESCAPE_SEQUENCES[c])
                    i += 1
                else:
                    if c == "x":
                        i += 1  # consume x
                        value = int(string[i:i + 2], 16)
                        out_bytes.append(value.to_bytes(1, signed=False))
                        i += 2  # consume 2 hex digits
                    elif c == "u":
                        i += 1  # consume u
                        if string[i] != "{":
                            raise CompilationError("expected '{' after \\u")
                        i += 1  # consume {

                        brace = string.find("}", i)
                        if brace < 0:
                            raise CompilationError("unclosed unicode code point escape literal")

                        value = int(string[i:brace], 16)
                        if value >= 2 ** 31:
                            raise CompilationError("code point value must be less than 2^31")

                        byte_size = (value.bit_length() + 7) // 8
                        out_bytes.append(value.to_bytes(byte_size, byteorder="big"))
                        i = brace  # consume code point with braces
                    elif str.isdigit(c):
                        size = 1
                        for j in range(1, 2):
                            if (i + j) >= len(string):
                                break
                            if str.isdigit(string[i + j]):
                                size += 1
                            else:
                                break

                        value = int(string[i:i + size], 10)
                        if not 0 <= value <= 255:
                            raise CompilationError("byte value must be between 0 and 255")

                        out_bytes.append(value.to_bytes())
                        i += size  # consume byte value
                    else:
                        raise CompilationError(f"unknown escape sequence '{string[i - 1:i + 1]}'")
            elif c == "\n":
                raise CompilationError("unfinished string")
            else:
                out_bytes.append(c.encode("utf-8"))
                i += 1  # consume character
    except CompilationError:
        raise
    except Exception:
        raise CompilationError(f"malformed string literal: {string}")

    return b"".join(out_bytes)


def parse_multistring(source: str) -> bytes:
    size = source.find("[", 1) + 1
    return source[size:-size].removeprefix("\n").encode("utf-8")


class String(CompileTimeConstant):
    value: bytes

    def __init__(self, meta: Meta, arg: Token | str | bytes):
        self.meta = meta

        if isinstance(arg, Token):
            if arg.type == "STRING":
                self.value = parse_string(arg)
            elif arg.type == "MULTISTRING":
                self.value = parse_multistring(arg)
            else:
                raise InternalCompilerError(f"illegal token type '{arg.type}' for string: {arg}")
            return

        if isinstance(arg, str):
            arg = arg.encode("utf-8")

        assert isinstance(arg, bytes)
        self.value = arg

    def evaluate(self, state: CompilerState) -> None:
        index = state.get_const_index(self.value)
        state.add_opcode(PushConst(index))
