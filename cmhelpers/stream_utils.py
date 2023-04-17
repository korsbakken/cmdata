"""Helper functions for working with streams and files."""
import typing as tp
import io
from pathlib import Path
import contextlib


def no_exit_context(obj: tp.ContextManager) -> tp.ContextManager:
    """Take a context manager and return the same object, but with an `__exit__` method
    that does nothing.
    
    Can be used, .e.g., to use a an existing stream in a `with` block without
    having it be closed when leaving the block.
    """
    class NoExitContext(type(obj)):
        def __init__(self, _contextmanager: tp.ContextManager):
            super().__init__(_contextmanager)
        def __exit__(
            self,
            __exc_type: type,
            __exc_value: Exception,
            __traceback
        ) -> tp.Optional[bool]:
            pass
    ###END class no_exit_context.NoExitContext
    return NoExitContext(obj)
###END def no_exit_context

def file_or_stream(
    file: tp.Union[str, Path, io.IOBase],
    mode: str = 'r',
    encoding: str = None,
    close_on_exit: bool = None
) -> tp.ContextManager:
    """Open a file or just use an existing stream, depending on the input.
    
    Takes an input that can be either a file path (str or `pathlib.Path`
    instance) or an existing stream (presumed to be open for reading/writing).
    If the input is a path, the corresponding file is opened. 
    
    Parameters
    ----------
    file : str, Path or io stream
        The path or stream to process. If a path, it will be opened, and the
        corresponding context manager will be returned. If a stream, either the
        stream itself will be returned, or a stream where the context manager
        has had its `__exit__` method replaced by a method that does nothing
        (meaning that the stream will not be closed after having been used in a
        `with` block).
    mode : str
        Mode to open `file` in. Only used if `file` is a file path to be opened,
        is ignored if `file` is a stream. Optional, `'r'` by default.
    encoding : str
        Encoding to pass to the `open` function if `file` is a path. Ignored if
        `file` is a stream.
    close_on_exit : bool or None
        Whether to close `file` after using it in a `with` block. If `None`,
        `file` *will* be closed if it is a file path that gets opened by this
        function, and *will not* be closed if it is a stream that was already
        open. Not closing `file` on exit is achieved by returning a custom
        context manager that supports all the same operations as the output from
        the `open` function (or `file` itself if it is a stream), but where the
        `__exit__` method does nothing.
    """
    if isinstance(file, str) or isinstance(file, Path):
        f = open(file, mode=mode, encoding=encoding)
        if close_on_exit is not None and not close_on_exit:
            f = no_exit_context(f)
    else:
        if close_on_exit:
            f = file
        else:
            f = no_exit_context(file)
    return f
###END file_or_stream
