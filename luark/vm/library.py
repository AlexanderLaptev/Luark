from __future__ import annotations

import typing
from typing import Callable

from luark.vm.types import NativeFunction, String, Table

if typing.TYPE_CHECKING:
    from luark.vm.luavm import ProgramRunner, PrototypeRunner


class Library:

    def __init__(self):
        self._function_table: Table = Table()

    def register(self, name: str = None):
        def add_function(func: Callable[..., None]) -> Callable[..., None]:
            function_name: bytes = name.encode('utf-8', errors='replace') if name is not None else func.__name__
            self._function_table.set(String(function_name), NativeFunction(func))
            return func

        return add_function

    def get_table(self) -> Table:
        return self._function_table


library = Library()

""" 
Это пример созданной библиотеки нативных функций. объект library используется в script.py для создания тестов.
Каждая функция должна обладать аргументами типа [ProgramRunner, PrototypeRunner] и ничего не возвращать
Взаимодействие с данными внутри программы осуществляется через взаимодействие со стеком значений `pr.value_stack.pop()`
Доступные типы, используемые в стеке значений описаны в vm/types.py

Виртуальная машина после завершения функции автоматически икрементирует счетчик команд (PrototypeRunner.program_counter)
"""


@library.register('print')  # name in Lua code
def print_function(program_runner: ProgramRunner, prototype_runner: PrototypeRunner) -> None:
    count = len(program_runner.value_stack) - program_runner.peek_mark()
    for value in reversed(program_runner.value_stack[-count:]):
        print(str(value))
    # value = program_runner.value_stack.pop()
    # print(str(value))
