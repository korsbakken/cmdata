"""Helper functionality to process YAML files."""

from __future__ import annotations
import typing as tp
import copy

import ruamel.yaml as yaml

from . import helpers


_YamlDataType = tp.Union[str, tp.Dict[str, tp.Any], tp.List[tp.Any]]
"""Data type for output from yaml-file parsing."""

def load_yaml(yamlfile: Path, **kwargs) -> _YamlDataType:
    """Load yaml files. Currently just wraps ruamel.yaml.safe_load"""
    return yaml.safe_load(yamlfile, **kwargs)
###END def load_yaml

class VarResolutionError(Exception):
    """Raised if `resolve_variables` does not return before reaching max 
    number of iterations."""
    pass
###END class VarResolutionError


def resolve_variables(
    data: _YamlDataType,
    subst_func: tp.Callable[[str, _YamlDataType], str] = None,
    max_iterations: int = 20,
    inplace: bool = False
) -> _YamlDataType:
    """Substitutes variables in strings in a YAML data structure.
    
    Parameters
    ----------
    data : str, dict, sequence or nested data structure thereof
        The data to subsitute variables in.
    subst_func : callable
        Function to use for making substitutions in each string. Must take a
        string and `data` as positional arguments and return a `str`. Optional,
        by default uses `substitute_var` with default parameers.
    max_iterations : int, optional
        Maximum number of times to iterate to resolve variables that reference
        other variables. If the maximum number of iterations is exceeded without
        having resolved all variables (which will happen if variables are
        circularly defined, or nested too deep), a `VarResolutionError` is
        raised.
    inplace : bool, optional
        Whether or not to make substitutions inplace in `data`. If False, a deep
        copy is made of `data` before subtitution starts. Note that if `data`
        contains any memory-intensive data structures, this may consume a large
        amount of resources, in which case `inplace` should be set to True for
        better performance. Note that if `data` is a plain `str` instance, a
        this parameter will be ignored (Python `str` instances are immutable).
        This should be an edge case, since it is not very useful. Optional, by
        default False.

    Returns
    -------
    _YamlDataType
        `data` itself or a copy thereof, with variables substituted.
    """
    if subst_func is None:
        subst_func = helpers.substitute_var
    if not inplace:
        data = copy.deepcopy(data)
    _num_iterations: int = 0
    # Define a function to crawl through the data if it is not a pure str.
    # It should return True if any substitutions were made.
    def crawl_through_data(curr_data: _YamlDataType, 
                           orig_data: _YamlDataType) -> bool:
        made_substitutions: bool = False
        indexes: list
        if hasattr(curr_data, 'keys'):
            indexes = curr_data.keys()
        else:
            indexes = range(0, len(curr_data))
        for _i in indexes:
            if isinstance(curr_data[_i], str):
                new_str = subst_func(curr_data[_i], orig_data)
                if new_str != curr_data[_i]:
                    made_substitutions = True
                curr_data[_i] = new_str
            else:
                made_substitutions = \
                    crawl_through_data(curr_data[_i], orig_data)
        return made_substitutions
    ###END def resolve_variable.crawl_through_data
    # Do the crawling, or just substitute if data is a plain string
    if isinstance(data, str):
        return subst_func(data, data)
    while crawl_through_data(data, data):
        _num_iterations += 1
        if _num_iterations > max_iterations:
            raise VarResolutionError(
                f'Maximum number of iterations ({str(max_iterations)}) '
                'exceeded! This may indicate circular variable definitions. '
                'Set `max_iterations` to a higher value if the variable '
                'definitions are deeply nested and you need more iterations.'
            )
    return data
###END def resolve_variables
