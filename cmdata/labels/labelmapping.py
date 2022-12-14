"""Module for retrieving maps and mapping between labels."""
from __future__ import annotations
import typing as tp
from pathlib import Path
import io

import pandas as pd
import numpy as np
import ruamel.yaml as yaml


class LabelMap:
    """Class used to map between different versions of labels.
    
    The class stores label versions in an internal `pandas.DataFrame`, indexed
    by standardized label codes, and with each possible version of the label in
    separate columns. A copy of the DataFrame can be through the `get_df`
    method, which makes a (shallow) copy to reduce the risk of external
    changes being made. The original DataFrame can be accessed through the
    attribute `_df`, though this should obviously be used with caution.
    
    Label definitions are read from yaml files using the `from_yaml` class
    method.
    """

    __slots__ = ('_df', '_code_col_name')
    _df: pd.DataFrame

    _yaml_meta_keys: tp.Tuple[str, ...] = (
        'code_type',
        'orient',
        'columns',
        'ordered',
        'data'
    )
    """Keys in YAML files that are not part of the data (contains metadata and,
    in the case of `"data"`, denotes the start of data after the metadata)."""

    _yaml_data_key: str = 'data'
    """Name of the key in a YAML file that denotes the start of the data
    dictionary (the one that contains the label values) after a block of
    metadata key/value pairs."""

    _default_code_col_name: str = 'code'
    """Default name of the column or index containing codes in the internal
    DataFrame"""

    def __repr__(self) -> str:
        return f'Instance of {repr(self.__class__)}:\n' \
            f'{repr(self._df)}'
    ###END def LabelMap.__repr__


    def __init__(
        self,
        defdict: tp.Dict[tp.Hashable, tp.Any],
        orient: tp.Literal['index', 'columns'] = 'columns',
        values_dtype: tp.Union[str, type, np.dtype] = 'category',
        index_dtype: tp.Union[str, type, np.dtype] = 'category',
        code_col_name: str = None
    ):
        """Initializes an instance with definitions from a dictionary.
        
        Parameters
        ----------
        defdict : dict
            Dictionary with label codes as keys and dicts with equal lengths and
            the same keys as values. Will be converted into an internal
            DataFrame using `pandas.DataFrame.from_dict.
        orient : `'index'` or `'columns'`, optional
            Orientation of `defdict`. Same as in `pandas.DataFrame.from_dict`.
            Optional, by default `'columns'`.
        values_dtype : str, type, or numpy.dtype, optional
            dtype to use for the values columns in the internal DataFrame.
            Opitional, by default `'category'`.
        index_dtype : str, type, or numpy.dtype, optional
            dtype to use for the index in the internal DataFrame. Opitional, by
            default `'category'`.
        code_col_name: str, optional
            Name to use for the index in the internal DataFrame, or code column
            when/if the index is converted into a regular column. Optional,
            defaults to the class attribute `_default_code_col_name` (`'code'`
            in the base class).
        """
        self._df: pd.DataFrame = pd.DataFrame.from_dict(
            data=defdict,
            orient=orient,
            dtype=values_dtype
        )
        self._df.index = self._df.index.astype(index_dtype)
        self._code_col_name: str = code_col_name if code_col_name is not None \
            else self._default_code_col_name
        self._df.index.name = self._code_col_name
    ###END def LabelMap.__init__

    @property
    def code_col_name(self) -> str:
        return self._code_col_name
    ###END def property LabelMap.code_col_name

    def get_df(
        self,
        deep: bool = False
    ) -> pd.DataFrame:
        """Returns a copy of the internal DataFrame. Shallow by default.
        
        Parameters
        ----------
        deep : bool, optional
            Whether to make a deep copy (copy values, not just of the DataFrame
            object itself). Optional, False by default.
        """
        return self._df.copy(deep=deep)
    ###END def LabelMap.get_df

    @classmethod
    def from_yaml(
        cls,
        yamlfile: tp.Union[str, Path, tp.TextIO],
        key: tp.Union[tp.Hashable, tp.Sequence[tp.Hashable]] = None,
        orient: tp.Literal['index', 'columns', None] = None
    ) -> LabelMap:
        """Constructs a `LabelMap` instance from a YAML file definition.

        The YAML dictionary that is obtained after following the key path
        specified by the `key` parameter (if any) is assumed to have one of two
        structures:
            1. A data dictionary, where each key denotes either a code or a
               column name (depending on whether `orient` is `'index'` or
               `'columns'`, respectively), and each value is another dictionary
               with column names or codes as keys and corresponding value as
               values.
            2. A dictionary where the first key/value pairs contain metadata,
               followed by a final element with key `"data"` and where the value
               is the data dictionary, as specified in point 1 above. Valid keys
               in the metadata block are given by the class attribute
               `_yaml_meta_keys` (`"code_type"`, `"orient"`, `"columns"`
               `"ordered"` in the base class, can be overridden or extended by
               derived classes). The key that specifies the data dictionary is
               `"data"` in the base class, but can be overridden by derived
               classes. Of the metadata elements, only `"orient"` is currently
               used by this function.

        If only valid metadata tags are present in the dictionary, and the key
        `"data"` is present, the dictionary is assumed to be of type 2. If any
        other keys are present, or if the key `"data"` is not prsent, it is
        assumed to be of form 1, and all keys are assumed to be codes or column
        names.

        *NB!* Note that keys are case-sensitive. The metadata keys should
        generally be lowercase.
        
        Parameters
        ----------
        yamlfile : str or Path
            YAML file to read from, either as a `str` or `pathlib.Path` instance
            giving the path/filename of the file, or a `TextIO` stream.
        key : hashable, or sequence of hashable, optional
            Key(s) for item to read the definitions from in the YAML file. The
            method will use the key to retrieve an item from the dict returned
            when reading the YAML file, and process that item rather than
            processing from the root of the YAML file. If `key` is a list, the
            elements will be used to get the item from a nested dict. Note that
            in order to get nested items, `keys` must not be a hashable
            container, so you should provide a `list`, not a `tuple` or other
            immutable container, or `key` may be interpreted as just a single-
            level key.
        orient : `'index'` or `'columns'`
            Orientation to read the YAML file dictionary into a DataFrame. Works
            like the `orient` parameter of `pandas.DataFrame.from_dict`.
            Optional. If not specified, the value will be read from the element
            with key `orient` in the YAML file if a metadata block is present.
            If not, `'index'` is used as the default.

        Returns
        -------
        LabelMap
        """
        yamlstream: tp.TextIO
        with open(yamlfile, mode='r') as yamlstream:
            _def: tp.Dict[tp.Hashable, tp.Any] = yaml.safe_load(yamlstream)
        if key:
            if isinstance(key, tp.Hashable):
                _def = _def[key]
            else:
                for _key in key:
                    _def = _def[_key]
        # Check whether or not we have a metadata block
        if set(_def.keys()).issubset(cls._yaml_meta_keys) and \
                cls._yaml_data_key in _def.keys():
            if orient is None:
                if 'orient' in _def.keys():
                    orient = _def['orient']
                else:
                    orient = 'index'
            return cls(_def[cls._yaml_data_key], orient=orient)
        else:
            if orient is None:
                orient = 'index'
            return cls(_def, orient=orient)
    ###END def classmethod LabelMap.from_yaml

    def map_pd(
        self,
        pdobj: tp.Union[pd.Series, pd.Index],
        map_from: str,
        map_to: str = 'index',
        raise_on_missing: bool = True
    ) -> tp.Union[pd.Series, pd.Index]:
        """Map the values of a pandas `Series` or `Index`.
        
        Parameters
        ----------
        pdobj : pandas.Series or pandas.Index
            The pandas object to map
        map_from : str
            The column name in the internal DataFrame of `self` to map from, or
            `'index'` if mapping from the index codes (in which case the name of
            the index can also be used, as given by `self.code_col_name`).
        map_to : str, optional
            The column name with values to map to (or `'index'` if mapping to
            the index values, alternatively the index name /
            `self.code_col_name`). Optional, defaults to `'index'`.
        raise_on_missing : bool, optional
            Whether to raise a `KeyError` if any values in `pdobj` are not
            present in the internal DataFrame column specified by `map_from`. If
            False, missing values will map to `NA`. Optional, True by default.

        Returns
        -------
        pandas.Series or pandas.Index
            A new pandas object with the mapped values.
        """
        mapper: pd.Series
        mapping_df = self.get_df()
        index_aliases: tp.Tuple[str, ...] = ('index', self.code_col_name)
        if map_from in index_aliases:
            if map_to in index_aliases:
                mapper = pd.Series(data=mapping_df.index, index=mapping_df.index)
            else:
                mapper = mapping_df.reset_index()[map_to]
        elif map_to in index_aliases:
            mapper = mapping_df[map_from].reset_index().set_index(map_from)
        else:
            mapper = mapping_df[[map_to, map_from]].set_index(map_from, append=False)
        if not raise_on_missing:
            return pdobj.map(mapper)
        else:
            na_locs: pd.Series = pdobj.isna()
            # `mapper` is a 1-column DataFrame, must be turned into a Series by
            # selecting just the first (and only) column.
            mapped_obj: tp.Union[pd.Series, pd.Index] = \
                pdobj.map(mapper.iloc[:,0])
            if not np.array_equal(mapped_obj.isna(), na_locs, equal_nan=True):
                raise KeyError(
                    'Not all values in `pdobj` are present in values to be '
                    'mapped from.'
                )
            else:
                return mapped_obj
    ###END def LabelMap.map_pd

    def map_pd_index(
        self,
        pdobj: tp.Union[pd.DataFrame, pd.Series],
        map_from: str,
        map_to: str = 'index',
        axis: tp.Literal['index', 'columns'] = 'index',
        level: tp.Union[int, str] = None,
        raise_on_missing: bool = True,
        inplace: bool = False
    ) -> tp.Union[pd.DataFrame, pd.Series]:
        """Map the values of the index or columns of a DataFrame or Series
        
        The function maps values in a similar manner to `map_pd`, but maps the
        index or columns of a pandas DataFrame or Series instead of the values
        of the DataFrame/Series itself, and returns a new DataFrame/Series with
        the same values as the original, but altered index/column values.

        Parameters
        ----------
        pdobj : panas.DataFrame or pandas.Series
            The pandas object for which to map the index or columns
        map_from : str
            Column of the internal DataFrame with the values to map from, or
            `'index'` if mapping from the index. Same as the corresponding
            parameter of `map_pd`.
        map_to : str, optional
            Column of the internal DataFrame with values to map to, or
            `'index'`. Optional, defaults to `'index'`.
        axis : `'index'` or `'columns'`, optional
            Whether to map the index or column values of `pdobj`. Optional,
            `'index'` by default.
        level : int or str
            Which level to map, in the case of a MultiIndex. Will raise a
            `TypeError` if the index being mapped is not a MultiIndex. If None
            or not specified, all levels will be mapped. Note that this
            parameter is not truly optional. It will default to None and must
            not be specified if the index is not a MultiIndex, but is mandatory
            if the index *is* a MultiIndex. In that case, a `ValueError` will be
            raised if the parameter is not specified.
        raise_on_missing : bool, optional
            Whether to raise a `KeyError` if any values in `pdobj` (or the
            specified level of `pdobj`) are not present in the internal
            DataFrame column specified by `map_from`. If False, missing values
            will map to `NA`. Optional, True by default.
        inplace : bool, optional
            Whether to change the index of `pdobj` inplace. A best effort will
            be made to make the change on the original `pandas` object and
            return it, but it cannot be completely guaranteed that a copy will
            not still be made internally by pandas. If you need to be certain
            that the pandas object is still the same, use the `id()` built-in
            function to compare the object before and after the mapping.
            Optional, False by default.

        Returns
        -------
        pandas.DataFrame or pandas.Series
            New pandas object with the same values as `pdobj` but mapped index
            or column values.

        Raises
        ------
        TypeError
            If the specified index is not a MultiIndex, but `level` is
            specified, or if `level` is not a string or int.
        ValueError
            If the specified index is a MultiIndex, but `level` is not specified
        """
        # Get the index to map
        indexobj: pd.Index = getattr(pdobj, axis)
        if level is None and isinstance(indexobj, pd.MultiIndex):
            raise ValueError('`level` must be specified for a MultiIndex.')
        if level is not None and not isinstance(indexobj, pd.MultiIndex):
            raise TypeError(
                'Only MultiIndexes are accepted when `level` is not None'
            )
        if level is not None:
            if isinstance(level, str):
                level = indexobj.names.index(level)
            if not isinstance(level, int):
                raise TypeError(
                    '`level` must be an int (level number) or str (level name)'
                )
            indexobj = indexobj.levels[level]
        mapped_indexobj: pd.Index = self.map_pd(
            indexobj,
            map_from=map_from,
            map_to=map_to,
            raise_on_missing=raise_on_missing
        )
        # Assign the new index, either to a copy of `pdobj`` or the original,
        # depending on the value of `inplace`.
        if inplace:
            pdobj = pdobj.copy(deep=False)
        if level is None:
            setattr(pdobj, axis, mapped_indexobj)
        else:
            new_multiindex: pd.MultiIndex = \
                getattr(pdobj, axis) \
                    .set_levels(levels=mapped_indexobj, level=level)
            setattr(pdobj, axis, new_multiindex)
        return pdobj
    ###END def LabelMap.map_pd_index

###END class LabelMap
