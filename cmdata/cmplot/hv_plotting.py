"""Module for plotting based on holoviews, with data in xarray structures.

Currently uses matplotlib as the dfault backend, to produce plots suitable for
presentations and static formats. Rendering with other backends is sometimes
supported, but is generally not tested, and may not produce expected results.

The module usually expects data to be stored in xarray `DataArray` or `Dataset`
objects.
"""
from __future__ import annotations
import typing as tp
import dataclasses

import holoviews as hv
import matplotlib as mplt
import xarray as xr


# Define convenience types
XrData: tp.TypeAlias = tp.Union[xr.DataArray, xr.Dataset]
XrDataTypeVar = tp.TypeVar('XrDataTypeVar', bound=XrData)
NumType: tp.TypeAlias = tp.Union[int, float]
HvOptsType: tp.TypeAlias = tp.Union[tp.Mapping[str, tp.Any], hv.Options]
HvColor: tp.TypeAlias = tp.Union[str, tp.Tuple[float, float, float]]


def plot_lines(
    plotdata: XrData,
    x: tp.Hashable,
    y: tp.Optional[tp.Hashable] = None,
    hue: tp.Optional[tp.Hashable] = None,
    colormap: tp.Optional[
        tp.Dict[tp.Hashable, HvColor]
    ] = None,
    add_total: tp.Union[bool, tp.Hashable] = False,
    total_code: tp.Hashable = 'TOTAL',
    total_label: str = 'Total',
    legend_labels: tp.Optional[tp.Mapping[tp.Hashable, str]] = None,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    xlim: tp.Optional[tp.Tuple[NumType, NumType]] = None,
    ylim: tp.Optional[tp.Tuple[NumType, NumType]] = None,
    xticks: tp.Optional[tp.Sequence[tp.Hashable]] = None,
    yticks: tp.Optional[tp.Sequence[tp.Hashable]] = None,
    opts: tp.Optional[tp.Union[HvOptsType, tp.Sequence[HvOptsType]]] = None,
    backend: tp.Literal['matplotlib'] = 'matplotlib',
    legend_opts: tp.Optional[tp.Mapping[str, tp.Any]] = None,
    fig_size: int = 150,
    aspect: float = 1.5
) -> tp.Union[hv.NdOverlay, hv.Curve]:
    """Creates a line plot, with optionally overlaid lines."""

    # Make plotdata a Dataset if it isn't one already. If it is, make sure
    # that `y` is specified, since there is no `name` attribute to infer it
    # from
    if isinstance(plotdata, xr.DataArray):
        y = plotdata.name
        plotdata = plotdata.to_dataset()
    elif isinstance(y, xr.Dataset):
        if y is None:
            raise ValueError(
                '`y` must be specified when plotdata is an xarray.Dataset.'
            )
    else:
        raise TypeError(
            '`plotdata` must be an xarray `Dataset` or `DataArray`.'
        )
    
    # Add data and labels for total sum over the hue dim, if requested.
    if add_total:
        if isinstance(add_total, bool):
            add_total_dim: tp.Hashable = hue
        else:
            add_total_dim = add_total
        total_arr: xr.DataArray = plotdata[y].sum(
            dim=add_total_dim,
            keep_attrs=True
        ).expand_dims(
            dim={
                add_total_dim: [total_code]
            }
        )
        plotdata = xr.concat(
            objs=[total_arr.to_dataset(), plotdata],
            dim=add_total_dim
        )

        # If the hue dim is the one being summed over and legend labels are
        # specified, add the total to the legend labels. The total is added
        # to the *beginning*, since it will usually be greater than any of the
        # individual lines.
        if legend_labels and add_total_dim == hue:
            # Create legend_labels from scratch, to put the total label first
            legend_labels = {
                _key: _value for _key, _value in zip(
                    [total_code] + list(legend_labels.keys()),
                    [total_label] + list(legend_labels.values())
                )
            }

    # If legend labels are specified, rename the dimension values to match,
    # since the legend apparently will display dimension coordinate values.
    # Potentially, the `legend_labels` option could be used, but it does not
    # appear to work for the matplotlib extension (has no effect), as of
    # 2023-01-30, holoviews version 1.15.4.
    if legend_labels and hue in plotdata.dims:
        legend_label_coords, legend_label_values = \
            zip(*(legend_labels.items()))
        legend_labels_arr = xr.DataArray(
            data=list(legend_label_values),
            dims=(hue,),
            coords={
                hue: list(legend_label_coords)
            }
        )
        plotdata_origindex = plotdata.copy(deep=False)
        plotdata = plotdata.reindex_like(legend_labels_arr)
        plotdata = plotdata.assign_coords(
            {
                hue: legend_labels_arr
            }
        )
        # Since we have changed the dimension coordinate values of the hue
        # dimension, we also need to change the colormap keys accordingly
        if colormap:
            colormap = {
                _newkey: colormap[_oldkey] for _oldkey, _newkey in zip(
                    legend_label_coords,
                    legend_label_values
                )
            }

    # Create the holoviews Dataset to use for plotting
    hvds: hv.Dataset = hv.Dataset(
        data=plotdata,
        kdims=[x, hue],
        vdims=[y]
    )

    # Explicitly set values for the hue dimension, to ensure that it does not get
    # alphabetically sorted in the overlays and legends.
    hue_dim: hv.Dimension = hvds.get_dimension(hue)
    if legend_labels:
        hue_dim.values = list(legend_labels.values())
    else:
        hue_dim.values = plotdata[hue].to_numpy().tolist()

    # Define curve and point elements to be overlaid, and create a raw figure
    # object (NdOverlay) before applying matplotlib styling options.
    curves: hv.HoloMap = hvds.to(hv.Curve, kdims=x)
    points: hv.HoloMap = hvds.to(hv.Scatter, kdims=x)
    raw_fig: hv.Overlay = (curves*points).overlay(hue)

    # Set color options if needed
    colorlist: tp.List[HvColor]
    colorcycle: tp.Optional[hv.Cycle]
    if colormap:
        _huedimval: HvColor
        colorlist = [
            colormap[_huedimval] for _huedimval in hue_dim.values
        ]
        colorcycle = hv.Cycle(colorlist)
        raw_fig = tp.cast(hv.Overlay, raw_fig.options(
            hv.opts.Curve(color=colorcycle),
            hv.opts.Scatter(color=colorcycle)
        ))

    # Set matplotlib options. First set defaults, then update with the
    # legend_opts parameter if set.
    mplt_legend_opts: tp.Dict[str, tp.Any] = dict(
        loc='upper left',
        bbox_to_anchor=(1.05, 1.0),
        title_fontsize=0,
        frameon=False
    )
    if legend_opts:
        mplt_legend_opts.update(legend_opts)

    # Set default matplotlib options. First define a dict, then remove None-
    # valued items, to avoid passing None values to hv.opts.NdOverlay
    default_opts_dict: tp.Dict[str, tp.Any] = dict(
        aspect=aspect,
        fig_size=fig_size,
        xlim=xlim,
        ylim=ylim,
        xlabel=xlabel,
        ylabel=ylabel,
        xticks=xticks,
        yticks=yticks,
        legend_opts=mplt_legend_opts
    )
    for _key, _val in default_opts_dict.copy().items():
        if _val is None:
            del default_opts_dict[_key]
    mplt_opts: tp.Sequence[HvOptsType] = [
        hv.opts.NdOverlay(**default_opts_dict)
    ]
    if opts:
        if not isinstance(opts, tp.Sequence):
            opts = [opts]
        mplt_opts.extend(opts)

    ret_fig: hv.NdOverlay = tp.cast(hv.NdOverlay, raw_fig.options(mplt_opts))

    return ret_fig

