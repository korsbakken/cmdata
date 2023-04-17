"""Plotting functionality for the CICERO Climate Mitigation group."""

# Try to import hv_plotting. If this results in an ImportError, some requisite
# packages are probably not installed.
import typing as tp

submodule_import_errors: tp.Dict[str, Exception] = dict()

try:
    from . import hv_plotting
except ImportError as ie:
    submodule_import_errors['hv_plotting'] = ie
