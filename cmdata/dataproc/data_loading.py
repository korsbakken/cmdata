"""Abstract base classes and basic functionality for loading data files."""
from __future__ import annotations

import typing as tp
import enum
from pathlib import Path
from abc import ABC, abstractmethod, abstractproperty

import pandas as pd

from .configparsers import PathConfigParser


# Custom type definitions

# Custom types used by PandasDataLoader
ColumnAdjustment = tp.Callable[[pd.Series], pd.Series]
GlobalAdjustment = tp.Callable[[pd.DataFrame], pd.DataFrame]
ClosedIntervalSpec = tp.Literal['left', 'right', 'both', 'neither']



@enum.unique
class DataReprType(enum.Enum):
    """Enums to identify type of data representation.
    
    These enums will typically be used to specify what type of object will be
    returned by functions that fetch data sets, e.g., a pandas DataFrame or an
    xarray DataArray/Dataset.

    Attributes
    ----------
    PD : enum
        Pandas data structure (i.e., `pandas.DataFrame` or `pandas.Series`)
    XR : enum
        Xarray data structure (i.e., `xarray.Dataset` or `xarray.DataArray`)
    NP : enum
        Numpy array
    CUST : enum
        Custom data structure (typically used in user-defined subclasses that
        represent data with a different type than any of the "usual" ones).
    """
    PD = 'pd'
    XR = 'xr'
    NP = 'np'
    CUST = 'custom'
###END class DataReprType


class DataConfig(PathConfigParser):
    """Base class for loading and holding configuration for data files."""
    
    def __init__(
        self,
        config_file: tp.Optional[tp.Union[Path, str]] = None,
        config_str: tp.Optional[str] = None,
        encoding: tp.Optional[str] = None,
        root_path_option_name: str = 'root_path',
        root_path: tp.Optional[Path] = None,
        **kwargs
    ):
        """
        Parameters
        ----------
        config_file : Path or str
            Configuration file to read. Can be left unspecified (None) if
            `config_str` is given.
        config_str : str, optional
            String with configuration to use. Must have the same format
            (including newlines and indentations) as the contents of a
            configuration file. Optional. If both `config_str` and `config_file`
            are specified, they will be read as separate configuration files,
            and the contents of `config_str` will override `config_file` where
            they overlap.
        encoding : str, optional
            The encoding of the contents of `config_file`. Will be passed to
            `configparser.ConfigParser.read` to read the file.
        root_path_option_name : str, optional
            Option name used for the default root path. Optional, uses the class
            attribute `_DEFAULT_ROOT_PATH_OPTION` by default.
        root_path : Path
            Default root path (as a Path instance) to set on the instance.
            Optional, defaults to `None`. If set, it will override any value
            that might be set in the default section of configuration files that
            are later read. If not set, the instance will first try to read it
            from the default setion of any file that is read, with the `read`
            method. If not present in the configuration file, the directory that
            contains the file will be used.
        **kwargs
            Additional keyword arguments to pass to the `__init__` method of
            `PathConfigParser`. Should usually not be specified unless the
            configuration file has a different format than the class expects
            by default.
        """
        super().__init__(
            root_path_option_name=root_path_option_name,
            root_path=root_path,
            **kwargs
        )
        if config_file:
            self.read(config_file, encoding=encoding)
        elif config_str is None:
            raise ValueError(
                'Either `config_file` or `config_str` must be specified.'
            )
        if config_str:
            self.read_string(config_str)
    ###END def DataConfig.__init__


###END class DataConfig


