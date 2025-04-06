-- local a = {}
-- local a = { 1 }
-- local a = { 1, "a", true }
-- local a = { 1, "a", true, foo() }
-- local a = { 1, "a", true, (foo()) }

-- local a = { foo = 1, bar = 2, "x", "y", baz = 3, "z" }
local a = { foo = 1, [1] = bar, ["baz"] = foo() }
