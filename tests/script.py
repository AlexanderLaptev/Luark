import sys

from luark.compiler.compiler import Compiler
from luark.compiler.exceptions import CompilationError

compiler = Compiler(debug=True)
try:
    program = compiler.compile_file("./script.lua")
except CompilationError:
    print("! Compilation error.", file=sys.stderr)
