"""Utilities to help with common xarray tasks.

The module contains a few classes of methods that can be registered as xarray
accessors. Those classes can be registered using module-level functions that
begin with the prefix `register_`. They generally take the desired name of
the accessor as a parameter, which can be ommitted and instead use a default
name.

Functions to register accessors
-------------------------------
register_tsutils(name: str = 'tsutils', xrtype: str = 'both')
    Register the class `XrTsUtils` as an accessor, which provides utility
    functions for time series and growth rates. Can be registered both as a
    `Dataset` accessor and a `DataArray` accessor.
"""

import typing as tp

import xarray as xr

XrObj: type = tp.Union[xr.Dataset, xr.DataArray]


class XrTsUtils:
    """Accessor class for xarray, for time series and growth rates."""

    __slots__ = ('_xrobj')
    _xrobj: XrObj

    def __init__(self, xrobj: XrObj):
        self._xrobj: XrObj = xrobj
    ###END def XrTsUtils.__init__

    def rel_diff(self, dim: str, shift_n: int = 1) -> XrObj:
        """Calculate relative change along a dimension.

        Calculates the difference along a given dimension, and divides by the
        starting value, giving the relative change along a dimension (0 = no
        change, 1 = 100% change per step).

        For xarray object `xrobj`, if `shift_n` is 1, the result will be equal
        to `(xrobj - xrobj.shift(dim=1)) / xrobj.shift(dim=1)`. I.e., the value
        at position `k` along `dim` will be equal to the difference between the
        values at `k` and `k-1`, relative to the value at `k-1`. If `shift_n` is
        different from 1, it wll be `(xrobj - xrobj.shift(dim=shift_n)) /
        (shift_n * xrobj.shift(dim=shift_n))`. I.e., the value at position `k`
        will be the difference between positions `k` and `k-shift_n`, relative
        to the value at `k-shift_n` and divided by the distance.

        NB! In the current implementation the rate is not adjusted for
        coordinate values along `dim`. It is assumed that each shift is just a
        shift of one unit. This should be fixed in future updates (i.e., we
        should maybe divide by the coordinate difference along `dim` if `dim`
        has an index coordinate).
        
        Parameters
        ----------
        dim : str
            Dimension to calculate the rate of change along
        shift_n : int, optional
            How many steps to shift along `dim` when calculating the relative
            difference. Optional, 1 by default.
        """
        x: tp.Union[xr.Dataset, xr.DataArray] = self._xrobj
        s = x.shift({dim: shift_n})
        return (x-s)/(shift_n - s)
    ###END def XrTsUtils.rel_diff

###END class XrTsUtils

def _get_regfuncs(
    xrtype: tp.Literal['Dataset', 'DataArray', 'both'] = 'both'
) -> tp.List[tp.Callable[[str], tp.Callable]]:
    """Get registration functions for specified xarray types."""
    regfuncs: tp.List[tp.Callable]
    if xrtype == 'DataArray':
        regfuncs = [xr.register_dataarray_accessor]
    elif xrtype == 'DAtaset':
        regfuncs = [xr.register_dataset_accessor]
    elif xrtype == 'both':
        regfuncs = [
            xr.register_dataarray_accessor,
            xr.register_dataset_accessor
        ]
    else:
        raise ValueError(
            '`xrtype` must be "DataArray", "Dataset", or "both".'
        )
    return regfuncs
###END def _get_regfuncs

def register_tsutils(
    name: str = 'tsutils',
    xrtype: tp.Literal['Dataset', 'DataArray', 'both'] = 'both'
):
    """Register XrTsUtils as xarray accessor `tsutils`.
    
    Parameters
    ----------
    name : str, optional
        Name to give to the accessor. Optional, `'tsutils'` by default.
    xrtype : str, optional
        What xarray object type to register the accessor for. Can be
        `'Dataset'`, `'DataArray'` or `'both'`. Optional, `'both'` by default.
    """
    regfuncs: tp.List[tp.Callable] = _get_regfuncs(xrtype=xrtype)
    _func: tp.Callable[[str], tp.Callable]
    for _func in regfuncs:
        _func(name)(XrTsUtils)
###END def register_tsutils
