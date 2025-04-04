function foo()
    local x = 0
    function bar()
        function baz()
            x = x + 1
        end
        return baz
    end
    return bar
end
