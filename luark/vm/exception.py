class NilPointerException(RuntimeError):
    """A runtime error on access data by nil"""
    pass


# class TypeException(RuntimeError):
#     """ A runtime error that when types dont match"""

class UnsupportedOperation(RuntimeError):
    """ A runtime error when vm gets unsupported operation from compiler"""