class DataLoader(ABC):
    """Abstract base class for loading and processing raw and cached data."""

    __slots__ = ('data_config', )

    @abstractproperty
    def data_processor(self) -> tp.Union[
        tp.Mapping[DataReprType, tp.Callable],
        tp.Callable
    ]:
        """Property that provides a method to be used for processing raw data,
        or a mapping from `DataReprType` to callables that provides functions to
        be used to turn raw data into each type of data representation.
        
        The function(s) will be called by `self.load_raw_dataset`, and will be
        given only keyword arguments, as follows:

        Parameters
        ----------
        raw_data : any
            Raw data object to be processed, type is determined by
            implementation. When called by `self.load_raw_dataset`, it will be
            equal to the return value of `self.read_raw_datafiles`.
        caller : DataLoader
            The calling object itself. Will always be set when called by
            `self.load_raw_dataset`.
        data_config : DataConfig
            The configuration used by the calling method. Will be equal to the
            `data_config` parameter of `self.load_raw_dataset` when called by
            that method (which defaults to `self.data_config`).
        **kwargs
            Additional keyword arguments. Will be equal to the contents of the
            parameter `data_processor_kwargs` when called by
            `self.load_raw_dataset`.
        """
        raise NotImplementedError(
            '`data_processor` must be implemented by subclasses, either as a '
            'function or as a dictionary from `DataReprType` to callables.'
        )
    ###END def abstractproperty data_processor

    def __init__(
        self,
        data_config: tp.Optional[tp.Union[DataConfig, Path]] = None,
        data_config_str: tp.Optional[str] = None
    ):
        """
        Parameters
        ----------
        data_config : DataConfig or Path, optional
            `DataConfig` instance with configuration for the data, or `Path`
            representing a configuration file to be read with `DataConfig.read`.
        data_config_str : str, optional
            Optional string with configuration file contents. Overrides contents
            of `data_config` where they overlap, if both are specified.
        """
        self.data_config: DataConfig = self.resolve_config(
            data_config=data_config,
            data_config_str=data_config_str,
            allow_empty=True
        )
    ###END def DataLoader.__init__

    class NoDataConfigError(Exception):
        """Exception if no data config or config string has been specified."""
        pass
    ###END class DataLoader.NoDataConfigError

    @classmethod
    def resolve_config(
        cls,
        data_config: tp.Optional[tp.Union[DataConfig, Path]] = None,
        data_config_str: tp.Optional[str] = None,
        allow_empty: bool = False
    ) -> DataConfig:
        """Resolve `data_config` and `data_config_str` options into a
        `DataConfig` instance.

        Parameters
        ----------
        data_config : DataConfig or Path, optional
            `DataConfig` instance with configuration for the data, or `Path`
            representing a configuration file to be read with `DataConfig.read`.
        data_config_str : str, optional
            Optional string with configuration file contents. Overrides contents
            of `data_config` where they overlap, if both are specified.
        allow_empty : bool, optional
            Whether to allow both `data_config` and `data_config_str` to be
            empty. If True and if they are, a `DataConfig` instance with no
            configuration options will be returned, and no error raised. If
            False and neither `data_config` nor `data_config_str` are
            specified, a `DataLoader.NoDataConfigError` will be raised.
        """
        if isinstance(data_config, Path):
            data_config = DataConfig(config_file=data_config)
        elif data_config is None:
            if data_config_str is None:
                if allow_empty:
                    return DataConfig(config_str='')
                else:
                    raise cls.NoDataConfigError(
                        'Either `data_config` or `data_config_str` must be '
                        'specified.'
                    )
            data_config = DataConfig(config_str=data_config_str)
        elif not isinstance(data_config, DataConfig):
            raise TypeError(
                '`data_config` must be a `DataConfig` or a `Path` instance.'
            )
        else:
            # Now we know that we have a `DataConfig` instance. Read
            # `data_config_str` in case there is additional config to be read
            # there.
            if data_config_str is not None:
                data_config.read_string(data_config_str)
        return data_config
    ###END def classmethod DataLoader.resolve_config

    def load_raw_dataset(
        self,
        data_config: tp.Optional[DataConfig] = None,
        cache_processed_data: bool = True,
        file_getter_kwargs: tp.Optional[tp.Dict[str, tp.Any]] = None,
        data_processor_kwargs: tp.Optional[tp.Dict[str, tp.Any]] = None,
        data_repr: tp.Optional[DataReprType] = None,
        **kwargs
    ) -> tp.Any:
        """Abstract method for loading a raw dataset, with base functionality.
        
        Parameters
        ----------
        data_config : DataConfig, optional
            `DataConfig` instance with configuration for the data. Optional,
            uses the `DataConfig` instance `self.data_config` assigned through
            the `__init__` method by defaults.
        data_repr : DataReprType
            Type of data representation object to be returned.
        cache_processed_data : bool = True
            Whether to store processed data in a cached version that can be
            read directly later without reprocessing the raw data files.
        file_getter_kwargs : dict from str to any, optional
            Keyword arguments to pass to `self.get_raw_datafile_paths`
            (abstract method to be implemented by subclasses).
        data_processor_kwargs : dict from str to any, optional
            Keyword arguments to pass to `self.data_processor` or the values of
            it.
        **kwargs
            Keyword arguments to pass to both `self.get_raw_datafile_paths` and
            `self.data_processor`. This is a convenience to avoid having to
            pass parameters as dictionaries, but requires that both functions
            can accept or ignore all keyword arguments that the other function
            expects, and that arguments with overlapping names always have the
            same value for both functions. NB! These keyword arguments will
            only be passed to those functions if the respective dictionary
            argument (`file_getter_kwargs` and `data_processor_kwargs`) is
            None.
        """
        if data_config is None:
            data_config = self.data_config
        # Resolve keyword arguments
        if file_getter_kwargs is None:
            file_getter_kwargs = kwargs.copy()
        if data_processor_kwargs is None:
            data_processor_kwargs = kwargs.copy()
        # Get the paths of the raw data files
        data_file_paths: tp.Union[Path, tp.Sequence[Path]] = \
            self.get_raw_datafile_paths(
                data_config=data_config,
                **file_getter_kwargs
            )
        # Read the data files
        raw_data = self.read_raw_datafiles(
            datafiles=data_file_paths,
            data_config=data_config
        )
        # Get the right data processor to use
        process_data: tp.Callable
        if isinstance(self.data_processor, tp.Mapping):
            if data_repr is None:
                raise ValueError(
                    '`data_repr` must be specified when `self.data_processor` '
                    'is given as a mapping from data representation type to '
                    'processor functions.'
                )
            try:
                process_data = self.data_processor[data_repr]
            except KeyError as ke:
                if (len(ke.args) != 1) or (ke.args[0] != data_repr):
                    raise ke
                raise KeyError(
                    f'`process_data` contains no entry for data '
                    f'representation type {data_repr}.'
                )
        else:
            process_data = self.data_processor
        processed_data = process_data(
            raw_data=raw_data,
            data_config=data_config,
            caller=self,
            **data_processor_kwargs
        )
        return processed_data
    ###END def DataLoader.load_raw_dataset

    @abstractmethod
    def get_raw_datafile_paths(
        self,
        data_config: tp.Optional[DataConfig] = None,
        **kwargs
    ) -> tp.Union[Path, tp.Sequence[Path]]:
        """Abstract  method for getting datafile paths.
        
        To be implemented by subclasses. Called by `load_raw_dataset` to find
        paths to requested raw data files.
        
        Parameters
        ----------
        data_config : DataConfig, optional
            Data configuration object. The method implementation should usually
            leave this parameter as optional, and use `self.data_config`
            by default.
        **kwargs
            Implementation-dependent keyword arguments used to specify what
            data to get, if required.

        Returns
        -------
        Path or sequence of Path
            Path(s) representing the raw data files with the required data.
        """
        pass
    ###END def DataLoader.get_raw_datafile_paths

    @abstractmethod
    def read_raw_datafiles(
        self,
        datafiles: tp.Union[Path, tp.Sequence[Path]],
        data_config: tp.Optional[DataConfig] = None
    ) -> tp.Any:
        """Abstract  method to read raw data files.
        
        To be implemented by subclasses. Called by `load_raw_dataset`. Needs
        to accept a Path instance or a sequence of Path instances as returned
        by `self.get_raw_datafile_paths`, and return a data object (data type
        is left up to the implementing subclass) that can be passed to the data
        processing function(s) used in that method.
        
        Parameters
        ----------
        datafiles : Path or Sequence of Path
            The data file(s) to read, as returned by `self.get_raw_datafiles`.
        data_config : DataConfig, optional
            Data configuration object. The implementing function should leave
            it as optional, and use `self.data_config` by default.

        Returns
        -------
        Any
            Implementation-dependent data structure with raw data.
        """
        pass
    ###END def abstractmethod DataLoader.read_raw_datafiles

