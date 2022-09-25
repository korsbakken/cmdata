"""Subpackage for unit definitions and working with units.

Most functionality in this package makes use of the `pint` package.
"""
import typing as tp
from pathlib import Path
import functools

import pint


class UregFileSpec(tp.NamedTuple):
    path: Path
    include_default: bool
###END class UregFileSpec

units_files: tp.Dict[str, UregFileSpec] = {
    'NBS_zh': UregFileSpec(
        path=Path(__file__).parent / 'pint_units_NBS_zh.txt',
        include_default=True
    )
}

def get_ureg_names() -> tp.Tuple[str, ...]:
    """Get names of available UnitRegistry objects.
    
    The returned names can be passed to `get_ureg` to load and return the
    corresponding UnitRegistry object.
    
    Returns
    -------
    tuple of str
    """
    return tuple(units_files.keys())
###END def get_reg_names

@functools.cache
def get_ureg(name: str) -> pint.UnitRegistry:
    """Get a custom `UnitRegistry` for use with `pint`.
    
    The names of available unit registries can be obtained through the function
    `get_ureg_names`.

    The function loads a UnitRegistry from a definition file the first time a
    given UnitRegistry is requested. On subsequent calls with the same `name`
    parameter, a cached instance is returned (using `functools.lru_cache`). If
    you wish to clear the cache and load fresh UnitRegistry instances from file,
    you can call `get_ureg.clear_cache()` before calling `get_ureg` itself.
    Please note that the instance returned from cache for a given `name` is the
    *same* instance as the one that was returned the first time. If you plan on
    making changes to the `UnitRegistry` instance, you should therefore consider
    making a copy first (e.g., using the `copy` function from the built-in
    `copy` module) if the instance is used other places in your code where you
    do not intend for those changes to take effect.
    """
    if not isinstance(name, str):
        raise TypeError(
            '`name` must be a string.'
        )
    if name not in get_ureg_names():
        raise KeyError(
            f'No unit registry with key {name}. Please use `get_ureg_names()` '
            'to obtain a tuple of valid unit registry names.'
        )
    ureg_data: UregFileSpec = units_files[name]
    ureg: pint.UnitRegistry
    if ureg_data.include_default:
        ureg = pint.UnitRegistry()
        ureg.load_definitions(ureg_data.path)
    else:
        ureg = pint.UnitRegistry(ureg_data.path)
    return ureg
###END def get_ureg
