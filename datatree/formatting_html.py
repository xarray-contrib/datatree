from html import escape
from functools import partial
from typing import Mapping

from xarray.core.formatting_html import (
    _obj_repr,
    attr_section,
    coord_section,
    datavar_section,
    dim_section,
    _mapping_section,
)

from xarray.core.options import OPTIONS

OPTIONS['display_expand_groups'] = "default"


def summarize_children(children: Mapping[str, "DataTree"]) -> str:
    children_li_elements = [
        f"<ul class='xr-sections'>{group_repr(n, c)}</ul>"
        for n, c in children.items()
    ]

    children_li = "".join(
        children_li_elements
    )
    return (
        "<ul class='xr-sections'>"
        f"<div style='padding-left:2rem;'>{children_li}<br></div>"
        "</ul>"
    )


children_section = partial(
    _mapping_section,
    name="Groups",
    details_func=summarize_children,
    max_items_collapse=1,
    expand_option_name="display_expand_groups",
)


def group_repr(group_name: str, dt: "DataTree") -> str:
    header_components = [f"<div class='xr-obj-type'>{escape(group_name)}</div>"]

    ds = dt.ds
    children = {c.name: c for c in dt.children}

    sections = [
        children_section(children),
        dim_section(ds),
        coord_section(ds.coords),
        datavar_section(ds.data_vars),
        attr_section(ds.attrs),
    ]

    return _obj_repr(ds, header_components, sections)


def datatree_repr(dt: "DataTree") -> str:
    obj_type = f"datatree.{type(dt).__name__}"

    header_components = [f"<div class='xr-obj-type'>{escape(obj_type)}</div>"]

    ds = dt.ds
    children = {c.name: c for c in dt.children}

    sections = [
        children_section(children),
        dim_section(ds),
        coord_section(ds.coords),
        datavar_section(ds.data_vars),
        attr_section(ds.attrs),
    ]

    return _obj_repr(ds, header_components, sections)
