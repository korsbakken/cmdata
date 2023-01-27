"""Helper functions and classes"""
from __future__ import annotations

import typing as tp
import dataclasses
import collections

import pandas as pd
import numpy as np
import numpy.typing as nptyping


DC = tp.TypeVar('DC')
def dictify_dataclass(_class: DC) -> DC:
    """Adds dict access methods to a dataclass.
    
    Designed to be used as a decorator:

    ```
    import dataclasses

    @dictify_dataclass
    @dataclasses.dataclass(*args, **kwargs)
    class C:
        attr1: type = default1
        attr2: type = default2
        ...
    ```
    """
    if not hasattr(_class, '__getitem__'):
        _class.__getitem__ = lambda self, key: getattr(self, key)
    if not hasattr(_class, '__setitem__'):
        _class.__setitem__ = lambda self, key, value: setattr(self, key, value)
    if not hasattr(_class, '__delitem__'):
        _class.__delitem__ = lambda self, key: delattr(self, key)
    def get_field_names(self):
        return tuple([_field.name for _field in dataclasses.fields(self)])
    if not hasattr(_class, 'keys'):
        _class.keys = get_field_names
    if not hasattr(_class, 'values'):
        _class.values = dataclasses.astuple
    def items(self):
        return zip(self.keys(), self.values())
    if not hasattr(_class, 'items'):
        _class.items = items
    if not hasattr(_class, '__iter__'):
        _class.__iter__ = lambda self: iter(self.keys())

    return _class
###END def dictify

@tp.dataclass_transform()
def dictdataclass(_class: type[DC] = None, **kwargs) \
        -> type[tp.Union[DC, tp.Dict]]:
    """Convenience wrapper that combines `dictify_dataclass` and
    `dataclasses.dataclass` into a single decorator:
    
    ```
    @dictdataclass(*args, **kwargs)
    class C:
        ...
    ```

    is equivalent to

    ```
    @dictify_dataclass
    @dataclasses.dataclass(*args, **kwargs)
    class C:
        ...
    ```
    """
    if _class is not None:
        return dictify_dataclass(dataclasses.dataclass(_class, **kwargs))
    else:
        _c: DC
        return lambda _c: \
            dictify_dataclass(dataclasses.dataclass(**kwargs)(_c))
###END dictdataclass

# @dataclasses.dataclass
# class DictDataClass(collections.UserDict):
#     """Extended dataclass, with dict functionality."""

#     # class _AccessDict:
#     #     def __init__(self, dataclass_obj):
#     #         self._data = dataclass_obj
#     #     def __getitem__(self, key):
#     #         return getattr(self._data, key)
#     #     def __setitem__(self, key, value):
#     #         setattr(self._data, key, value)
#     #     def __delitem__(self, key):
#     #         delattr(self._data, key)

#     @property
#     def data(self) -> dict:
#         return dataclasses.asdict(self)

#     def __settem__(self, key, value):
#         return setattr(self, key, value)

#     def __delitem__(self, key):
#         return delattr(self, key)

#     # def __post_init__(self):
#     #     self.data = self._AccessDict(self)
        
# ###END dataclass class DictDataClass


