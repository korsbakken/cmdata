"""Xarray-related functionality for IEA datasets.

For now, this module mostly just contains functionality for working with
existing IEA xarray data structures. The xr_data.iea package under
gcp_china_regression is used to read CSV files and create those data structures.
In time, that functionality should be moved to here and other appropriate
locations in the `cmdata` package."""
import typing as tp

import xarray as xr
import pandas as pd

from ..labels import iea as iealabels
from .. import helpers


# Check that xr_utils.XrExtsel has been registered, or register it if
# necessary.
if not helpers.xr_utils.registered_name(helpers.xr_utils.XrExtsel):
    helpers.xr_utils.register_extsel()


# Get dimension names
from ..names import iea
DN: iea.DimNames
from ..names.iea import dim_names as DN


def add_hierarchy(
    xrobj: tp.Union[xr.Dataset, xr.DataArray],
    dataset_id: str,
    dim: tp.Union[str, tp.Sequence[str]] = None,
    hierarchy_labelsets: tp.Mapping[str, str] = None
) -> tp.Union[xr.Dataset, xr.DataArray]:
    """Add hierarchy coordinates to an IEA xarray Dataset/DataArray.

    For each available dimension, adds two coordinate varaibles, which by
    default will have names `<dim>_level` and `<dim>_parent`, where `<dim>` is
    the name of the dimension in question. These contain:
        * `<dim>_level`: The level in the hierarchy of each element along the
          dimension. This is 1 for the top-level (usually total) value, and 2
          for each element directly below that (such as ELECHEAT, OTHEN, and
          TFC, for the GHG_bigco2 dataset).
        * `<dim>_parent`: The parent element. All elements at a given level
          should sum up to the value of the parent element (though this is not
          100% guaranteed, can depend on the dataset).
    Usually, memo elements will have level 99. If there is a natural parent for
    the memo element (i.e., if the memo element is entirely contained within a
    single element), the parent is labelled as `MEMO_<parent>`, where `<parent>`
    is the name of the natural parent element.

    A new object with the added coordinates is returned, they are not added in
    place.
    
    Parameters
    ----------
    xrobj : xarray.Dataset or xarray.DataArray
        The xarray object to add the hierarchy coordinates to.
    dataset_id : str
        The dataset id for the dataset contained in `xrobj`. It must match an
        available file id in `labels.iea`.
    dim : str or sequence of str, optional
        The dimension name or names to add hierarchy elements for. Currently,
        only `flow` is supported. Requires that there is hierarchy information
        in `labels.iea` for the given dimension. Optional, will add for all
        available dimensions (for which hierarchy information exists in
        `labels.iea`) if not specified. Note that even if hierarchy information
        is added in the label file for the given dataset in `labels.iea`, the
        code for this function must be updated to reflect that. It is currently
        not autodetected (although functionality to do so may be added in the
        future).
    hierarchy_labelsets: mapping str -> str, or callable
        Mapping from dimension name to the name of the labelset in the label
        file for the given dataset (`dataset_id`) that contains the hierarchy
        information for the given dimension. Optional. By default,
        `'_hierarchy'` will be suffixed to the dimension name(s) in `dim`.
    """
    if dim is None:
        dim = [DN.FLOW]
    _dim: str
    if any([not isinstance(_dim, str) for _dim in dim]):
        raise TypeError('All elements in `dim` must be strings.')
    for _dim in dim:
        if not _dim in xrobj.dims:
            raise ValueError(
                f'The xarray object does not contain the dimension `{_dim}`.'
            )
    if isinstance(dim, str):
        dim = [dim]
    _currdim: str
    if hierarchy_labelsets is None:
        hierarchy_labelsets: tp.Dict[str, str] = dict()
    for _currdim in dim:
        if not _currdim in hierarchy_labelsets:
            hierarchy_labelsets[_currdim] = f'{_currdim}_hierarchy'
        _labelset: str = hierarchy_labelsets[_currdim]
        # Get the DataFrame with levels and parents, then rename the columns
        # to have the desired coordinate names, and the index to have the same
        # as the dimension, so that the DataFrame can easily be imported back
        # into the dataset.
        _labeldf: pd.DataFrame = iealabels.get_label_map(
            dataset_id, _labelset
        ).get_df() \
            .rename(
                columns={
                    'level': f'{_currdim}_level',
                    'parent': f'{_currdim}_parent'
                }
            ) \
                .rename_axis(index=_currdim)
        xrobj = xrobj.assign_coords(_labeldf)
    return xrobj
###END def add_hierarchy
