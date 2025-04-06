# Features
- Closing of upvalues
- Improve error reporting
- Lazy evaluation
- Ensure correct expression list evaluation order (return, call, vararg, table constructors)
  - Return statements
  - Function calls
  - Varargs
  - Table constructors
  - For loops

# Testing
- Write custom tests
- Write code to run custom tests

# Potential bugs
- Goto statements
- Releasing locals

# Refactors
- Figure out assertions and `InternalCompilerError`s
- Use `block.compile()` now that it's available
- Use proper singletons
- Use OOP instead of `isinstance()` checks where possible

# Optimizations
- Optimize `if not <cond> then <block> else <block> end` by swapping blocks
- Use a single `store_list` opcode for storing multiple contiguous expressions in a table
