
local foo = function(a)
    print(a, 1)
    --return (a + b)
end

foo("string to print", 2)

-- a = 1
-- a = 1, 2
-- a = ...
-- a = foo()

-- a, b = 1
-- a, b = 1, 2
-- a, b = 1, 2, 3, 4
-- a, b = ...
-- a, b = foo()
-- a, b = (...)
-- a, b = ..., ...
-- a, b = 1, (...)
-- a, b = 1, (foo())
-- a, b = b, a

-- i, a[i] = i+1, 20

