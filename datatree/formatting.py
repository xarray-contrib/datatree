from xarray.core.formatting import diff_dataset_repr

from .mapping import _check_isomorphic


def diff_node_repr(a, b, compat, path):
    dataset_diff_repr = diff_dataset_repr(a, b, compat)
    return f"Nodes at position {path} do not match:\n".join(dataset_diff_repr)


def diff_tree_repr(a, b, compat):

    # TODO get the string error message somehow
    _check_isomorphic(a, b, require_names_equal=True if compat is "identical" else False)
