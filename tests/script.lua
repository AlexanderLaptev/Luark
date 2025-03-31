local function foo() return 2, 3 end
local a, b, c = 1, foo()
print(a, b, c)
