from html import escape

from xarray.core.formatting_html import (
    _obj_repr,
    attr_section,
    coord_section,
    datavar_section,
    dim_section,
)


def group_section():
    raise NotImplementedError


def node_repr(dt: "DataTree") -> str:
    obj_type = f"xarray.{type(dt).__name__}"

    header_components = [f"<div class='xr-obj-type'>{escape(obj_type)}</div>"]

    ds = dt.ds
    sections = [
        dim_section(ds),
        coord_section(ds.coords),
        datavar_section(ds.data_vars),
        attr_section(ds.attrs),
    ]

    return _obj_repr(ds, header_components, sections)


def datatree_repr(dt: "DataTree") -> str:
    return node_repr(dt)
