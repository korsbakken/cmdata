"""Helper functions for package datadesc"""

from __future__ import annotations
import typing as tp
from pathlib import Path
import re
import copy


def recurse_by_type(
    obj: tp.Sequence[tp.List[tp.Any], tp.Dict[tp.Hashable, tp.Any]],
    match_type: type,
    action: tp.Callable,
    recurse_depth: int = None,
    inplace: bool = False
) -> tp.Any:
    """Helper function to act on all elements of a given type.
    
    Recurses through all elements of `obj`, and applies `action` to all
    elements and (depending on `recurse_depth`) subelements of `obj` that
    match the specified type.
    
    Parameters
    ----------
    obj : sequence or dict-like
        The object to recurse through. Must be either a sequence that can be
        iterated over, or a dict or similar data type with an `items` method
        that provides an iterable that yields all the keys and values.
    match_type : type
        Type to match. Elements `x` for which `isinstance(x, match_type)`
        returns True will be acted on. NB! If `match_type` is itself a dict
        or sequence type, recursion will stop once it is matched. The
        matching dict/sequence will not be descended into.
    action : callable
        The action to apply to matching elements
    recurse_depth : int, optional
        Depth to recurse to. `1` means only act on the first-level elements of
        `obj` and do not recurse. None means no limit, recurse until only
        a level is reached that contains no further sequences or dicts, or
        until the stack size limit is reached and an exception is raised.
        Optional, by default None.
    inplace : bool, optional
        Whether to make changes inplace. Optional, by default False

    Returns
    -------
        `obj` (if `inplace` is True) or a copy (if `inplace` is False) with
        the transformed values.
    """
    _obj: tp.Any = obj if inplace else copy.copy(obj)
    if isinstance(_obj, match_type):
        return action(_obj)
    # Recurse if recurse_depth has not been reached, and if
    # _obj is a dict or sequence (but not str)
    if (recurse_depth is None or recurse_depth > 0) \
            and (isinstance(_obj, tp.Dict) or
                 isinstance(_obj, tp.Sequence)) \
                and not isinstance(_obj, str):
    # Get an iterable that will yield values and keys (if dict) or index values
    # (if a sequence)
        _iterobj = None
        if isinstance(_obj, tp.Dict):
            _iterobj = _obj.items()
        if isinstance(_obj, tp.Sequence):
            _iterobj = enumerate(_obj)
        # If _iterobj is still None, _obj is not a dict or sequence, so return
        if _iterobj is None:
            return _obj
        _key: tp.Union[str, int]
        _val: tp.Any
        for _key, _val in _iterobj:
            _obj[_key] = recurse_by_type(
                obj=_val,
                match_type=match_type,
                action=action,
                recurse_depth=None if recurse_depth is None \
                    else recurse_depth-1,
                inplace=inplace
            )
    return _obj
###END def recurse_by_type


_IndexedData = tp.Union[str, tp.Dict[str, tp.Any], tp.List[tp.Any]]

def substitute_var(
    text: str,
    substitute_data: _IndexedData,
    var_pattern: re.Pattern = re.compile(r'\$\{(.+)\}'),
    separator: str = '/'
) -> str:
    """Substitute variables from a provided data structure in a string.
    
    The function takes a data structure which may be a `dict`-like data
    structure or a sequence (technically any object that supports bracket
    indexing with a single argument, i.e., a `__getitem__` method with a single
    parameter) or any nested structure of those data structures, and substitutes
    values into a provided string.

    By default, the function expects the string `text` to contain variable
    patterns of the form `${index}`, which will be replaced by
    `substitute_data[index]`. Alternatively, if the string inside the curly
    brackets is of the form `'index0/index1'`, it will be assumed that
    `substitute_data` is a nested data structure, and the pattern will be
    replaced by `subtitute_data[index0][index1]`. More indexes can be added,
    each separated by a slash, for deeper nesting. Each index can contain any
    character other than the separator character (by default `'/'`). 

    If needed, the pattern to be substituted can be changed from `${...}`
    through the optional parameter `var_pattern`, and the separator character
    can be changed through the parameter `separator`.

    Parameters
    ----------
    text : str
        The text to substitute in.
    substitute_data : dict or sequence
        Data structure to take substitution values from. Can be a dict, list, or
        any other subscriptable data structure, or nesting of such data
        structures.
    var_pattern : re.Pattern, optional
        Regular expression `Pattern` for finding variables to be substituted.
        The entire pattern is substituted, and must contain a single matching
        group which will be used as index or indices to retrieve values from
        `substitute_data`. Must be a compiled `re.Pattern` instance, not a
        `str`. Optional, by default `re.compile(r'\$\{(.+)+\}')`.
    separator : str, optional
        Character or string to use as separator. Will be used to split the
        string returned in the matching group in `var_pattern`. None of the
        indexes can contain this character at all. There currently no mechanism
        for escaping the separator character if it occurs in any index values. 
        Optional, by default `'/'`.
    """
    def get_subst(match: re.Match) -> str:
        indexes: tp.List[str] = match.group(1).split(separator)
        _subs = substitute_data
        for index in indexes:
            _subs = _subs[index]
        return _subs
    ###END def substitute_var.get_subst
    return var_pattern.sub(get_subst, text)
###END def sbustitute_var
