# Bytecode
- collapse `push_false+test` and `push_true+test`
- consecutive jumps (a constant jump to a constant jump, optimize in multiple passes)
- multiple consecutive returns

# AST
- if statement with a single else block (`if cond then ; else foo() end`)
- `or true`, `and false`
 