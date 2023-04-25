"""Utilities to download and work with SDMX statistics data sources."""

import typing as tp
import enum

# Import an sdmx module, so it can be easily changed between pandasdmx and
# sdmx1 later, if needed.
class SDMXPackage(enum.StrEnum):
    SDMX1 = enum.auto()
    PANDASDMX = enum.auto()
###END class enum SDMXPackage

# Make sure that the import and `sdmx_package` are consistent
sdmx_package: SDMXPackage = SDMXPackage.SDMX1
if sdmx_package == SDMXPackage.SDMX1:
    import sdmx1 as sdmx
elif sdmx_package == SDMXPackage.PANDASDMX:
    import pandasdmx as sdmx
else:
    raise RuntimeError('Internal error, flag to specify SDMX package is not '
                       'set correctly.')