###END class DataLoader

def set_nonna_if_not_present(
    obj: tp.Any,
    attr_name: str,
    attr_value: tp.Any,
    default_value: tp.Any,
    override_none: bool = False
) -> tp.Any:
    """Helper function to set attribute values that might already exist.
    
    The function sets the `attr_value` in the attribute given by `attr_name` if
    `attr_value` is specified, or sets a default value if `attr_value` is None
    *and* the attribute does not exist already.
    
    Parameters
    ----------
    obj : any
        The object to set the attribute on
    attr_name : str
        Name of the attribute to set
    attr_value : any
        The value to set
    default_value : any
        The value to set if `attr_value` is None, *and* `obj` does not already
        have an attribute with the name given by `attr_name` (i.e., if
        `hasattr(obj, attr_name)` is False).
    override_none : bool, optional
        Whether to set `default_value` if `obj` has the attribute, but it is
        currently None. Optional, by default False.

    Returns
    -------
    The value that was set, if any. Returns None if the existing value was kept.
    """
    if attr_value is not None:
        setattr(obj, attr_name, attr_value)
        return attr_value
    else:
        if not hasattr(obj, attr_name) or (override_none and (getattr(obj, attr_name) is None)):
            setattr(obj, attr_name, default_value)
            return default_value
        else:
            return None
