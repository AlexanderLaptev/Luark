-- rightfully stolen from https://gist.github.com/hoffoo/b420d1ecc60ad6ec44e5
local array = { 5, 3, 3, 4, 1, 2, 2 }

function swap(a, b, table)
    if table[a] == nil or table[b] == nil then
        return false
    end

    if table[a] > table[b] then
        table[a], table[b] = table[b], table[a]
        return true
    end

    return false
end

function bubblesort(array)
    for i = 1, #array do
        local ci = i
        ::redo::
        if swap(ci, ci + 1, array) then
            ci = ci - 1
            goto redo
        end
    end
end

print("bubblesorting!")
bubblesort(array)
for i = 1, #array do
    print(array[i])
end
print("finished bubblesorting!")
print()

print(1, 2, 3)
print(tonumber("5")*2)
local result = 2 * 5
print(result, #tostring(result))
print("we can ".."concat".." strings and".." more: "..result..", "..(2*3>7))


function factorial(n)
    if n <= 1 then do return 1 end end
    return n * factorial(n - 1) -- no tailrec optimization sadly (yet) :(
end
print(factorial(5))
