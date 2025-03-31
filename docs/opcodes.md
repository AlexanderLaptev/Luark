Format: `<name> <arg 1> ... <arg N>: (<pop list>) -> (<push list>)`.  
Lists are bottom-to-top (leftmost is at the bottom of the stack).

- `pop: (value) -> ()` &mdash; pops a value from the stack.


- `push_const <K>: () -> (const)` &mdash; pushes a constant with the index `K` onto the stack.
- `push_int <N>: () -> (N)` &mdash; pushes an integer `N` onto the stack.
- `push_float <F>: () -> (F)` &mdash; pushes an integer `F` as a float onto the stack (e.g. `push_float 5` pushes `5.0`).
- `push_true: () -> (true)` &mdash; pushes the value `true` onto the stack.
- `push_false: () -> (false)` &mdash; pushes the value `false` onto the stack.
- `push_nil: () -> (nil)` &mdash; pushes the value `nil` onto the stack.


- `load_local <L>: () -> (value)` &mdash; pushes the value of the local with the index `L`.
- `store_local <L>: (value) -> ()` &mdash; pops the value from the stack and stores it into the local with the index `L`.
- `get_upvalue <U>: () -> (upvalue)` &mdash; pushes the upvalue with the index `U`.


- `new_table: () -> (table)` &mdash; creates a new table and pushes it onto the stack.
- `get_table: (table, key) -> (value)` &mdash; gets the value with the given key in the given table and pushes the result onto the stack.
- `set_table: (value, table, key) -> ()` &mdash; stores the given value in the given table with the given key.
- `store_list <N>: (table, value 1, ..., value N) -> ()` &mdash; stores `N` values in the given table consecutively.
