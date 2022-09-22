"""Base functionality for processing pandas-based data structures.

This package should be extended or used by datasource-/dataset-specific
packages. It includes base functionality for manipulating pandas indexes and
reading CSV files (which should be overridden or extended by dataset-specific
functions in derived packages). The main objective is to munge data into a
format suitable for converting to xarray Datasts or DataArrays, which is the
preferred data structure for the `cmdata` package.
"""

