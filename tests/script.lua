--[[
repeat
    while foo() do
        baz()
    end
until bar()
--]]

--[[
for i = 1, 2, 3 do
    foo()
end
--]]

for a, b, c in foo(), bar() do
    bar()
end
