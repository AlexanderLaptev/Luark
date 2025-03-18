from luark.compiler import Compiler

compiler = Compiler(debug=True)
compiler.compile_file("tests/script.lua")
