from xarray.core.formatting_html import dataset_repr


def datatree_repr(dt: "DataTree") -> str:
    return dataset_repr(dt.ds)
