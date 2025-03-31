import os
import traceback

from luark.compiler import Compiler

compiler = Compiler()

TEST_DIR = "lua-5.4.7-tests"

with open("REPORT.txt", "w") as report:
    failed = 0
    tests = os.listdir(TEST_DIR)
    for test in tests:
        file_path = os.path.join(TEST_DIR, test)
        # noinspection PyBroadException
        try:
            report.write("\n==========================\n\n")
            report.write(f">> Compiling '{test}'...\n")
            compiler.compile_file(file_path)
        except Exception as e:
            report.write(f"'{test}' errored out!\n\n")
            report.write(traceback.format_exc())
            report.write("\n")
            failed += 1
        else:
            report.write("Success!\n")

    total = len(tests)
    successful = total - failed
    message = f"Compiled {successful} tests out of {total} ({failed} failed).\n"
    report.write(message)
    print(message)