###END set_nonna_if_not_present

class PandasDataLoader(DataLoader):
    """DataLoader class for processing tabular/CSV-style data to DataFrames.
    
    This subclass provides extra functionality and implements some abstract
    methods of `DataLoader`, but not all. The class must therefore be
    subclassed by a class that implements the remaining abstract methods before
    being instantiated. Remaining abstract methods include:

      * `get_raw_datafile_paths`
      * `data_processor`

    Also, the `read_raw_datafiles` simply reads a list of CSV files into
    DataFrames with `pandas.read_csv` without any custom arguments, and
    concatenates the DataFrames together in order of appearance. If any
    customized behavior is needed, `read_raw_datafiles` will also need to be
    overridden in a subclass.
    """

    __slots__ = (
        'source_data_dtypes',
        'data_index_cols',
        'global_preadjustments',
        'column_adjustments',
        'global_postadjustments'
    )

    def __init__(
        self,
        data_config: tp.Optional[tp.Union[DataConfig, Path]] = None,
        data_config_str: tp.Optional[str] = None,
        source_data_dtypes: tp.Optional[tp.Mapping[str, tp.Union[str, type]]] \
            = None,
        data_index_cols: tp.Optional[tp.Sequence[str]] = None,
        global_preadjustments: tp.Optional[tp.Sequence[GlobalAdjustment]] = \
            None,
        column_adjustments: tp.Optional[
            tp.Mapping[
                tp.Hashable,
                tp.Union[ColumnAdjustment, tp.Sequence[ColumnAdjustment]]
            ]
        ] = None,
        global_postadjustments: tp.Optional[tp.Sequence[GlobalAdjustment]] = \
            None
    ):
        """
        Parameters
        ----------
        data_config : DataConfig or Path, optional
            `DataConfig` instance with configuration for the data, or `Path`
            representing a configuration file to be read with `DataConfig.read`.
        data_config_str : str, optional
            Optional string with configuration file contents. Overrides contents
            of `data_config` where they overlap, if both are specified.
        source_data_dtypes : mapping of str to str or type, optional
            dtypes to use for each column in the raw data (column names must be
            as returned by `self.read_raw_datafiles`).
        data_index_cols : sequence of str, optional
            Columns to set as index (column names must be those that are
            current after all other processing has been done).
        global_preadjustments : sequence of callables, optional
            Adjustments to make to the DataFrame after type conversion but
            before `column_adjustments`. Must be a sequence of functions that
            take a DataFrame as their only argument and return a DataFrame.
            Should typically be implemented by subclasses.
        column_adjustments : mapping from str to callable, optional
            Adjustments to make to individual columns, after `global_preadjustments`
            and before `global_postadjustments`. Must be a  mapping from column
            names to functions that take a single column (`pandas.Series`) and
            returns a Series of the same length and with the same index, or a
            sequence of such functions. Each will be called, and the result
            inserted into the DataFrame in place of the original column. For
            sequences of functions for a single column, the functions will be
            called in order. However, no assumptions should be made about the
            order in which the different columns are processed.
        global_postadjustments : sequence of callables, optional
            Adjustments to make to the whole DataFrame after other processing,
            before returning.
        """
        super().__init__(
            data_config=data_config,
            data_config_str=data_config_str
        )
        # Set source_data_dtypes and data_index_cols. If either are None,
        # first test whether `self` already has these attributes (e.g., if they
        # have been set by a subclass), and set to empty containers if not.
        # NB! The code below is now a somewhat inconsistent mix of setting
        # attributes directly and using `set_nonna_if_not_present` to do so.
        # The effect should be the same, but using `set_nonna_if_not_present`
        # has the drawback of being harder to analyze for type checking and
        # auto-completion.
        self.source_data_dtypes: tp.Dict[str, tp.Union[str, type]]
        set_nonna_if_not_present(
            self,
            attr_name='source_data_dtypes',
            attr_value=source_data_dtypes,
            default_value=dict()
        )
        self.data_index_cols: tp.List[str]
        set_nonna_if_not_present(
            self,
            attr_name='data_index_cols',
            attr_value=data_index_cols,
            default_value=list()
        )
        self.global_preadjustments: tp.Sequence[GlobalAdjustment]
        # self.column_adjustments: tp.Dict[
        #     tp.Hashable, tp.Union[
        #         tp.Sequence[ColumnAdjustment], ColumnAdjustment
        #     ]
        # ]
        self.global_postadjustments: tp.Sequence[GlobalAdjustment]
        set_nonna_if_not_present(
            self,
            attr_name='global_preadjustments',
            attr_value=global_preadjustments,
            default_value=list()
        )
        if column_adjustments is not None:
            self.column_adjustments = dict(column_adjustments)
            # self.column_adjustments = {
            #     _key: _adj if isinstance(_adj, tp.Sequence) else [_adj] for _key, _adj in column_adjustments.items()
            # }
        else:
            if not hasattr(self, 'column_adjustments'):
                self.column_adjustments = dict()
        # Ensure that `self.column_adjustments` has sequences of callables, and
        # and no scalars.
        # Then set a type hint, since we now know that all elements in
        # self.column_adjustments are sequences.
        for _key, _value in self.column_adjustments.items():
            if not isinstance(_value, tp.Sequence):
                self.column_adjustments[_key] = [_value]
        self.column_adjustments: tp.Dict[tp.Hashable, tp.Sequence[ColumnAdjustment]]
        if global_postadjustments is not None:
            self.global_postadjustments = global_postadjustments
        else:
            if not hasattr(self, 'global_postadjustments'):
                self.global_postadjustments = list()
    ###END def PandasDataLoader.__init__

    @staticmethod
    def process_raw_df(
        raw_data: pd.DataFrame,
        caller: PandasDataLoader,
        data_config: DataConfig
    ) -> pd.DataFrame:
        """Function to return a processed DataFrame from a raw data DataFrame.
        
        To be called by `self.load_raw_dataset`, but written as a static method
        because `self.load_raw_dataset` expects a function, not a method. `self`
        will be passed into the function through the `caller` parameter.
        
        Parameters
        ----------
        raw_data : pandas.DataFrame
            DataFrame with raw data, as returned by `read_raw_datafiles`.
        caller : PandasDataLoader
            The calling instance.
        data_config : DataConfig
            DataConfig configuration from the calling instance. Not necessarily
            used.

        Returns
        -------
        pandas.DataFrame
            Processed DataFrame, with dtypes set according to
            `caller.source_data_dtypes`, and index using columns specified in
            `caller.data_index_cols`.
        """
        # Get type conversion specs
        dtypes: tp.Mapping[str, tp.Union[str, type]] = \
            caller.source_data_dtypes
        _df: pd.DataFrame = raw_data.astype(dtypes)

        # Global and column-wise adjustments
        # First type definitions
        _global_adjustment: GlobalAdjustment
        _col_adjustments: tp.Sequence[ColumnAdjustment]
        global_preadjustments: tp.Sequence[GlobalAdjustment] = \
            caller.global_preadjustments
        column_adjustments: tp.Mapping[tp.Hashable, tp.Sequence[ColumnAdjustment]] = \
            caller.column_adjustments
        global_postadjustments: tp.Sequence[GlobalAdjustment] = \
            caller.global_postadjustments

        # Then make the adjustments
        for _global_adjustment in global_preadjustments:
            _df = _global_adjustment(_df)
        _colname: tp.Hashable
        for _colname, _col_adjustments in column_adjustments.items():
            _col_adjustment: ColumnAdjustment
            for _col_adjustment in _col_adjustments:
                _df[_colname] = _col_adjustment(_df[_colname])
            # Make a copy to remove any unnecessary fragmentation
            _df = _df.copy(deep=False)
        for _global_adjustment in global_postadjustments:
            _df = _global_adjustment(_df)
        
        index_cols: tp.Sequence[str] = caller.data_index_cols
        if index_cols:
            _df = _df.set_index(index_cols)

        return _df
    ###END def staticmethod PandasDataLoader.process_raw_df

    @property
    def data_processor(self) -> tp.Callable[
        [pd.DataFrame, PandasDataLoader, DataConfig],
        pd.DataFrame
    ]:
        return self.process_raw_df
    ###END def property PandasDataLoader.data_processor

    @staticmethod
    def set_intervals(
        df: pd.DataFrame,
        interval_cols: tp.Optional[tp.Mapping[str, tp.Tuple[str, str]]] = None,
        closed: tp.Optional[tp.Union[
            ClosedIntervalSpec,
            tp.Mapping[str, ClosedIntervalSpec]
        ]] = None,
        drop: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """Helper function to combines pairs of columns into single columns of
        dtype Interval.
        
        Parameters
        ----------
        df : pandas.DataFrame
            The DataFrame of columns to combine
        interval_cols : mapping of str to tuples of two strings each
            Mapping (e.g., dict) with the names of the new interval columns as
            keys and 2-element tuples of the names of the corresponding columns
            with left and right values (in that order) for the intervals.
        closed : mapping of str to `'right'`, `'left'`, `'both'` or `'neither'`
            Specifies which limits should be closed for each of the new interval
            columns. If `'interval_cols'` contains only a single element,
            `closed` can be a single str value. Optional, defaults to using the
            pandas default (currently `'right'`) for all columns.
        drop : bool, optional
            Whether to drop the original columns used as limits. Optional, True
            by default.
        **kwargs
            Keyword-argument form for `interval_cols`. *NB!* If both
            `interval_cols` and kwargs are given and contain overlapping keys,
            the values from `kwargs` will be used.

        Returns
        -------
        pandas.DataFrame
            A new (shallow-copied) DataFrame with combined colummns.
        """
        if interval_cols is None:
            interval_cols = kwargs
        interval_cols.update(kwargs)
        if isinstance(closed, str) or closed is None:
            if isinstance(closed, str) and len(interval_cols) > 1:
                raise ValueError(
                    '`closed` must be a mapping if more than one pair of columns '
                    'are being turned into intervals.'
                )
            _closed: tp.Optional[ClosedIntervalSpec] = closed
            closed = {
                k: _closed for k in interval_cols.keys()
            }
        _newcols: tp.List[pd.Series] = list()
        for target_col, source_cols in interval_cols.items():
            _newcols.append(
                pd.IntervalIndex.from_arrays(
                    left=df[source_cols[0]],
                    right=df[source_cols[1]],
                    closed=closed[target_col]
                ).to_series(
                    index=df.index,
                    name=target_col
                )
            )
        if drop:
            dropcols = [x[0] for x in interval_cols.values()] + \
                [x[1] for x in interval_cols.values()]
        else:
            dropcols = []
        newdf: pd.DataFrame = pd.concat(
            [
                df.drop(columns=dropcols),
                *_newcols,
            ],
            axis=1
        )
        return newdf
    ###END def staticmethod PandasDataLoader.set_intervals

    def _read_and_concat_datafiles(
        self,
        datafile_paths: tp.Union[Path, tp.Sequence[Path]],
        read_func: tp.Callable[[Path], pd.DataFrame],
        **kwargs
    ) -> pd.DataFrame:
        """Helper function to read multiple data files into DataFrames and
        return the concatenated result. Useful helper file for implementing a
        `read_raw_datafiles` method in subclasses.
        
        Parameters
        ----------
        datafile_paths : Path or sequence of Path
            The data file paths. Can also be just a single Path instance.
        read_func : callable
            Function that accepts a Path and optional keyword arguments, and
            returns a DataFrame. Will be used to read the data files into
            DataFrames to be concatenated. E.g., pass `pandas.read_csv` to
            read CSV files, or `pandas.read_excel` to read Excel files.
        **kwargs
            Optional keyword arguments, will be passed to `read_func` after a
            positional `Path` argument.
        """
        if isinstance(datafile_paths, Path):
            datafile_paths = [datafile_paths]
        elif not isinstance(datafile_paths, tp.Sequence):
            raise TypeError(
                '`datafile_paths` must be a Path or sequence of Path objects.'
            )
        _path: Path
        df_list: tp.List[pd.DataFrame] = list()
        for _path in datafile_paths:
            df_list.append(read_func(_path, **kwargs))
        return pd.concat(df_list, axis=0)
    ###END def PandasDataLoader._read_and_concat_datafiles

###END class PandasDataLoader
