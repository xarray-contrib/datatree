import functools

from anytree.iterators import LevelOrderIter
from xarray import Dataset, DataArray

from .treenode import TreeNode
from .datatree import DataNode, DataTree


class TreeIsomorphismError(ValueError):
    """Error raised if two tree objects are not isomorphic to one another when they need to be."""

    pass


def _check_isomorphic(subtree_a, subtree_b, require_names_equal=False):
    """
    Check that two trees have the same structure, raising an error if not.

    Does not check the actual data in the nodes, but it does check that if one node does/doesn't have data then its
    counterpart in the other tree also does/doesn't have data.

    Also does not check that the root nodes of each tree have the same parent - so this function checks that subtrees
    are isomorphic, not the entire tree above (if it exists).

    Can optionally check if respective nodes should have the same name.

    Parameters
    ----------
    subtree_a : DataTree
    subtree_b : DataTree
    require_names_equal : Bool, optional
        Whether or not to also check that each node has the same name as its counterpart. Default is False.

    Raises
    ------
    TypeError
        If either subtree_a or subtree_b are not tree objects.
    TreeIsomorphismError
        If subtree_a and subtree_b are tree objects, but are not isomorphic to one another, or one contains data at a
        location the other does not. Also optionally raised if their structure is isomorphic, but the names of any two
        respective nodes are not equal.
    """
    # TODO turn this into a public function called assert_isomorphic

    for i, dt in enumerate(subtree_a, subtree_b):
        if not isinstance(dt, TreeNode):
            raise TypeError(f"Argument number {i+1} is not a tree, it is of type {type(dt)}")

    # Walking nodes in "level-order" fashion means walking down from the root breadth-first.
    # Checking by walking in this way implicitly assumes that the tree is an ordered tree (which it is so long as
    # children are stored in a tuple or list rather than in a set).
    for node_a, node_b in zip(LevelOrderIter(subtree_a), LevelOrderIter(subtree_b)):
        path_a, path_b = node_a.pathstr, node_b.pathstr

        if require_names_equal:
            if node_a.name != node_b.name:
                raise TreeIsomorphismError(f"Trees are not isomorphic because node {path_a} in the first tree has name"
                                           f"{node_a.name}, whereas its counterpart node {path_b} in the second tree "
                                           f"has name {node_b.name}.")

        if node_a.has_data != node_b.has_data:
            dat_a = 'no ' if not node_a.has_data else ''
            dat_b = 'no ' if not node_b.has_data else ''
            raise TreeIsomorphismError(f"Trees are not isomorphic because node {path_a} in the first tree has "
                                       f"{dat_a}data, whereas its counterpart node {path_b} in the second tree "
                                       f"has {dat_b}data.")

        if len(node_a.children) != len(node_b.children):
            raise TreeIsomorphismError(f"Trees are not isomorphic because node {path_a} in the first tree has "
                                       f"{len(node_a.children)} children, whereas its counterpart node {path_b} in the "
                                       f"second tree has {len(node_b.children)} children.")


def map_over_subtree(func):
    """
    Decorator which turns a function which acts on (and returns) Datasets into one which acts on and returns DataTrees.

    Applies a function to every dataset in this subtree, returning one or more new trees which store the results.

    The function will be applied to any dataset stored in any of the nodes in the trees. The returned trees will have
    the same structure as the supplied trees.

    `func` needs to return one Datasets, DataArrays, or None in order to be able to rebuild the subtrees after
    mapping, as each result will be assigned to its respective node of a new tree via `DataTree.__setitem__`. Any
    returned value that is one of these types will be stacked into a separate tree before returning all of them.

    Parameters
    ----------
    func : callable
        Function to apply to datasets with signature:
        `func(*args, **kwargs) -> Union[Dataset, Iterable[Dataset]]`.

        (i.e. func must accept at least one Dataset and return at least one Dataset.)
        Function will not be applied to any nodes without datasets.
    *args : tuple, optional
        Positional arguments passed on to `func`. Will be converted to Datasets via .ds if DataTrees.
    **kwargs : Any
        Keyword arguments passed on to `func`. Will be converted to Datasets via .ds if DataTrees.

    Returns
    -------
    mapped : callable
        Wrapped function which returns one or more tree(s) created from results of applying ``func`` to the dataset at
        each node.

    See also
    --------
    DataTree.map_over_subtree
    DataTree.map_over_subtree_inplace
    """

    # TODO inspect function to work out immediately if the wrong number of arguments were passed for it?

    @functools.wraps(func)
    def _map_over_subtree(*args, **kwargs):
        """Internal function which maps func over every node in tree, returning a tree of the results."""

        all_tree_inputs = [a for a in args if isinstance(a, DataTree)] + [
            a for a in kwargs.values() if isinstance(a, DataTree)
        ]

        if len(all_tree_inputs) > 0:
            first_tree, *other_trees = all_tree_inputs
        else:
            raise TypeError("Must pass at least one tree object")

        for other_tree in other_trees:
            # isomorphism is transitive
            _check_isomorphic(first_tree, other_tree, require_names_equal=False)

        # Walk all trees simultaneously, applying func to all nodes that lie in same position in different trees
        out_data_objects = {}
        for nodes in zip(dt.subtree for dt in all_tree_inputs):

            node_first_tree, *_ = nodes

            # TODO make a proper relative_path method
            relative_path = node_first_tree.pathstr.replace(first_tree.pathstr, "")

            node_args_as_datasets = [a.ds if isinstance(a, DataTree) else a for a in args]
            node_kwargs_as_datasets = {
                k: v.ds if isinstance(v, DataTree) else v for k, v in kwargs
            }

            # TODO should we allow mapping functions that return zero datasets?
            # TODO generalise to functions that return multiple values
            result = func(*node_args_as_datasets, **node_kwargs_as_datasets) if node_first_tree.has_data else None
            out_data_objects[relative_path] = result

        # TODO: Possible bug - what happens if another tree argument does not have root named the same way?
        return DataTree(name=first_tree.name, data_objects=out_data_objects)

    return _map_over_subtree
