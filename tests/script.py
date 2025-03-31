from luark.compiler.compiler import Compiler

compiler = Compiler(debug=True)
program = compiler.compile_file("./script.lua")
