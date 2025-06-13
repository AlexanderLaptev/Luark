import typing
if typing.TYPE_CHECKING:
    from luark.vm.luavm import PrototypeRunner


class BaseRuntimeException(RuntimeError):
    def __init__(self, message: str = "", prototype_name: str = "", program_counter: int = 0):
        self.message: str = message
        self.prototype_name: str = prototype_name
        self.program_counter: int = program_counter


class NilPointerException(BaseRuntimeException):
    """A runtime error on access data by nil"""

    def __init__(self, prototype_runner: 'PrototypeRunner' = None, message: str = "Cannot access to data by nil"):
        super().__init__(
            message,
            prototype_runner.prototype.function_name if prototype_runner is not None else "",
            prototype_runner.program_counter if prototype_runner is not None else 0)


class TypeException(BaseRuntimeException):
    """ A runtime error that when types dont match"""

    def __init__(self, prototype_runner: 'PrototypeRunner', message: str = "Types doesnt match"):
        super().__init__(message, prototype_runner.prototype.function_name, prototype_runner.program_counter)


class UnsupportedOperation(BaseRuntimeException):
    """ A runtime error when vm gets unsupported operation from compiler"""

    def __init__(self, prototype_runner: 'PrototypeRunner',
                 message: str = "This operation is not supported by virtual machine yet"):
        super().__init__(message, prototype_runner.prototype.function_name, prototype_runner.program_counter)


class DefaultError(RuntimeError):

    def __init__(self, message: str = ""):
        self.message: str = message