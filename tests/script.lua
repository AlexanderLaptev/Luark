#! /usr/bin/env luac

function foo(x, y, ...)
    local a1 = function (xyzzy) print(xyzzy) end
    local a2 = 1 + 2 * 5 > 3.0 * .5 / 2.
    a("hello" .. "world")
    bar(x)
    baz(y)
    qux(y, ...)

    var1 = 2
    while var1 < 1000 do
        foo(var1 * 2)
        var1 = var1 / 2
    end

    expr = bar(x) // baz(y)
    repeat
        expr = expr % 7
    until test(expr)

    g1, g2.key, g3["value"] = bar(1), bar("a"), bar(2 + 2, baz("test"))
    return "return"
end

return 1, a(), b()
