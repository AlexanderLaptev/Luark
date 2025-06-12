-- function foo() return end
-- function foo() return 1 end
-- function foo() return 1, 2, 3 end
-- function foo() return 1, 2, ... end
-- function foo() return 1, 2, (...) end
-- function foo() return 1, 2, ...,  3 end
function foo() return 1, 2, bar() end
