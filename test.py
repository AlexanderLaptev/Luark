import time
import os
import compiler

compiler = compiler.LuaCompiler()

path = "lua-5.4.7-tests"
files = os.listdir(path)
failed = 0
start = time.time()
for file in files:
    full_path = os.path.join(path, file)
    with open(full_path) as source_file:
        source = source_file.read()
        try:
            compiler.compile(source)
            break
        except Exception as e:
            failed += 1
            print(f'{file} - FAIL: {str(e)}')
end = time.time()

total = len(files)
percent = int(round(failed / total * 100, 2))
print(f'Done - {failed} ({percent}%) failed out of {len(files)} ({round((end - start) * 1000)} ms)')