###END def plot_lines


def plot_bar_stacked(
    plotdata: XrData,
    x: tp.Hashable,
    y: tp.Optional[tp.Hashable] = None,
    hue: tp.Optional[tp.Hashable] = None,
    colormap: tp.Optional[
        tp.Dict[tp.Hashable, HvColor]
    ] = None,
    add_total: tp.Union[bool, tp.Hashable] = False,
    total_code: tp.Hashable = 'TOTAL',
    total_label: str = 'Total',
    legend_labels: tp.Optional[tp.Mapping[tp.Hashable, str]] = None,
    xlabel: tp.Optional[str] = None,
    ylabel: tp.Optional[str] = None,
    xlim: tp.Optional[tp.Tuple[NumType, NumType]] = None,
    ylim: tp.Optional[tp.Tuple[NumType, NumType]] = None,
    xticks: tp.Optional[tp.Sequence[tp.Hashable]] = None,
    yticks: tp.Optional[tp.Sequence[tp.Hashable]] = None,
    opts: tp.Optional[tp.Union[HvOptsType, tp.Sequence[HvOptsType]]] = None,
    backend: tp.Literal['matplotlib'] = 'matplotlib',
    legend_opts: tp.Optional[tp.Mapping[str, tp.Any]] = None,
    fig_size: int = 150,
    aspect: float = 1.5
) -> tp.Union[hv.NdOverlay, hv.Curve]:
    """Creates a stacked bar plot, with optional dot showing the total."""

    # Make plotdata a Dataset if it isn't one already. If it is, make sure
    # that `y` is specified, since there is no `name` attribute to infer it
    # from
    if isinstance(plotdata, xr.DataArray):
        y = plotdata.name
        plotdata = plotdata.to_dataset()
    elif isinstance(y, xr.Dataset):
        if y is None:
            raise ValueError(
                '`y` must be specified when plotdata is an xarray.Dataset.'
            )
    else:
        raise TypeError(
            '`plotdata` must be an xarray `Dataset` or `DataArray`.'
        )
    
    # Add data and labels for total sum over the hue dim, if requested.
    if add_total:
        if isinstance(add_total, bool):
            add_total_dim: tp.Hashable = hue
        else:
            add_total_dim = add_total
        total_arr: xr.DataArray = plotdata[y].sum(
            dim=add_total_dim,
            keep_attrs=True
        ).expand_dims(
            dim={
                add_total_dim: [total_code]
            }
        )
        plotdata = xr.concat(
            objs=[total_arr.to_dataset(), plotdata],
            dim=add_total_dim
        )

        # If the hue dim is the one being summed over and legend labels are
        # specified, add the total to the legend labels. The total is added
        # to the *beginning*, since it will usually be greater than any of the
        # individual lines.
        if legend_labels and add_total_dim == hue:
            # Create legend_labels from scratch, to put the total label first
            legend_labels = {
                _key: _value for _key, _value in zip(
                    [total_code] + list(legend_labels.keys()),
                    [total_label] + list(legend_labels.values())
                )
            }

    # If legend labels are specified, rename the dimension values to match,
    # since the legend apparently will display dimension coordinate values.
    # Potentially, the `legend_labels` option could be used, but it does not
    # appear to work for the matplotlib extension (has no effect), as of
    # 2023-01-30, holoviews version 1.15.4.
    if legend_labels and hue in plotdata.dims:
        legend_label_coords, legend_label_values = \
            zip(*(legend_labels.items()))
        legend_labels_arr = xr.DataArray(
            data=list(legend_label_values),
            dims=(hue,),
            coords={
                hue: list(legend_label_coords)
            }
        )
        plotdata_origindex = plotdata.copy(deep=False)
        plotdata = plotdata.reindex_like(legend_labels_arr)
        plotdata = plotdata.assign_coords(
            {
                hue: legend_labels_arr
            }
        )
        # Since we have changed the dimension coordinate values of the hue
        # dimension, we also need to change the colormap keys accordingly
        if colormap:
            colormap = {
                _newkey: colormap[_oldkey] for _oldkey, _newkey in zip(
                    legend_label_coords,
                    legend_label_values
                )
            }

    # Create the holoviews Dataset to use for plotting
    hvds: hv.Dataset = hv.Dataset(
        data=plotdata,
        kdims=[x, hue],
        vdims=[y]
    )

    # Explicitly set values for the hue dimension, to ensure that it does not get
    # alphabetically sorted in the overlays and legends.
    hue_dim: hv.Dimension = hvds.get_dimension(hue)
    if legend_labels:
        hue_dim.values = list(legend_labels.values())
    else:
        hue_dim.values = plotdata[hue].to_numpy().tolist()

    # Define curve and point elements to be overlaid, and create a raw figure
    # object (NdOverlay) before applying matplotlib styling options.
    # curves: hv.HoloMap = hvds.to(hv.Curve, kdims=x)
    bars: hv.HoloMap = hvds.to(
        hv.Bars,
        kdims=[x, hue]
    )
    raw_fig = bars
    # points: hv.HoloMap = hvds.to(hv.Scatter, kdims=x)
    # raw_fig: hv.Overlay = (curves*points).overlay(hue)
    # raw_fig: hv.Overlay = bars.overlay(hue)

    # Set color options if needed
    colorlist: tp.List[HvColor]
    colorcycle: tp.Optional[hv.Cycle]
    if colormap:
        _huedimval: HvColor
        colorlist = [
            colormap[_huedimval] for _huedimval in hue_dim.values
        ]
        colorcycle = hv.Cycle(colorlist)
        raw_fig = raw_fig.options(
            # hv.opts.Curve(color=colorcycle),
            # hv.opts.Scatter(color=colorcycle)
            hv.opts.Bars(color=colorcycle)
        )

    raw_fig = raw_fig.options(hv.opts.Bars(stacked=True))

    # Set matplotlib options. First set defaults, then update with the
    # legend_opts parameter if set.
    mplt_legend_opts: tp.Dict[str, tp.Any] = dict(
        loc='upper left',
        bbox_to_anchor=(1.05, 1.0),
        title_fontsize=0,
        frameon=False
    )
    if legend_opts:
        mplt_legend_opts.update(legend_opts)

    # Set default matplotlib options. First define a dict, then remove None-
    # valued items, to avoid passing None values to hv.opts.NdOverlay
    default_opts_dict: tp.Dict[str, tp.Any] = dict(
        aspect=aspect,
        fig_size=fig_size,
        xlim=xlim,
        ylim=ylim,
        xlabel=xlabel,
        ylabel=ylabel,
        xticks=xticks,
        yticks=yticks,
        legend_opts=mplt_legend_opts
    )
    for _key, _val in default_opts_dict.copy().items():
        if _val is None:
            del default_opts_dict[_key]
    mplt_opts: tp.Sequence[HvOptsType] = [
        hv.opts.Bars(**default_opts_dict)
    ]
    if opts:
        if not isinstance(opts, tp.Sequence):
            opts = [opts]
        mplt_opts.extend(opts)

    # ret_fig: hv.NdOverlay = raw_fig.options(mplt_opts)
    ret_fig = raw_fig

    return ret_fig

###END def plot_lines
