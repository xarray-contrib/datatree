from xarray.testing import ensure_warnings

from .datatree import DataTree
from .formatting import diff_tree_repr


@ensure_warnings
def assert_isomorphic(a: DataTree, b: DataTree):
    """
    Two DataTrees are isomorphic if every node has the same number of children.

    Parameters
    ----------
    a : xarray.DataTree
        The first object to compare.
    b : xarray.DataTree
        The second object to compare.

    See Also
    --------
    DataTree.equals
    DataTree.identical
    """
    __tracebackhide__ = True
    assert type(a) == type(b)
    if isinstance(a, DataTree):
        assert a.isomorphic(b), diff_tree_repr(a, b, "isomorphic")
    else:
        raise TypeError(f"{type(a)} not of type DataTree")


@ensure_warnings
def assert_equal(a: DataTree, b: DataTree):
    """
    Two DataTrees are equal if they have isomorphic node structures, and
    all stored Datasets are equal.

    Parameters
    ----------
    a : xarray.DataTree
        The first object to compare.
    b : xarray.DataTree
        The second object to compare.

    See Also
    --------
    Dataset.equals
    DataTree.identical
    """
    __tracebackhide__ = True
    assert type(a) == type(b)
    if isinstance(a, DataTree):
        assert a.equals(b), diff_tree_repr(a, b, "equals")
    else:
        raise TypeError(f"{type(a)} not of type DataTree")


@ensure_warnings
def assert_identical(a: DataTree, b: DataTree):
    """
    Like equals, but also checks all corresponding nodes have the same names, as well as
    all dataset attributes and the attributes on all variables and coordinates.

    Parameters
    ----------
    a : xarray.DataTree
        The first object to compare.
    b : xarray.DataTree
        The second object to compare.

    See Also
    --------
    Dataset.identical
    DataTree.equals
    """

    __tracebackhide__ = True
    assert type(a) == type(b)
    if isinstance(a, DataTree):
        assert a.equals(b), diff_tree_repr(a, b, "identical")
    else:
        raise TypeError(f"{type(a)} not of type DataTree")
