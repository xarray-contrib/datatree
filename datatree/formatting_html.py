from functools import partial
from html import escape
from typing import Any, Mapping

from xarray.core.formatting_html import (
    _load_static_files,
    _mapping_section,
    attr_section,
    collapsible_section,
    coord_section,
    datavar_section,
    dim_section,
)
from xarray.core.options import OPTIONS, _get_boolean_with_default

OPTIONS["display_expand_groups"] = "default"
OPTIONS["display_expand_group_data"] = "default"

additional_css_style = """
.xr-tree {
  display: inline-grid;
  grid-template-columns: 100%;
}

.xr-tree-item {
  display: inline-grid;
}
.xr-tree-item-mid {
  height: 100%;
}
.xr-tree-item-end {
  height: 1.2em;
}

.xr-tree-item-connection-vertical {
  grid-column-start: 1;
  border-right: 0.2em solid;
  border-color: var(--xr-border-color);
  width: 0px;
}
.xr-tree-item-connection-horizontal {
  grid-column-start: 2;
  grid-row-start: 1;
  height: 1em;
  width: 20px;
  border-bottom: 0.2em solid;
  border-color: var(--xr-border-color);
}

.xr-tree-item-data {
  grid-column-start: 3;
}
.xr-tree-item-data-sections {
  margin-left: 0.6em;
}
"""


def summarize_children(children: Mapping[str, Any]) -> str:
    def is_last_item(index, n_total):
        return index >= n_total - 1

    def format_child(name, child, end):
        """format node and wrap it into a tree"""
        formatted = node_repr(name, child)
        return _wrap_repr(formatted, end=end)

    n_children = len(children)

    children_html = "".join(
        format_child(name, child, end=is_last_item(index, n_children))
        for index, (name, child) in enumerate(children.items())
    )

    return f"<div class='xr-tree'>{children_html}</div>"


children_section = partial(
    _mapping_section,
    name="Groups",
    details_func=summarize_children,
    max_items_collapse=1,
    expand_option_name="display_expand_groups",
)


def summarize_data(node):
    ds = node.ds
    sections = [
        dim_section(ds),
        coord_section(ds.coords),
        datavar_section(ds.data_vars),
        attr_section(ds.attrs),
    ]
    return f"<div class='xr-tree-item-data-sections'>{''.join(sections)}</div>"


def data_section(node):
    name = "Data"

    details = summarize_data(node)

    n_items = 5
    expanded = _get_boolean_with_default(
        "display_expand_group_data",
        True,
    )
    collapsed = not expanded

    return collapsible_section(
        name=name,
        details=details,
        n_items=n_items,
        enabled=True,
        collapsed=collapsed,
    )


def join_sections(sections, header_components):
    combined_sections = "".join(
        f"<li class='xr-section-item'>{s}</li>" for s in sections
    )
    header = "".join(header_components)
    return (
        "<div class='xr-wrap' style='display:none'>"
        f"<div class='xr-header'>{header}</div>"
        f"<ul class='xr-sections'>{combined_sections}</ul>"
        "</div>"
    )


def node_repr(group_title: str, dt: Any) -> str:
    header_components = [f"<div class='xr-obj-type'>{escape(group_title)}</div>"]

    sections = [children_section(dt.children), data_section(dt)]

    return join_sections(sections, header_components)


def _wrap_repr(r: str, end: bool = False) -> str:
    """
    Wrap HTML representation with a tee to the left of it.

    Enclosing HTML tag is a <div> with :code:`display: inline-grid` style.

    Turns:
    [    title    ]
    |   details   |
    |_____________|

    into (A):
    |─ [    title    ]
    |  |   details   |
    |  |_____________|

    or (B):
    └─ [    title    ]
       |   details   |
       |_____________|

    Parameters
    ----------
    r: str
        HTML representation to wrap.
    end: bool
        Specify if the line on the left should continue or end.

        Default is True.

    Returns
    -------
    str
        Wrapped HTML representation.

        Tee color is set to the variable :code:`--xr-border-color`.
    """
    item_class = "xr-tree-item-mid" if not end else "xr-tree-item-end"
    return (
        "<div class='xr-tree-item'>"
        f"<div class='xr-tree-item-connection-vertical {item_class}'></div>"
        "<div class='xr-tree-item-connection-horizontal'></div>"
        f"<div class='xr-tree-item-data'><ul class='xr-sections'>{r}</ul></div>"
        "</div>"
    )


def datatree_repr(dt: Any) -> str:
    obj_type = f"datatree.{type(dt).__name__}"

    icons_svg, css_style = _load_static_files()

    return (
        "<div>"
        f"{icons_svg}"
        f"<style>{css_style}</style>"
        f"<style>{additional_css_style}</style>"
        f"<pre class='xr-text-repr-fallback'>{escape(repr(dt))}</pre>"
        f"{node_repr(obj_type, dt)}"
        "</div>"
    )