def dict_to_multi_df(
    d: tp.Dict[tp.Hashable, tp.Any],
    index_levels: tp.Union[tp.Sequence[tp.Hashable], int],
    column_levels: tp.Union[tp.Sequence[tp.Hashable], int],
    orient: tp.Literal['index', 'columns'] = 'index'
) -> pd.DataFrame:
    """Create a DataFrame with MultiIndex from a nexted dictionary.
    
    The function expects a dict of dicts, where each dict at a given level has
    the same keys (corresponding to MultiIndex level values), and the innermost
    values are scalars that specify the data to go in each cell of the resulting
    DataFrame.

    Parameters
    ----------
    d : dict
        The nested dict to be turned into a DataFrame
    index_levels : sequence or int
        Either a sequence that specifies the level names for the row MultiIndex
        levels, or an int giving the number of row levels. In the latter case,
        the levels will have the default names produced by the
        `pandas.MultiIndex` constructor. If there is only a single index level
        (i.e., not a MultiIndex), `index_levels`  must be either `1` or a
        single-element list with the index name. You must *not* pass a scalar
        string with the index name (if you do, the function will interpret each
        character in the string as a separate level name).
    column_levels : sequence or int
        Same as for `index_levels`, but specifies the names or number of column
        MultiIndex levels. The number of levels specified by `index_levels` and
        `column_levels` *must* add up to the number of nested levels in `d`.
    orient : str, optional
        Which order the levels of the nested dict `d` are in:
          * `'index'` (default): Outer levels correspond to row index levels,
            followed by column levels.
          * `'columns'`: Outer levels correspond to column levels, followed by
            row index levels.

    Returns
    -------
    pandas.DataFrame
    """
    index_level_num: int
    index_level_names: tp.List[tp.Hashable]
    column_level_num: int
    column_level_names: tp.List[tp.Hashable]
    if isinstance(index_levels, int):
        index_level_num = index_levels
        index_level_names = list(range(0, index_level_num-1))
    else:
        index_level_num = len(index_levels)
        index_level_names = list(index_levels)
    if isinstance(column_levels, int):
        column_level_num = column_levels
        column_level_names = list(range(0, column_level_num))
    else:
        column_level_num = len(column_levels)
        column_level_names = list(column_levels)
    total_level_num: int = index_level_num + column_level_num
    all_level_names: tp.List[tp.Hashable]
    if orient == 'index':
        all_level_names = index_level_names + column_level_names
    elif orient == 'columns':
        all_level_names = column_level_names + index_level_names
    else:
        raise ValueError(
            '`orient` must be either "index" or "columns".'
        )

    flat_df: pd.DataFrame = df_from_nested_dict(
        d=d,
        columns=all_level_names + ['___data___']
    )

    indexed_df: pd.DataFrame = flat_df.set_index(all_level_names).iloc[:, 0]
    indexed_df = tp.cast(pd.DataFrame, indexed_df.unstack(column_level_names))

    return indexed_df
####END def dict_to_multi_df


def df_from_nested_dict(
    d: tp.Dict[tp.Hashable, tp.Any],
    columns: tp.Sequence[tp.Hashable]
) -> pd.DataFrame:
    """Create a DataFrame from a nested dict.
    
    The keys of each level in the nested dict will be used as values for one
    column of the resulting DataFrame. The two columns defined by a dict at
    an intermediate level will be the product of the outer keys wit the keys
    of the child dictionaries. The values of the innermost dicts will be the
    actual values of the right-most column of the returned DataFrame.

    Parameters
    ----------
    d : dict
        The nested dict to be turned into a DataFrame
    columns : sequence of hashable
        The names (column index values) to use for the columns of the returned
        DataFrame. The number of elements must be equal to the number of
        nesting levels plus one (for the innermost values).

    Returns
    -------
    pandas.DataFrame
    """
    def _unnest(d: tp.Dict, keys: tp.List[tp.Hashable] = []) \
            -> tp.List[tp.Tuple]:
        result: tp.List[tp.Tuple] = []
        for k, v in d.items():
            if isinstance(v, dict):
                result.extend(_unnest(v, keys+[k]))
            else:
                result.append(tuple(keys+[k, v]))
        return result
    flat_tuple_list: tp.List[tp.Tuple]= _unnest(d)
    flat_df: pd.DataFrame = pd.DataFrame(
        data=flat_tuple_list,
        columns=columns
    )
    return flat_df
###END def df_from_nested_dict


def get_df_data(
    df: pd.DataFrame,
    name: tp.Hashable,
    return_type: bool = False
) -> tp.Union[
        pd.Series,
        tp.Tuple[pd.Series, tp.Literal['index', 'indexlevel', 'column']]
    ]:
    """Return a column, index or index level with a given name.
    
    Also optionally returns a tuple, with the column/index/index level as the
    first element, and a string identifying the type as the second element.
    
    The data is returned as a Series.
    
    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to get data from
    name : hashable
        The name of the column, index or index level to get.
    return_type : bool, optional
        Whether to return a tuple, with the second element identifying whether
        the returned data was found in the index, as a level of the index
        (which must then be a `MultiIndex`) or in a column. The second element
        will be `'index'`, `'indexlevel'` or `'column'`, respectively.

    Returns
    -------
    pandas.Series or tuple of pandas.Series and str
        A Series with the content of the column, index or index level values,
        with `name` attribute equal to the `name` argument. *NB!* If `name` is
        the name of a column of `df`, the actual column will be returned, not
        a copy (unlike the case of an index or index level, in which case a
        new Series will be returned). Make a copy if you want to be sure to
        avoid accidental changes to the original data.

    Raises
    ------
    KeyError
        If no column, index or index level with name `name` is found.
    """
    data_type: tp.Literal['index', 'indexlevel', 'column']
    data: pd.Series
    if isinstance(df.index, pd.MultiIndex) and name in df.index.names:
        data = df.index.get_level_values(name).to_series(name=name)
        data_type = 'indexlevel'
    elif df.index.name == name:
        data = df.index.to_series(name=name)
        data_type = 'index'
    elif name in df.columns:
        data = tp.cast(pd.Series, df[name])
        data_type = 'column'
    else:
        raise KeyError(name)

    if return_type:
        return (data, data_type)
    else:
        return data
