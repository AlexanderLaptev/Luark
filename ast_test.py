import compiler

compiler = compiler.LuaCompiler(debug=True)
compiler.compile_file("script.lua")
