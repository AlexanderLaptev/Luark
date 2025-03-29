---[[
local x = 1
do
    x = 2
    local x = 10
    x = 15
end
x = 3
--]]
