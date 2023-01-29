"""Helper functionality for xarray groupby operations."""
from __future__ import annotations
import typing as tp

import xarray as xr
import pandas as pd
import numpy as np
import xarray.core.groupby as xrgroupby

XrData: tp.TypeAlias = tp.Union[xr.Dataset, xr.DataArray]
XrTypeVar = tp.TypeVar('XrTypeVar', xr.Dataset, xr.DataArray)


class DimensionNotPresentError(Exception):
    """Denotes that an expected dimension is not present in an array."""
    __slots__ = ('expected_dimnames', 'msg')

    def __init__(
        self,
        msg: tp.Optional[str] = None,
        expected_dimnames: tp.Optional[tp.Tuple[tp.Hashable, ...]] = None
    ):
        self.msg: tp.Optional[str] = msg
        self.expected_dimnames: tp.Optional[tp.Tuple[tp.Hashable, ...]] = \
            expected_dimnames
        super().__init__(msg, expected_dimnames)
###END class DimensionNotPresentError


def groupby_keep_dimname(
    xrobj: XrTypeVar,
    grouper: tp.Union[tp.Hashable, xr.DataArray, xr.IndexVariable],
    func: tp.Union[str, tp.Callable[[XrTypeVar], XrTypeVar]],
    newdimname: tp.Optional[tp.Hashable] = None,
    raise_on_no_dim: bool = False
) -> tp.Union[XrTypeVar, xr.DataArray]:
    """Perform a grouping operation and keep or specify grouped dimension name.
    
    Normally when grouping an xarray object and performing a grouped reducing
    operation, the dimension that was reduced over will be replaced by a new
    dimension with a name given by the name of the grouping index variable. In
    such cases, this function will instead restore the original dimension name,
    or replace the grouping dimension name with a freely specified name.
    
    The function performs the grouping and applies a function to the groups,
    then takes the result and renames any dimension with the same name as the
    grouper into the original or specified dimension name.
    
    Parameters
    ----------
    xrobj : xarray.Dataset or xarray.DataArray
        The xarray object to be grouped
    grouper : hashable or xarray.DataArray
        The name of the variable/coordinate in `xrobj` to group over, or a
        `DataArray` to group over. Same as the `group` parameter in xarray's
        `groupby` function. *NB!* Only one-dimensional groupers will be
        accepted. For multi-dimensional groupers, it is not necessarily possible
        or well-defined how to rename the grouped dimension(s).
    func : str or callable
        Either the name of a method in `DatasetGroupBy` or `DataArrayGroupBy` to
        call, or a function to be applied to the groups (will be passed to the
        `map` method of `DatasetGroupBy`/`DataArrayGroupBy`). If a function,
        must be compatible with xarray's groupby `map` method.
    newdimname : str, optional
        New name to replace the grouped dimension by. Optional, by default equal
        to the original dimension name along which `grouper` is defined.
    raise_on_no_dim : bool, optional
        Raise a `DimensionNotPresentError` if neither the original dimension
        name nor the name of the grouper is present in the dimensions of the
        returned object after grouping and applying `func`. Optional, False by
        default.
    
    Returns
    -------
    xarray.Dataset or xarray.DataArray
        The result of the group/apply/combine operation, wiith restored/renamed
        group dimension name. If the original dimension name is still present,
        no dimension renaming will be done, even if the name of the grouper is
        also present among the dimension names. If neither the original
        dimension name or the name of the gruoper is present as dimension names,
        a `DimensionNotPresentError` will be raised if `raise==True`, otherwise
        the object will be returned without any dimension renaming.
    """
    original_dimname: tp.Hashable
    grouper_name: tp.Hashable
    grouper_dims: tp.Sequence[tp.Hashable]
    grouped_xrobj: tp.Union[XrTypeVar, xr.DataArray]

    if isinstance(grouper, xr.DataArray) \
            or isinstance(grouper, xr.IndexVariable):
        grouper_name = grouper.name
        grouper_dims = grouper.dims
    else:
        grouper_name = grouper
        grouper_dims = xrobj[grouper].dims
    if len(grouper_dims) > 1:
        raise ValueError(
            'Multi-dimensional groupers are not supported.'
        )
    original_dimname = grouper_dims[0]
    if newdimname is None:
        newdimname = original_dimname

    groupby: tp.Union[xrgroupby.DatasetGroupBy, xrgroupby.DataArrayGroupBy] = \
        xrobj.groupby(grouper)

    if callable(func):
        grouped_xrobj = groupby.map(func)
    else:
        grouped_xrobj = getattr(groupby, func)()

    # Rename dimensions if needed
    if original_dimname in grouped_xrobj.dims:
        if newdimname != original_dimname:
            grouped_xrobj = grouped_xrobj.rename(
                {
                    original_dimname: newdimname
                }
            )
        return grouped_xrobj
    elif grouper_name in grouped_xrobj.dims:
        grouped_xrobj = grouped_xrobj.rename(
            {
                grouper_name: newdimname
            }
        )
        return grouped_xrobj
    else:
        if raise_on_no_dim:
            raise DimensionNotPresentError(
                'Neither the original dimension name nor the grouper name is '
                'present in the dimensions of the grouped object.',
                expected_dimnames=(original_dimname, grouper_name)
            )
        else:
            return grouped_xrobj
###END def groupby_keep_dimname