###END def get_df_data

def set_index_as_columns(
    df: pd.DataFrame,
    include_levels: tp.Optional[tp.Sequence[str]] = None,
    exclude_levels: tp.Optional[tp.Sequence[str]] = None,
    column_names: tp.Optional[tp.Union[str, tp.Sequence[str], tp.Dict[str, str]]] \
        = None,
) -> pd.DataFrame:
    """Set a copy of index/index levels as columns in a DataFrame.

    Columns are added to the end of the returned `DataFrame`, in the order
    given by `include_levels` if specified, otherwise in the order of
    appearance in `df.index.names` if `df.index` is a `MultiIndex`.
    
    Parameters
    ----------
    df : pandas.DataFrame
        The DataFrame to process.
    include_levels : sequence of str, optional
        Names of index levels to include. Optional, defaults to all levels if
        not specified and `exclude_levels` is also None. Is ignored if
        `df.index` is not a MultiIndex (in which case the index itself is set
        as a single column).
    exclude_levels : sequence of str, optional
        Names of index levels to exclude. Other levels will be included. Must
        not be specified if `include_levels` is specified (will raise
        `ValueError`), but exactly one of `include_levels` and `exclude_levels`
        must be specified whenever `df.index` is a `MultiIndex`. Is ignored if
        `df.index` is not a `MultiIndex`.
    column_names : sequence of str, dict or str, optional
        Names to use for the columns in the returned DataFrame. If `df.index`
        is a `MultiIndex`, `column_names` can be given either as a sequence of
        `str`, in which case it must have the same length and be in the same
        order as `include_levels` (if specified) or as `df.index.names`, or
        as a `dict` that maps from level names in `df` to column names in the
        returned DataFrame. If `df.index` is not a `MultiIndex`, `column_names`
        must be a simple str. Optional, defaults to using the same name as the
        included index levels from `df`.

    Returns
    -------
    pandas.DataFrame
        New (shallow-copied) DataFrame with new columns equal to `df`.index` or
        the included levels of `df.index`.
    """
    ret_df: pd.DataFrame = df.copy(deep=False)
    del df
    if not isinstance(ret_df.index, pd.MultiIndex):
        _colname: tp.Optional[str]
        if column_names is None:
            _colname = ret_df.index.name
            if _colname is None:
                raise ValueError(
                    '`column_names` must be specified and be a single string '
                    'when `df.index.name` is not set.'
                )
            ret_df[_colname] = ret_df.index.to_series()
            return ret_df
    else:
        if include_levels is not None:
            if exclude_levels is not None:
                raise ValueError(
                    'Specify only one of `include_levels` and `exclude_levels`'
                    ', not both.'
                )
        elif exclude_levels is not None:
            if include_levels is not None:
                raise ValueError(
                    'Specify only one of `include_levels` and `exclude_levels`, '
                    'not both.'
                )
            include_levels = [
                _name for _name in ret_df.index.names
                if _name not in exclude_levels
            ]
        else:
            include_levels = ret_df.index.names
    if include_levels is None:
        raise RuntimeError(
            '`include_levels` is None, should not be possible at this point in '
            'the code.'
        )
    if column_names is None:
        column_names = {_colname: _colname for _colname in include_levels}
    elif isinstance(column_names, str):
        raise TypeError(
            '`column_names` cannot be a single str when `df.index` is a '
            'MultiIndex.'
        )
    elif isinstance(column_names, tp.Sequence):
        if len(column_names) != len(include_levels):
            '`column_names` must be the same length as the number of included '
            'index levels.'
        column_names = {
            _oldcol: _newcol
            for _oldcol, _newcol in zip(include_levels, tuple(column_names))
        }
    elif not isinstance(column_names, tp.Dict):
        raise TypeError(
            '`column_names` must be a sequence of str or a dict.'
        )
    if not isinstance(column_names, tp.Dict):
        raise RuntimeError(
            '`column_names` should be a dict at this point but is not, '
            'not clear why. Aborting!'
        )
    level_df: pd.DataFrame = ret_df.index.to_frame(index=True).loc[:, include_levels]
    if any([_colname not in include_levels for _colname in column_names.keys()]):
        raise ValueError(
            '`column_names` includes names that are not present in included '
            'index levels.'
        )
    level_df = level_df.rename(columns=column_names)

    return pd.concat([ret_df, level_df], axis=1)

