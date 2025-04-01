class InternalCompilerError(RuntimeError):
    """An internal error in the compiler."""
    pass


class CompilationError(RuntimeError):
    """A compilation error caused by an invalid program."""
    pass
