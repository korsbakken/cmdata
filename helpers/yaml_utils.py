"""Utilities for processing yaml files."""
import typing as tp
from pathlib import Path

import ruamel.yaml as yaml

from .stream_utils import file_or_stream


def read_yaml(
    file: tp.Union[str, Path, tp.TextIO],
    yaml_load_func: tp.Callable[[tp.IO], dict] = yaml.safe_load,
    **kwargs
) -> tp.Dict[tp.Hashable, tp.Any]:
    """Read contents of a YAML file, with no further processing.
    
    By default uses the `safe_load` function from `ruamel.yaml` (i.e., expects
    YAML version 1.2 by default).
    
    Parameters
    ----------
    file : str, Path or text io stream
        The YAML file to read
    **kwargs
        Keyword arguments to pass to the `safe_load` function.
        
    Returns
    -------
    dict
    """
    yaml_content: tp.Dict[tp.Hashable, tp.Any]
    with file_or_stream(file) as f:
        yaml_content = yaml_load_func(f, **kwargs)
    return yaml_content
###END def read_yaml