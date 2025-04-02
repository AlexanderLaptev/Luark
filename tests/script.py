import sys

from luark.compiler.compiler import Compiler
from luark.compiler.exceptions import CompilationError

compiler = Compiler(debug=True)
try:
    program = compiler.compile_file("./script.lua")
except CompilationError as e:
    print(*e.args, file=sys.stderr)
