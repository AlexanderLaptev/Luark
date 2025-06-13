import math
from typing import Callable

from luark.vm.exception import TypeException, DefaultError
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


@library.register('error')
def error_function(program_runner, prototype_runner) -> None:
    message: AnyType = program_runner.value_stack.pop()
    error_message: str
    if isinstance(message, String):
        error_message = message.value.decode('utf-8', errors='replace')
    else:
        error_message = str(message)

    raise DefaultError(message=error_message)


def _math_unary_operation(program_runner, prototype_runner, math_function, function_name: str):
    epsilon = 1e-15
    arg_luark: AnyType = program_runner.value_stack.pop()

    if not isinstance(arg_luark, (Integer, Float)):
        raise TypeException(
            prototype_runner,
            f"bad argument to '{function_name}' (number expected, got {type(arg_luark).__name__})")

    arg: float = float(arg_luark.value)
    try:
        result_py: float = math_function(arg)
        if abs(result_py) < epsilon:
            result_py = 0.
    except ValueError as e:
        raise DefaultError(f"bad argument to '{function_name}' ({str(e)})")
    except ZeroDivisionError as e:
        raise DefaultError(f"bad argument to '{function_name}' (division by zero: {str(e)})")
    program_runner.value_stack.append(Float(result_py))


@library.register('sin')
def sin_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.sin, 'sin')


@library.register('cos')
def cos_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.cos, 'cos')


@library.register('tan')
def tan_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.tan, 'tan')


@library.register('cot')
def cot_function(program_runner, prototype_runner) -> None:
    def cot_impl(x):
        return 1.0 / math.tan(x)

    _math_unary_operation(program_runner, prototype_runner, cot_impl, 'cot')


@library.register('ceil')
def ceil_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.ceil, 'ceil')


@library.register('floor')
def floor_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.floor, 'floor')


@library.register('abs')
def abs_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.fabs, 'abs')


@library.register('sqrt')
def sqrt_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.sqrt, 'sqrt')


@library.register('exp')
def exp_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.exp, 'exp')


@library.register('log')
def log_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.log, 'log')


@library.register('deg')
def deg_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.degrees, 'deg')


@library.register('rad')
def rad_function(program_runner, prototype_runner) -> None:
    _math_unary_operation(program_runner, prototype_runner, math.radians, 'rad')


@library.register('find')
def find_function(program_runner, prototype_runner) -> None:
    input_str: AnyType = program_runner.value_stack.pop()
    input_substr: AnyType = program_runner.value_stack.pop()

    if not isinstance(input_substr, String):
        raise TypeException(prototype_runner, "bad argument to 'find' (string expected)")
    if not isinstance(input_str, String):
        raise TypeException(prototype_runner, "bad argument to 'find' (string expected)")

    str_py: input_str = input_str.value.decode('utf-8', errors='replace')
    substr_py: input_str = input_substr.value.decode('utf-8', errors='replace')

    index_py: int = str_py.find(substr_py)
    if index_py == -1:
        program_runner.value_stack.append(Nil())
    else:
        program_runner.value_stack.append(Integer(index_py + 1))


@library.register('lower')
def lower_function(program_runner, prototype_runner) -> None:
    input_str: AnyType = program_runner.value_stack.pop()

    if not isinstance(input_str, String):
        raise TypeException(prototype_runner, "bad argument to 'lower' (string expected)")

    str_py: str = input_str.value.decode('utf-8', errors='replace')
    program_runner.value_stack.append(String(str_py.lower().encode('utf-8')))


@library.register('upper')
def lower_function(program_runner, prototype_runner) -> None:
    input_str: AnyType = program_runner.value_stack.pop()

    if not isinstance(input_str, String):
        raise TypeException(prototype_runner, "bad argument to 'upper' (string expected)")

    str_py: str = input_str.value.decode('utf-8', errors='replace')
    program_runner.value_stack.append(String(str_py.upper().encode('utf-8')))


@library.register('substring')
def substring_function(program_runner, prototype_runner) -> None:
    input_str: AnyType = program_runner.value_stack.pop()
    from_idx: AnyType = program_runner.value_stack.pop()
    to_idx: AnyType = program_runner.value_stack.pop()

    if not isinstance(input_str, String):
        raise TypeException(prototype_runner, "bad argument #1 to 'substring' (string expected)")
    if not isinstance(from_idx, Integer):
        raise TypeException(prototype_runner, "bad argument #2 to 'substring' (number/integer expected)")
    if not isinstance(to_idx, Integer):
        raise TypeException(prototype_runner, "bad argument #3 to 'substring' (number/integer expected)")

    str_py: str = input_str.value.decode('utf-8', errors='replace')
    str_len: int = len(str_py)
    from_idx_py: int = from_idx.value
    to_idx_py: int = to_idx.value

    if from_idx_py > 0:
        from_idx_py = from_idx_py - 1

    result_str_py: str
    if from_idx_py >= str_len or to_idx_py <= 0 or from_idx_py >= to_idx_py:
        result_str_py = ""
    else:
        final_py_start = max(0, from_idx_py)
        final_py_end = min(str_len, to_idx_py)
        result_str_py = str_py[final_py_start:final_py_end]

    program_runner.value_stack.append(String(result_str_py.encode('utf-8')))