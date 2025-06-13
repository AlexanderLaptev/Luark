import sys

from luark.compiler.compiler import Compiler
from luark.compiler.exceptions import CompilationError
from luark.vm.exception import BaseRuntimeException, DefaultError
from luark.vm.library import library
from luark.vm.luavm import LuaVM

try:
    compiler = Compiler(debug="code")
    # program = compiler.compile_file("./lua-5.4.7-tests/api.lua")
    program = compiler.compile_file("./script.lua")
    vm = LuaVM(program, library=library)
    vm.loop()
    pass
except CompilationError as e:
    print(*e.args, file=sys.stderr)
except BaseRuntimeException as e:
    print(e.message, e.prototype_name, e.program_counter)
except DefaultError as e:
    print(e.message)
