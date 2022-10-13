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
import pandas as pd

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
        return (x-s)/(shift_n * s)
    ###END def XrTsUtils.rel_diff

    def unstack_time(
        self,
        timedim: str,
        groupers: tp.List[tp.Any],
        remainder_dim: str = None,
        keep_time_coord: bool = True
    ) -> tp.Union[xr.Dataset, xr.DataArray]:
        """Unstack the time dimension into components or groupers.
        
        Meant to unstack the time dimension into multiple dimensions according
        to time components, such as year, month, hour, minute, but can also be
        used to group along other variables. If each resulting group contains
        more than one element (e.g., if the time dimension is unstacked by year
        and month, but there is more than one data point for some or all
        months), a remainder dimension name must be specified using the
        `'remainder_dim'` parameter.

        Parameters
        ----------
        timedim : str
            Name of the time dimension to unstack
        groupers : list of groupers or strings
            What time components or other groupers to use for ustacking the time
            dimension. Each element will be used as an argument to the xarray
            object's `groupby` function, which is called iteratively during the
            unstacking, so any object that can be passed to `groupby` is in
            principle a valid element of `groupers` (although not all arguments
            will produce valid results). The most common use case is to use
            strings that correspond to time components. These can either be of
            the form `timedimname.componentname` (e.g., `'time.year'`), or just
            `componentname` (in which case it is assumed that you mean the name
            of a component of the `dt` accessor of the time dimension coordinate
            array). NB! Groupers must be a list or other sequence. If you have
            just one grouper, enclose it in a single-element list or tuple.
        remainder_dim : str, optional
            Name to give to the dimension that any non-singular values remaining
            after the unstacking are stored along. It is mandatory if the
            unstacking does not produce only a single element for each group.
            The dimension will be assigned an integer coordinate running from 0
            to the maximum length of the remainder across groups.
        keep_time_coord : bool, optional
            Whether or not to keep the original time values for each data point
            as a coordinate (which will then depend on all the dimensions in
            `groupers`, and on `remainder_dim` if applicable). The coordinate
            will have the same name as the original time dimension (which will
            not exist as a dimension in the returned object). Optional, True by
            default.
        """
        xrobj: tp.Union[xr.Dataset, xr.DataArray] = self._xrobj
        # First convert strings to proper groupers
        _groupers = [None] * len(groupers)
        _i: int
        for _i, _grouper in enumerate(groupers):
            if isinstance(_grouper, str) \
                    and not _grouper.startswith(timedim+'.'):
                _groupers[_i] = getattr(xrobj[timedim].dt, _grouper)
            else:
                _groupers[_i] = _grouper
        # Then group and unstack
        # lastgroup: tp.Union[xr.core.groupby.DatasetGroupBy,
        #                     xr.core.groupbyDataArrayGroupBy] \
        #     = xrobj.groupby(_groupers[0])
        # Define a function to recursively group
        def _group_recursive(
            _x: tp.Union[xr.Dataset, xr.DataArray],
            _rem_groupers: tp.List[tp.Any]  # Remaining groupers
        ) -> tp.Union[xr.Dataset, xr.DataArray]:
            if _rem_groupers:
                _curr_grouper = _rem_groupers[0]
                # If _curr_grouper is a string not starting with the name of
                # the time dimension, assume that it is the name of an
                # attribute of the `dt` accessor.
                if isinstance(_curr_grouper, str) \
                        and not _curr_grouper.startswith(timedim+'.'):
                    _curr_grouper = getattr(_x[timedim].dt, _curr_grouper)
                return _x.groupby(_curr_grouper).map(
                    lambda x: _group_recursive(x, _rem_groupers[1:])
                )
            else:
                _x_return: tp.Union[xr.Dataset, xr.DataArray] = \
                    _x.copy(deep=False)
                _time_coord: xr.DataArray = _x_return['time'].copy(deep=False) \
                    if keep_time_coord else None
                if remainder_dim:
                    _x_return = _x_return.rename({timedim: remainder_dim})
                    # Delete the time dim index to ensure that we don't get all
                    # the time values concatenated together as a separate
                    # dimension when the groupby function concatenates the
                    # results
                    # # Old, remove the deletion of the remainder_dim coordinate
                    # # below. We instead need to set an integer coordinate.
                    # if remainder_dim in _x_return:
                    #     del _x_return[remainder_dim]
                    _x_return = _x_return.assign_coords(
                        {remainder_dim: list(range(0, len(_time_coord)))}
                    )
                    if keep_time_coord:
                        _x_return = _x_return.assign_coords(
                            {timedim: (remainder_dim, _time_coord.to_numpy())}
                        )
                else:
                    if len(_time_coord) > 1:
                        raise ValueError(
                            'Remaining time dimension is longer than 1 element'
                            ' for at least one time group. You must specify a '
                            'value for `remainder_dim` to store the remainder '
                            'values.'
                        )
                    if not keep_time_coord and timedim in _x_return:
                        del _x_return[timedim]
                    _x_return = _x_return.squeeze(timedim)
                return _x_return
        ###END def XrTsUtils.unstack_time._group_recursive
        return _group_recursive(_x=xrobj, _rem_groupers=groupers)
    ###END def XrTsUtils.unstack_time

###END class XrTsUtils


