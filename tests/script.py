import sys

from luark.compiler.compiler import Compiler
from luark.compiler.exceptions import CompilationError

try:
    compiler = Compiler(debug="code")
    program = compiler.compile_file("./lua-5.4.7-tests/api.lua")
    # program = compiler.compile_file("./script.lua")
    pass
except CompilationError as e:
    print(*e.args, file=sys.stderr)
