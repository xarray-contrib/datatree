import functools
import itertools
from collections import OrderedDict

from anytree.iterators import LevelOrderIter
from xarray import Dataset, DataArray

from .treenode import TreeNode


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

    if not isinstance(subtree_a, TreeNode):
        raise TypeError(f"Argument `subtree_a` is not a tree, it is of type {type(subtree_a)}")
    if not isinstance(subtree_b, TreeNode):
        raise TypeError(f"Argument `subtree_b` is not a tree, it is of type {type(subtree_b)}")

    # Walking nodes in "level-order" fashion means walking down from the root breadth-first.
    # Checking by walking in this way implicitly assumes that the tree is an ordered tree (which it is so long as
    # children are stored in a tuple or list rather than in a set).
    for node_a, node_b in zip(LevelOrderIter(subtree_a), LevelOrderIter(subtree_b)):
        path_a, path_b = node_a.pathstr, node_b.pathstr

        if require_names_equal:
            if node_a.name != node_b.name:
                raise TreeIsomorphismError(f"Trees are not isomorphic because node '{path_a}' in the first tree has "
                                           f"name '{node_a.name}', whereas its counterpart node '{path_b}' in the "
                                           f"second tree has name '{node_b.name}'.")

        if node_a.has_data != node_b.has_data:
            dat_a = 'no ' if not node_a.has_data else ''
            dat_b = 'no ' if not node_b.has_data else ''
            raise TreeIsomorphismError(f"Trees are not isomorphic because node '{path_a}' in the first tree has "
                                       f"{dat_a}data, whereas its counterpart node '{path_b}' in the second tree "
                                       f"has {dat_b}data.")

        if len(node_a.children) != len(node_b.children):
            raise TreeIsomorphismError(f"Trees are not isomorphic because node '{path_a}' in the first tree has "
                                       f"{len(node_a.children)} children, whereas its counterpart node '{path_b}' in "
                                       f"the second tree has {len(node_b.children)} children.")


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
        from .datatree import DataTree

        all_tree_inputs = [a for a in args if isinstance(a, DataTree)] + [
            a for a in kwargs.values() if isinstance(a, DataTree)
        ]
        which_args_are_trees = [isinstance(a, DataTree) for a in args]
        which_kwargs_are_trees = {k: isinstance(v, DataTree) for k, v in kwargs.items()}

        if len(all_tree_inputs) > 0:
            first_tree, *other_trees = all_tree_inputs
        else:
            raise TypeError("Must pass at least one tree object")

        for other_tree in other_trees:
            # isomorphism is transitive
            _check_isomorphic(first_tree, other_tree, require_names_equal=False)

        # Walk all trees simultaneously, applying func to all nodes that lie in same position in different trees
        # Store tuples of results in a dict because we don't yet know how many trees we need to rebuild to return
        out_data_objects = {}
        subtrees = [dt.subtree for dt in all_tree_inputs]
        for nodes in zip(*subtrees):
            node_first_tree, *_ = nodes

            # TODO make a proper relative_path method
            path = node_first_tree.pathstr#.replace(first_tree.pathstr, "")
            relative_path = node_first_tree.pathstr.replace(first_tree.pathstr, "")
            print(relative_path)

            # Extract all node datasets from trees
            node_args_as_datasets = []
            for position, (node, is_tree) in enumerate(itertools.zip_longest(nodes, which_args_are_trees)):
                if is_tree:
                    node_args_as_datasets.append(node.ds)
                else:
                    node_args_as_datasets.append(args[position])
            node_kwargs_as_datasets = {}
            for node, (k, is_tree) in itertools.zip_longest(nodes, which_kwargs_are_trees):
                if is_tree:
                    node_kwargs_as_datasets[k] = node
                else:
                    node_kwargs_as_datasets[k] = kwargs[k]

            results = func(*node_args_as_datasets, **node_kwargs_as_datasets) if node_first_tree.has_data else None

            # TODO implement mapping over multiple trees inplace using if conditions from here on?
            out_data_objects[relative_path] = results

        # Find out how many return values we had
        num_return_values = _check_return_values(out_data_objects)

        print(out_data_objects)

        # Reconstruct potentially multiple subtrees from the dict of results
        # Fill in all nodes of all result trees
        result_trees = []
        for _ in range(num_return_values):
            out_tree_contents = {}
            for n in first_tree.subtree:
                p = n.pathstr
                out_tree_contents[p] = out_data_objects[p] if p in out_data_objects.keys() else None

            # TODO: document how names are just taken from first dt passed
            # TODO: Possible bug - what happens if another tree argument does not have root named the same way?
            new_tree = DataTree(name=first_tree.name, data_objects=out_tree_contents)
            print(new_tree)
            result_trees.append(new_tree)

        # If only one result then don't wrap it in a tuple
        if len(result_trees) == 1:
            return result_trees[0]
        else:
            return tuple(result_trees)

    return _map_over_subtree


def _check_return_values(returned_objects):
    """Walk through all values returned by mapping func over subtrees, raising on any invalid or inconsistent types."""
    #print(returned_objects)

    if all(r is None for r in returned_objects.values()):
        raise TypeError("Called supplied function on all nodes but found a return value of None for"
                        "all of them.")

    result_data_objects = [(p, r) for p, r in returned_objects.items() if r is not None]

    prev_path, prev_obj = result_data_objects[0]
    prev_num_return_values, num_return_values = None, None
    for p, obj in result_data_objects[1:]:
        if isinstance(obj, (Dataset, DataArray)):
            num_return_values = 1
        elif isinstance(obj, tuple):
            for r in enumerate(obj):
                if not isinstance(r, (Dataset, DataArray)):
                    raise TypeError(f"One of the results of calling func on datasets on the nodes at position {p} is "
                                    f"of type {type(r)}, not Dataset or DataArray.")

            num_return_values = len(tuple)
        else:
            raise TypeError(f"The result of calling func on the node at position {p} is of type {type(obj)}, not "
                            f"Dataset or DataArray, nor a tuple of such types.")

        if num_return_values != prev_num_return_values and prev_num_return_values is not None:
            raise TypeError(f"Calling func on the nodes at position {p} returns {num_return_values} separate return "
                            f"values, whereas calling func on the nodes at position {prev_path} instead returns "
                            f"{prev_num_return_values} separate return values.")

        prev_path, prev_obj, prev_num_return_values = p, obj, num_return_values

    return num_return_values