###END def set_index_as_columns


def pdsel(
    pdobj: tp.Union[pd.DataFrame, pd.Series],
    _indexer_type: tp.Literal['label', 'index'] = 'label',
    **kwargs
) -> tp.Union[pd.DataFrame, pd.Series]:
    """Select by column or index level values using keyword arguments.
    
    Returns
    -------
    pandas.DataFrame or pandas.Series
    """
    # First get indexers that are column names
    col_indexers: tp.Dict
    if isinstance(pdobj, pd.DataFrame):
        col_indexers = {
            _colname: _indexer for _colname, _indexer in kwargs.items()
            if _colname in pdobj.columns
        }
    else:
        col_indexers = {}
    level_indexers: tp.Dict = {
        _levelname: _indexer for _levelname, _indexer in kwargs.items()
        if _levelname not in col_indexers.keys()
    }
    # Check that level_indexers are valid index levels, or empty if df.index is
    # not a MultiIndex.
    if level_indexers:
        if not isinstance(pdobj.index, pd.MultiIndex):
            raise ValueError(
                'Keyword arguments contain keys that are not valid column names.'
            )
        elif any(
            [
                _levelname not in pdobj.index.names
                for _levelname in level_indexers.keys()
            ]
        ):
            raise ValueError(
                'Keyword arguments contain keys that are not valid index level '
                'names.'
            )

    filtered_obj: tp.Union[pd.DataFrame, pd.Series] = pdobj.copy(deep=False)

    # First select from the index. The .loc accessor will raise a KeyError if
    # any of the keys are not found, so selecting on the index first rather
    # the columns ensures that we don't get an error if any of the index labels
    # are no longer present after filtering on the column values.
    if level_indexers:
        multiindex_selector: tp.List = make_multiindex_selector(
            pdobj,
            **level_indexers
        )
        filtered_obj = filtered_obj.loc[multiindex_selector]

    # Then filter the DataFrame by each column. Turn each column in
    # turn into an index, get the indices for each, and use it to filter
    # the DataFrame before repeating with the next column.
    for _col, _selection in col_indexers.items():
        tempindex: pd.Index = pd.Index(filtered_obj[_col])
        indexer: tp.Union[slice, np.ndarray]
        if isinstance(_selection, slice):
            indexer = tempindex.slice_indexer(
                start=_selection.start,
                end=_selection.stop,
                step=_selection.step
            )
        else:
            indexer = tempindex.get_indexer_for(_selection)
        filtered_obj = filtered_obj.iloc[indexer]

    return filtered_obj
    
###END def pdsel


def make_multiindex_selector(
    pdobj: tp.Union[pd.MultiIndex, pd.DataFrame, pd.Series],
    **kwargs
) -> tp.Tuple:
    """Make a selector that can be passed to `pdobj.loc` using keyword
    arguments with `pdobj.index` level names as keys.
    
    Similar to the `.sel` method in `xarray`.
    """
    if not isinstance(pdobj, pd.MultiIndex) \
            and not isinstance(pdobj.index, pd.MultiIndex):
        raise TypeError(
            '`pdobj` must have or be a MultiIndex.'
        )
    if isinstance(pdobj, pd.DataFrame) or isinstance(pdobj, pd.Series):
        assert isinstance(pdobj.index, pd.MultiIndex)
        pdobj = pdobj.index
    if any([_key not in pdobj.names for _key in kwargs.keys()]):
        raise ValueError(
            'Passed keyword argument that is not an existing level name.'
        )
    selector: tp.List = [slice(None)] * len(pdobj.names)
    for _key, _selector in kwargs.items():
        selector[pdobj.names.index(_key)] = _selector
    return tuple(selector)
###END def make_multiindex_selector
