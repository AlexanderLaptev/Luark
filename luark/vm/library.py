from typing import Callable, TYPE_CHECKING

from luark.vm.exception import TypeException
from luark.vm.types import Table, String, NativeFunction, AnyType, Nil, Boolean, Integer, Float, Function

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


@library.register('print')  # name in lua-code
def print_function(program_runner, prototype_runner) -> None:
    value = program_runner.value_stack.pop()
    print(str(value))


@library.register('type')
def type_function(program_runner, prototype_runner) -> None:
    value: AnyType = program_runner.value_stack.pop()
    type_name: str

    if isinstance(value, Nil):
        type_name = "nil"
    elif isinstance(value, Boolean):
        type_name = "boolean"
    elif isinstance(value, (Integer, Float)):
        type_name = "number"
    elif isinstance(value, String):
        type_name = "string"
    elif isinstance(value, Table):
        type_name = "table"
    elif isinstance(value, (Function, NativeFunction)):
        type_name = "function"
    else:
        error_message = f"Object of unknown type '{type(value).__name__}' passed to 'type' function"
        raise TypeException(prototype_runner, error_message)

    program_runner.value_stack.append(String(type_name.encode('utf-8', errors='replace')))
