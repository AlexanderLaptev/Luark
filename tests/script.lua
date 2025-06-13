local function foo(a, b, ...)
    x = a
    y = b * ...
end

foo(1, 2, 3, 4, 5)
print(x)
print(y)