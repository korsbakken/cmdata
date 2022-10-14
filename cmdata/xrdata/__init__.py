"""Base functionality for xarray-based data structures.

This package should be extended or used by datasource-/dataset-specific
packages. It includes base functionality for translating labels in xarray data
structures, and converting pandas data structures to xarray, and extensions for
standardizing and keeping track of dimension names.
"""

from .. import helpers
from ..labels import iea as iealabels
