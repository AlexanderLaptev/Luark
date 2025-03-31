from luark.compiler import Compiler

compiler = Compiler(debug=True)
compiler.compile_file("lua-5.4.7-tests/attrib.lua")
# compiler.compile_file("script.lua")
