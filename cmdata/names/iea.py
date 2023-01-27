"""Names to be used with IEA datasets.

So fra only contains a data class of dimension names to be used consisently
across all IEA data sets.
"""

import typing as tp
from dataclasses import dataclass

@dataclass(frozen=True, kw_only=True)
class DimNames:
    TIME: str = 'time'
    REGION: str = 'region'
    FLOW: str = 'flow'
    PRODUCT: str = 'product'
    UNIT: str = 'unit'
    GAS: str = 'gas'
    ALLOCATION: str = 'allocation'
###END class dataclass DimNames
dim_names: DimNames = DimNames()
    