class XrPlotUtils:
    """Xarray accessor class for extra plotting-related functionality."""

    __slots__ = ('_xrobj')
    _xrobj: XrObj

    def __init__(self, xrobj: XrObj):
        self._xrobj: tp.Union[xr.Dataset, xr.DataArray] = xrobj
    ###END def XrPlotUtils.__init__

    def pdplot(
        self,
        y: tp.Union[str, tp.List[str]] = None,
        kind: str = None,
        **kwargs
    ) -> tp.Any:
        """Make plots leveraging pandas `Dataframe.plot` functions.
        
        This function transforms a Dataset or DataArray into a pandas Series or
        DataFrame, and calls functions under its `plot` attribute, which ofers
        more plot types than `xarray` does natively through `Dataset.plot` or
        `DataArray.plot`.

        Parameters
        ----------
        x : str or any, optional
            Dimension to use for the `x` argument of pandas plotting functions.
            This usually does not need to be specified. By default, all
            dimensions will be used (and will be levels of the MultiIndex of the
            DataFrame or Series that the xarray object gets converted into
            before plotting).
        y : str or list of str, optional
            Dimension to use for the `y` argument of pandas plotting functions.
            The dimension(s) listed under this parameter get unstacked onto
            columns of the DataFrame that the xarray object is converted into,
            before calling the DataFrame's `plot` function.
        kind : str, optional
            What kind of plot to produce. See the documentation of
            `pandas.DataFrame.plot` for valid options. If not specified, the
            xarray object will be converted into a DataFrame, and its `plot`
            function will be called directly.
        **kwargs
            Additional keyword arguments to pass to the plotting function. See
            the documentation of `pandas.DataFrame.plot`.
        
        Returns
        -------
            Whichever value is returned by the relevant pandas plotting
            function, typically the return value of a matplotlib plotting
            function.
        """
        pdobj: tp.Union[pd.DataFrame, pd.Series]
        xrobj: tp.Union[xr.Dataset, xr.DataArray] = self._xrobj
        if isinstance(xrobj, xr.Dataset):
            pdobj: pd.DataFrame = xrobj.to_dataframe()
        elif isinstance(xrobj, xr.DataArray):
            pdobj: pd.Series = xrobj.to_series()
        else:
            pdobj = xrobj.to_pandas()
        if y is not None:
            pdobj: pd.DataFrame = pdobj.unstack(y)
        plotfunc: tp.Callable
        if kind is None:
            plotfunc = pdobj.plot
        else:
            plotfunc = getattr(pdobj.plot, kind)
        return plotfunc(**kwargs)
    ###END def XrPlotUtils.pdplot

    def bar(
        self,
        y: str = None,
        **kwargs
    ) -> tp.Any:
        """Make a bar plot leveraging pandas `DataFrame.plot.bar`.
        
        See the documentation of the `pdplot` method. This method is equivalent
        to calling `pdplot` with `kind='bar'`."""
        return self.pdplot(y=y, kind='bar', **kwargs)
    ###END dev XrPlotUtils.pdplot

###END class XrPlotUtils

class XrDisplayUtils:
    """Xarray accessor class for extra display-related functionality."""

    __slots__ = ('_xrobj')
    _xrobj: XrObj

    def __init__(self, xrobj: XrObj):
        self._xrobj: tp.Union[xr.Dataset, xr.DataArray] = xrobj
    ###END def XrDisplayUtils.__init__

###END class XrDisplayUtils

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

def register_accessor(
    name: str,
    accessor_cls: type,
    xrtype: tp.Literal['Dataset', 'DataArray', 'both'] = 'both'
):
    """Register a generic accessor with selected Xarray classes.
    
    Parameters
    ----------
    name : str
        Name to give to the accessor.
    accessor_cls : type
        The accessor class to register
    xrtype : str, optional
        What xarray object type to register the accessor for. Can be
        `'Dataset'`, `'DataArray'` or `'both'`. Optional, `'both'` by default.
    """
    regfuncs: tp.List[tp.Callable] = _get_regfuncs(xrtype=xrtype)
    _func: tp.Callable[[str], tp.Callable]
    for _func in regfuncs:
        _func(name)(accessor_cls)
###END def register_accessor

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
    register_accessor(name=name, accessor_cls=XrTsUtils, xrtype=xrtype)
###END def register_tsutils

def register_plotutils(
    name: str = 'plotutils',
    xrtype: tp.Literal['Dataset', 'DataArray', 'both'] = 'both'
):
    """Reguster XrPlotUtils as xarray accessor `plotutils`.
    
    Parameters
    ----------
    name : str, optional
        Name to give to the accessor. Optional, `'plotutils'` by default
    xrtype : str, optional
        What xarray object type to register the accessor for. Can be
        `'Dataset'`, `'DataArray'` or `'both'`. Optional, `'both'` by default.
    """
    register_accessor(name=name, accessor_cls=XrPlotUtils, xrtype=xrtype)
###END def register_plotutils

def register_displayutils(
    name: str = 'display',
    xrtype: tp.Literal['Dataset', 'DataArray', 'both'] = 'both'
):
    """Reguster XrDisplayUtils as xarray accessor `display`.
    
    Parameters
    ----------
    name : str, optional
        Name to give to the accessor. Optional, `'display'` by default
    xrtype : str, optional
        What xarray object type to register the accessor for. Can be
        `'Dataset'`, `'DataArray'` or `'both'`. Optional, `'both'` by default.
    """
    register_accessor(name=name, accessor_cls=XrDisplayUtils, xrtype=xrtype)
###END def register_displayutils
