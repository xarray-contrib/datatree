from functools import partial
from html import escape
from typing import Any, Mapping

from xarray.core.formatting_html import (
    _mapping_section,
    _obj_repr,
    attr_section,
    coord_section,
    datavar_section,
    dim_section,
)
from xarray.core.options import OPTIONS

OPTIONS["display_expand_groups"] = "default"

def summarize_children(children: Mapping[str, Any]) -> str:
    children_html = "".join(
        _wrapped_node_repr(n, c, end=False)                          # Long lines
        if i < len(children)-1 else _wrapped_node_repr(n, c, end=True) # Short lines
        for i, (n, c) in enumerate(children.items())
    )

    return "".join([
        "<div style='display: inline-grid; grid-template-columns: 100%'>",
            children_html,
        "</div>"
    ])


children_section = partial(
    _mapping_section,
    name="Groups",
    details_func=summarize_children,
    max_items_collapse=1,
    expand_option_name="display_expand_groups",
)

def node_repr(group_title: str, dt: Any) -> str:
    header_components = [f"<div class='xr-obj-type'>{escape(group_title)}</div>"]

    ds = dt.ds

    sections = [
        children_section(dt.children),
        dim_section(ds),
        coord_section(ds.coords),
        datavar_section(ds.data_vars),
        attr_section(ds.attrs),
    ]

    return _obj_repr(ds, header_components, sections)

def _wrapped_node_repr(*args, end=False, **kwargs):
    # Get node repr
    r = node_repr(*args, **kwargs)

    # height of line
    end = bool(end)
    height = "100%" if end is False else "1.2em";
    return "".join([
        "<div style='display: inline-grid;'>",
            "<div style='",
                "grid-column-start: 1;",
                "border-right: 0.2em solid;",
                "border-color: var(--xr-border-color);",
                f"height: {height};",
                "width: 0px;",
            "'>",
            "</div>",
            "<div style='",
                "grid-column-start: 2;",
                "grid-row-start: 1;",
                "height: 1em;",
                "width: 20px;",
                "border-bottom: 0.2em solid;",
                "border-color: var(--xr-border-color);",
            "'>",
            "</div>",
            "<div style='",
                "grid-column-start: 3;",
            "'>",
                "<ul class='xr-sections'>",
                    r,
                "</ul>"
            "</div>",
        "</div>",
    ])


def datatree_repr(dt: Any) -> str:
    obj_type = f"datatree.{type(dt).__name__}"
    return node_repr(obj_type, dt)
