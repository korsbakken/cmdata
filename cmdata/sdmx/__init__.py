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
    import sdmx as sdmx
elif sdmx_package == SDMXPackage.PANDASDMX:
    import pandasdmx as sdmx
else:
    raise RuntimeError('Internal error, flag to specify SDMX package is not '
                       'set correctly.')

from . import legacy_connect


def get_legacy_server_connect_sdmx_client(*args, **kwargs) -> sdmx.Client:
    """Get an SDMX Client with support for SSL legacy server connect.
    
    Parameters
    ----------
    *args, **kwargs
        Arguments to pass to `sdmx.Client`

    Returns
    -------
    sdmx.Client
    """
    client: sdmx.Client = sdmx.Client(*args, **kwargs)
    client.session.mount(
        'https://',
        legacy_connect.LegacyServerConnectAdapter()
    )
    return client
