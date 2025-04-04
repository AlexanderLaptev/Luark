-- foo = function () end
-- foo = function (a) end
-- foo = function (a, b) end
-- foo = function (a, b, ...) end
-- foo = function (...) end

-- function foo() end
-- function foo(a) end
-- function foo(a, b) end
-- function foo(a, b, ...) end
-- function foo(...) end

-- function a.b() end
-- function a.b.c() end
-- function a.b.c(foo, bar, ...) end

-- function a:b() end
-- function a:b(x, y) end
-- function a:b(x, y, ...) end

function a.b.c:d(x, y, z, ...) end
