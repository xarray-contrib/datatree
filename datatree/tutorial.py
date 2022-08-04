from __future__ import annotations

import os
import pathlib
import typing

from .datatree import DataTree
from .io import open_datatree as _open_datatree

_default_cache_dir_name = "xarray_datatree_data"
base_url = "https://carbonplan-share.s3.us-west-2.amazonaws.com/xarray-datatree"


SAMPLE_DATASETS = {
    "cesm2-lens": "cesm2-lens.nc",
    "cmip6": "cmip6.nc",
}


def _construct_cache_dir(path):
    import pooch

    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    elif path is None:
        path = pooch.os_cache(_default_cache_dir_name)

    return path


def open_datatree(
    name: typing.Literal["cesm2-lens", "cmip6"],
    cache_dir: str | pathlib.Path | None = None,
    *,
    engine: str = "netcdf4",
    **kwargs,
) -> DataTree:
    """
    Open a datatree from the xarray-datatree online repository (requires internet access).

    Parameters
    ----------
    name : str
        The name of the datatree to open. Valid names are

         * ``'cesm2-lens'``
         * ``'cmip6'``


    cache_dir : str | pathlib.Path
        The directory to cache the datatree in. If None, the default cache directory is used.
    engine : str
        The engine to use for the datatree.
    kwargs : dict
        Additional keyword arguments to pass to the xarray.open_dataset function.
    """
    try:
        import pooch
    except ImportError as e:
        raise ImportError(
            "pooch is required to download and open sample datasets.  To proceed please install pooch using: `python -m pip install pooch` or `conda install -c conda-forge pooch`."
        ) from e

    logger = pooch.get_logger()
    logger.setLevel("WARNING")
    cache_dir = _construct_cache_dir(cache_dir)
    try:
        path = SAMPLE_DATASETS[name]
    except KeyError as exc:
        raise KeyError(
            f"{name} is not a valid sample dataset. Valid names are {list(SAMPLE_DATASETS.keys())}"
        ) from exc

    url = f"{base_url}/{path}"
    asset_path = pooch.retrieve(url=url, known_hash=None, path=cache_dir)
    return _open_datatree(asset_path, engine=engine, **kwargs)
