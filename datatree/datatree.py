from __future__ import annotations

import textwrap
from typing import Any, Callable, Dict, Hashable, Iterable, List, Mapping, Union

import anytree
from xarray.core import dtypes, utils
from xarray.core.arithmetic import DatasetArithmetic
from xarray.core.combine import merge
from xarray.core.common import DataWithCoords
from xarray.core.dataarray import DataArray
from xarray.core.dataset import Dataset
from xarray.core.ops import NAN_CUM_METHODS, NAN_REDUCE_METHODS, REDUCE_METHODS
from xarray.core.variable import Variable

from .mapping import map_over_subtree
from .treenode import PathType, TreeNode, _init_single_treenode

"""
The structure of a populated Datatree looks roughly like this:

DataTree("root name")
|-- DataNode("weather")
|   |   Variable("wind_speed")
|   |   Variable("pressure")
|   |-- DataNode("temperature")
|   |       Variable("sea_surface_temperature")
|   |       Variable("dew_point_temperature")
|-- DataNode("satellite image")
|   |   Variable("true_colour")
|   |-- DataNode("infrared")
|   |       Variable("near_infrared")
|   |       Variable("far_infrared")
|-- DataNode("topography")
|   |-- DataNode("elevation")
|   |       Variable("height_above_sea_level")
|-- DataNode("population")


DEVELOPERS' NOTE
----------------
The idea of this module is to create a `DataTree` class which inherits the tree structure from TreeNode, and also copies
the entire API of `xarray.Dataset`, but with certain methods decorated to instead map the dataset function over every
node in the tree. As this API is copied without directly subclassing `xarray.Dataset` we instead create various Mixin
classes which each define part of `xarray.Dataset`'s extensive API.

Some of these methods must be wrapped to map over all nodes in the subtree. Others are fine to inherit unaltered
(normally because they (a) only call dataset properties and (b) don't return a dataset that should be nested into a new
tree) and some will get overridden by the class definition of DataTree.
"""


class DatasetPropertiesMixin:
    """Expose properties of wrapped Dataset"""

    # TODO a neater way of setting all of these?
    # We wouldn't need this at all if we inherited directly from Dataset...

    @property
    def dims(self):
        if self.has_data:
            return self.ds.dims
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def variables(self):
        if self.has_data:
            return self.ds.variables
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def encoding(self):
        if self.has_data:
            return self.ds.encoding
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def sizes(self):
        if self.has_data:
            return self.ds.sizes
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def attrs(self):
        if self.has_data:
            return self.ds.attrs
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def nbytes(self) -> int:
        return sum(node.ds.nbytes for node in self.subtree)

    @property
    def indexes(self):
        if self.has_data:
            return self.ds.indexes
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def xindexes(self):
        if self.has_data:
            return self.ds.xindexes
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def coords(self):
        if self.has_data:
            return self.ds.coords
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def data_vars(self):
        if self.has_data:
            return self.ds.data_vars
        else:
            raise AttributeError("property is not defined for a node with no data")

    # TODO should this instead somehow give info about the chunking of every node?
    @property
    def chunks(self):
        if self.has_data:
            return self.ds.chunks
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def real(self):
        if self.has_data:
            return self.ds.real
        else:
            raise AttributeError("property is not defined for a node with no data")

    @property
    def imag(self):
        if self.has_data:
            return self.ds.imag
        else:
            raise AttributeError("property is not defined for a node with no data")

    # TODO .loc, __contains__, __iter__, __array__, '__len__',

    dims.__doc__ = Dataset.dims.__doc__
    variables.__doc__ = Dataset.variables.__doc__
    encoding.__doc__ = Dataset.encoding.__doc__
    sizes.__doc__ = Dataset.sizes.__doc__
    attrs.__doc__ = Dataset.attrs.__doc__
    indexes.__doc__ = Dataset.indexes.__doc__
    xindexes.__doc__ = Dataset.xindexes.__doc__
    coords.__doc__ = Dataset.coords.__doc__
    data_vars.__doc__ = Dataset.data_vars.__doc__
    chunks.__doc__ = Dataset.chunks.__doc__


_MAPPED_DOCSTRING_ADDENDUM = textwrap.fill(
    "This method was copied from xarray.Dataset, but has been altered to "
    "call the method on the Datasets stored in every node of the subtree. "
    "See the `map_over_subtree` function for more details.",
    width=117,
)

# TODO equals, broadcast_equals etc.
# TODO do dask-related private methods need to be exposed?
_DATASET_DASK_METHODS_TO_MAP = [
    "load",
    "compute",
    "persist",
    "unify_chunks",
    "chunk",
    "map_blocks",
]
_DATASET_METHODS_TO_MAP = [
    "copy",
    "as_numpy",
    "__copy__",
    "__deepcopy__",
    "set_coords",
    "reset_coords",
    "info",
    "isel",
    "sel",
    "head",
    "tail",
    "thin",
    "broadcast_like",
    "reindex_like",
    "reindex",
    "interp",
    "interp_like",
    "rename",
    "rename_dims",
    "rename_vars",
    "swap_dims",
    "expand_dims",
    "set_index",
    "reset_index",
    "reorder_levels",
    "stack",
    "unstack",
    "update",
    "merge",
    "drop_vars",
    "drop_sel",
    "drop_isel",
    "drop_dims",
    "transpose",
    "dropna",
    "fillna",
    "interpolate_na",
    "ffill",
    "bfill",
    "combine_first",
    "reduce",
    "map",
    "assign",
    "diff",
    "shift",
    "roll",
    "sortby",
    "quantile",
    "rank",
    "differentiate",
    "integrate",
    "cumulative_integrate",
    "filter_by_attrs",
    "polyfit",
    "pad",
    "idxmin",
    "idxmax",
    "argmin",
    "argmax",
    "query",
    "curvefit",
]
# TODO unsure if these are called by external functions or not?
_DATASET_OPS_TO_MAP = ["_unary_op", "_binary_op", "_inplace_binary_op"]
_ALL_DATASET_METHODS_TO_MAP = (
    _DATASET_DASK_METHODS_TO_MAP + _DATASET_METHODS_TO_MAP + _DATASET_OPS_TO_MAP
)

_DATA_WITH_COORDS_METHODS_TO_MAP = [
    "squeeze",
    "clip",
    "assign_coords",
    "where",
    "close",
    "isnull",
    "notnull",
    "isin",
    "astype",
]

# TODO NUM_BINARY_OPS apparently aren't defined on DatasetArithmetic, and don't appear to be injected anywhere...
_ARITHMETIC_METHODS_TO_MAP = (
    REDUCE_METHODS + NAN_REDUCE_METHODS + NAN_CUM_METHODS + ["__array_ufunc__"]
)


def _wrap_then_attach_to_cls(
    target_cls_dict, source_cls, methods_to_set, wrap_func=None
):
    """
    Attach given methods on a class, and optionally wrap each method first. (i.e. with map_over_subtree)

    Result is like having written this in the classes' definition:
    ```
    @wrap_func
    def method_name(self, *args, **kwargs):
        return self.method(*args, **kwargs)
    ```

    Every method attached here needs to have a return value of Dataset or DataArray in order to construct a new tree.

    Parameters
    ----------
    target_cls_dict : MappingProxy
        The __dict__ attribute of the class which we want the methods to be added to. (The __dict__ attribute can also
        be accessed by calling vars() from within that classes' definition.) This will be updated by this function.
    source_cls : class
        Class object from which we want to copy methods (and optionally wrap them). Should be the actual class object
        (or instance), not just the __dict__.
    methods_to_set : Iterable[Tuple[str, callable]]
        The method names and definitions supplied as a list of (method_name_string, method) pairs.
        This format matches the output of inspect.getmembers().
    wrap_func : callable, optional
        Function to decorate each method with. Must have the same return type as the method.
    """
    for method_name in methods_to_set:
        orig_method = getattr(source_cls, method_name)
        wrapped_method = (
            wrap_func(orig_method) if wrap_func is not None else orig_method
        )
        target_cls_dict[method_name] = wrapped_method

        if wrap_func is map_over_subtree:
            # Add a paragraph to the method's docstring explaining how it's been mapped
            orig_method_docstring = orig_method.__doc__
            if orig_method_docstring is not None:
                if "\n" in orig_method_docstring:
                    new_method_docstring = orig_method_docstring.replace(
                        "\n", _MAPPED_DOCSTRING_ADDENDUM, 1
                    )
                else:
                    new_method_docstring = (
                        orig_method_docstring + f"\n\n{_MAPPED_DOCSTRING_ADDENDUM}"
                    )
                setattr(target_cls_dict[method_name], "__doc__", new_method_docstring)


class MappedDatasetMethodsMixin:
    """
    Mixin to add Dataset methods like .mean(), but wrapped to map over all nodes in the subtree.
    """

    __slots__ = ()
    _wrap_then_attach_to_cls(
        vars(), Dataset, _ALL_DATASET_METHODS_TO_MAP, wrap_func=map_over_subtree
    )


class MappedDataWithCoords(DataWithCoords):
    # TODO add mapped versions of groupby, weighted, rolling, rolling_exp, coarsen, resample
    # TODO re-implement AttrsAccessMixin stuff so that it includes access to child nodes
    _wrap_then_attach_to_cls(
        vars(),
        DataWithCoords,
        _DATA_WITH_COORDS_METHODS_TO_MAP,
        wrap_func=map_over_subtree,
    )


class DataTreeArithmetic(DatasetArithmetic):
    """
    Mixin to add Dataset methods like __add__ and .mean().
    """

    _wrap_then_attach_to_cls(
        vars(),
        DatasetArithmetic,
        _ARITHMETIC_METHODS_TO_MAP,
        wrap_func=map_over_subtree,
    )


class DataTree(
    TreeNode,
    DatasetPropertiesMixin,
    MappedDatasetMethodsMixin,
    MappedDataWithCoords,
    DataTreeArithmetic,
):
    """
    A tree-like hierarchical collection of xarray objects.

    Attempts to present the API of xarray.Dataset, but methods are wrapped to also update all the tree's child nodes.

    Parameters
    ----------
    data_objects : dict-like, optional
        A mapping from path names to xarray.Dataset, xarray.DataArray, or xtree.DataTree objects.

        Path names can be given as unix-like paths, or as tuples of strings (where each string
        is known as a single "tag"). If path names containing more than one tag are given, new
        tree nodes will be constructed as necessary.

        To assign data to the root node of the tree {name} as the path.
    name : Hashable, optional
        Name for the root node of the tree. Default is "root"

    See also
    --------
    DataNode : Shortcut to create a DataTree with only a single node.
    """

    # TODO should this instead be a subclass of Dataset?

    # TODO Add attrs dict

    # TODO attribute-like access for both vars and child nodes (by inheriting from xarray.core.common.AttrsAccessMixin?)

    # TODO ipython autocomplete for child nodes

    # TODO Some way of sorting children by depth

    # TODO Consistency in copying vs updating objects

    # TODO do we need a watch out for if methods intended only for root nodes are called on non-root nodes?

    # TODO add any other properties (maybe dask ones?)

    # TODO currently allows self.ds = None, should we instead always store at least an empty Dataset?

    # TODO dataset methods which should not or cannot act over the whole tree, such as .to_array

    # TODO del and delitem methods

    def __init__(
        self,
        data_objects: Dict[PathType, Union[Dataset, DataArray, None]] = None,
        name: Hashable = "root",
    ):
        # First create the root node
        super().__init__(name=name, parent=None, children=None)
        if data_objects:
            root_data = data_objects.pop(name, None)
        else:
            root_data = None
        self.ds = root_data

        if data_objects:
            # Populate tree with children determined from data_objects mapping
            for path, data in data_objects.items():
                # Determine name of new node
                path = self._tuple_or_path_to_path(path)
                if self.separator in path:
                    node_path, node_name = path.rsplit(self.separator, maxsplit=1)
                else:
                    node_path, node_name = "/", path

                # Create and set new node
                new_node = DataNode(name=node_name, data=data)
                self.set_node(
                    node_path,
                    new_node,
                    allow_overwrite=False,
                    new_nodes_along_path=True,
                )

    @property
    def ds(self) -> Dataset:
        return self._ds

    @ds.setter
    def ds(self, data: Union[Dataset, DataArray] = None):
        if not isinstance(data, (Dataset, DataArray)) and data is not None:
            raise TypeError(
                f"{type(data)} object is not an xarray Dataset, DataArray, or None"
            )
        if isinstance(data, DataArray):
            data = data.to_dataset()
        self._ds = data

    @property
    def has_data(self):
        return self.ds is not None

    @classmethod
    def _init_single_datatree_node(
        cls,
        name: Hashable,
        data: Union[Dataset, DataArray] = None,
        parent: TreeNode = None,
        children: List[TreeNode] = None,
    ):
        """
        Create a single node of a DataTree, which optionally contains data in the form of an xarray.Dataset.

        Parameters
        ----------
        name : Hashable
            Name for the root node of the tree. Default is "root"
        data : Dataset, DataArray, Variable or None, optional
            Data to store under the .ds attribute of this node. DataArrays and Variables will be promoted to Datasets.
            Default is None.
        parent : TreeNode, optional
            Parent node to this node. Default is None.
        children : Sequence[TreeNode], optional
            Any child nodes of this node. Default is None.

        Returns
        -------
        node :  DataTree
        """

        # This approach was inspired by xarray.Dataset._construct_direct()
        obj = object.__new__(cls)
        obj = _init_single_treenode(obj, name=name, parent=parent, children=children)
        obj.ds = data
        return obj

    def __str__(self):
        """A printable representation of the structure of this entire subtree."""
        renderer = anytree.RenderTree(self)

        lines = []
        for pre, fill, node in renderer:
            node_repr = node._single_node_repr()

            node_line = f"{pre}{node_repr.splitlines()[0]}"
            lines.append(node_line)

            if node.has_data:
                ds_repr = node_repr.splitlines()[2:]
                for line in ds_repr:
                    if len(node.children) > 0:
                        lines.append(f"{fill}{renderer.style.vertical}{line}")
                    else:
                        lines.append(f"{fill}{line}")

        return "\n".join(lines)

    def _single_node_repr(self):
        """Information about this node, not including its relationships to other nodes."""
        node_info = f"DataNode('{self.name}')"

        if self.has_data:
            ds_info = "\n" + repr(self.ds)
        else:
            ds_info = ""
        return node_info + ds_info

    def __repr__(self):
        """Information about this node, including its relationships to other nodes."""
        # TODO redo this to look like the Dataset repr, but just with child and parent info
        parent = self.parent.name if self.parent is not None else "None"
        node_str = f"DataNode(name='{self.name}', parent='{parent}', children={[c.name for c in self.children]},"

        if self.has_data:
            ds_repr_lines = self.ds.__repr__().splitlines()
            ds_repr = (
                ds_repr_lines[0]
                + "\n"
                + textwrap.indent("\n".join(ds_repr_lines[1:]), "     ")
            )
            data_str = f"\ndata={ds_repr}\n)"
        else:
            data_str = "data=None)"

        return node_str + data_str

    def __getitem__(
        self, key: Union[PathType, Hashable, Mapping, Any]
    ) -> Union[TreeNode, Dataset, DataArray]:
        """
        Access either child nodes, variables, or coordinates stored in this tree.

        Variables or coordinates of the contained dataset will be returned as a :py:class:`~xarray.DataArray`.
        Indexing with a list of names will return a new ``Dataset`` object.

        Like Dataset.__getitem__ this method also accepts dict-like indexing, and selection of multiple data variables
        (from the same Dataset node) via list.

        Parameters
        ----------
        key :
            Paths to nodes or to data variables in nodes can be given as unix-like paths, or as tuples of strings
            (where each string is known as a single "tag").
        """
        # Either:
        if utils.is_dict_like(key):
            # dict-like selection on dataset variables
            return self.ds[key]
        elif utils.hashable(key):
            # path-like: a path to a node possibly with a variable name at the end
            return self._get_item_from_path(key)
        elif utils.is_list_like(key) and all(k in self.ds for k in key):
            # iterable of variable names
            return self.ds[key]
        elif utils.is_list_like(key) and all("/" not in tag for tag in key):
            # iterable of child tags
            return self._get_item_from_path(key)
        else:
            raise ValueError("Invalid format for key")

    def _get_item_from_path(
        self, path: PathType
    ) -> Union[TreeNode, Dataset, DataArray]:
        """Get item given a path. Two valid cases: either all parts of path are nodes or last part is a variable."""

        # TODO this currently raises a ChildResolverError if it can't find a data variable in the ds - that's inconsistent with xarray.Dataset.__getitem__

        path = self._tuple_or_path_to_path(path)
        tags = [
            tag for tag in path.split(self.separator) if tag not in [self.separator, ""]
        ]
        *leading_tags, last_tag = tags

        if leading_tags is not None:
            penultimate = self.get_node(tuple(leading_tags))
        else:
            penultimate = self

        if penultimate.has_data and last_tag in penultimate.ds:
            return penultimate.ds[last_tag]
        else:
            return penultimate.get_node(last_tag)

    def __setitem__(
        self,
        key: Union[Hashable, List[Hashable], Mapping, PathType],
        value: Union[TreeNode, Dataset, DataArray, Variable, None],
    ) -> None:
        """
        Add either a child node or an array to the tree, at any position.

        Data can be added anywhere, and new nodes will be created to cross the path to the new location if necessary.

        If there is already a node at the given location, then if value is a Node class or Dataset it will overwrite the
        data already present at that node, and if value is a single array, it will be merged with it.

        If value is None a new node will be created but containing no data. If a node already exists at that path it
        will have its .ds attribute set to None. (To remove node from the tree completely instead use `del tree[path]`.)

        Parameters
        ----------
        key
            A path-like address for either a new node, or the address and name of a new variable, or the name of a new
            variable.
        value
            Can be a node class or a data object (i.e. Dataset, DataArray, Variable).
        """

        # TODO xarray.Dataset accepts other possibilities, how do we exactly replicate all the behaviour?
        if utils.is_dict_like(key):
            raise NotImplementedError

        path = self._tuple_or_path_to_path(key)
        tags = [
            tag for tag in path.split(self.separator) if tag not in [self.separator, ""]
        ]

        # TODO a .path_as_tags method?
        if not tags:
            # only dealing with this node, no need for paths
            if isinstance(value, (Dataset, DataArray, Variable)):
                # single arrays will replace whole Datasets, as no name for new variable was supplied
                self.ds = value
            elif isinstance(value, TreeNode):
                self.add_child(value)
            elif value is None:
                self.ds = None
            else:
                raise TypeError(
                    "Can only assign values of type TreeNode, Dataset, DataArray, or Variable, "
                    f"not {type(value)}"
                )
        else:
            *path_tags, last_tag = tags
            if not path_tags:
                path_tags = "/"

            # get anything that already exists at that location
            try:
                existing_node = self.get_node(path)
            except anytree.resolver.ResolverError:
                existing_node = None

            if existing_node is not None:
                if isinstance(value, Dataset):
                    # replace whole dataset
                    existing_node.ds = Dataset
                elif isinstance(value, (DataArray, Variable)):
                    if not existing_node.has_data:
                        # promotes da to ds
                        existing_node.ds = value
                    else:
                        # update with new da
                        existing_node.ds[last_tag] = value
                elif isinstance(value, TreeNode):
                    # overwrite with new node at same path
                    self.set_node(path=path, node=value)
                elif value is None:
                    existing_node.ds = None
                else:
                    raise TypeError(
                        "Can only assign values of type TreeNode, Dataset, DataArray, or Variable, "
                        f"not {type(value)}"
                    )
            else:
                # if nothing there then make new node based on type of object
                if isinstance(value, (Dataset, DataArray, Variable)) or value is None:
                    new_node = DataNode(name=last_tag, data=value)
                    self.set_node(path=path_tags, node=new_node)
                elif isinstance(value, TreeNode):
                    self.set_node(path=path, node=value)
                else:
                    raise TypeError(
                        "Can only assign values of type TreeNode, Dataset, DataArray, or Variable, "
                        f"not {type(value)}"
                    )

    def map_over_subtree(
        self,
        func: Callable,
        *args: Iterable[Any],
        **kwargs: Any,
    ) -> DataTree:
        """
        Apply a function to every dataset in this subtree, returning a new tree which stores the results.

        The function will be applied to any dataset stored in this node, as well as any dataset stored in any of the
        descendant nodes. The returned tree will have the same structure as the original subtree.

        func needs to return a Dataset in order to rebuild the subtree.

        Parameters
        ----------
        func : callable
            Function to apply to datasets with signature:
            `func(node.ds, *args, **kwargs) -> Dataset`.

            Function will not be applied to any nodes without datasets.
        *args : tuple, optional
            Positional arguments passed on to `func`.
        **kwargs : Any
            Keyword arguments passed on to `func`.

        Returns
        -------
        subtree : DataTree
            Subtree containing results from applying ``func`` to the dataset at each node.
        """
        # TODO this signature means that func has no way to know which node it is being called upon - change?

        return map_over_subtree(func)(self, *args, **kwargs)

    def map_over_subtree_inplace(
        self,
        func: Callable,
        *args: Iterable[Any],
        **kwargs: Any,
    ) -> None:
        """
        Apply a function to every dataset in this subtree, updating data in place.

        Parameters
        ----------
        func : callable
            Function to apply to datasets with signature:
            `func(node.ds, *args, **kwargs) -> Dataset`.

            Function will not be applied to any nodes without datasets,
        *args : tuple, optional
            Positional arguments passed on to `func`.
        **kwargs : Any
            Keyword arguments passed on to `func`.
        """

        # TODO if func fails on some node then the previous nodes will still have been updated...

        for node in self.subtree:
            if node.has_data:
                node.ds = func(node.ds, *args, **kwargs)

    def render(self):
        """Print tree structure, including any data stored at each node."""
        for pre, fill, node in anytree.RenderTree(self):
            print(f"{pre}DataNode('{self.name}')")
            for ds_line in repr(node.ds)[1:]:
                print(f"{fill}{ds_line}")

    # TODO re-implement using anytree findall function?
    def get_all(self, *tags: Hashable) -> DataTree:
        """
        Return a DataTree containing the stored objects whose path contains all of the given tags,
        where the tags can be present in any order.
        """
        matching_children = {
            c.tags: c.get_node(tags)
            for c in self.descendants
            if all(tag in c.tags for tag in tags)
        }
        return DataTree(data_objects=matching_children)

    # TODO re-implement using anytree find function?
    def get_any(self, *tags: Hashable) -> DataTree:
        """
        Return a DataTree containing the stored objects whose path contains any of the given tags.
        """
        matching_children = {
            c.tags: c.get_node(tags)
            for c in self.descendants
            if any(tag in c.tags for tag in tags)
        }
        return DataTree(data_objects=matching_children)

    def merge(self, datatree: DataTree) -> DataTree:
        """Merge all the leaves of a second DataTree into this one."""
        raise NotImplementedError

    def merge_child_nodes(self, *paths, new_path: PathType) -> DataTree:
        """Merge a set of child nodes into a single new node."""
        raise NotImplementedError

    def merge_child_datasets(
        self,
        *paths: PathType,
        compat: str = "no_conflicts",
        join: str = "outer",
        fill_value: Any = dtypes.NA,
        combine_attrs: str = "override",
    ) -> Dataset:
        """Merge the datasets at a set of child nodes and return as a single Dataset."""
        datasets = [self.get(path).ds for path in paths]
        return merge(
            datasets,
            compat=compat,
            join=join,
            fill_value=fill_value,
            combine_attrs=combine_attrs,
        )

    def as_array(self) -> DataArray:
        return self.ds.as_dataarray()

    @property
    def groups(self):
        """Return all netCDF4 groups in the tree, given as a tuple of path-like strings."""
        return tuple(node.pathstr for node in self.subtree)

    def to_netcdf(
        self, filepath, mode: str = "w", encoding=None, unlimited_dims=None, **kwargs
    ):
        """
        Write datatree contents to a netCDF file.

        Paramters
        ---------
        filepath : str or Path
            Path to which to save this datatree.
        mode : {"w", "a"}, default: "w"
            Write ('w') or append ('a') mode. If mode='w', any existing file at
            this location will be overwritten. If mode='a', existing variables
            will be overwritten. Only appies to the root group.
        encoding : dict, optional
            Nested dictionary with variable names as keys and dictionaries of
            variable specific encodings as values, e.g.,
            ``{"root/set1": {"my_variable": {"dtype": "int16", "scale_factor": 0.1,
            "zlib": True}, ...}, ...}``. See ``xarray.Dataset.to_netcdf`` for available
            options.
        unlimited_dims : dict, optional
            Mapping of unlimited dimensions per group that that should be serialized as unlimited dimensions.
            By default, no dimensions are treated as unlimited dimensions.
            Note that unlimited_dims may also be set via
            ``dataset.encoding["unlimited_dims"]``.
        kwargs :
            Addional keyword arguments to be passed to ``xarray.Dataset.to_netcdf``
        """
        from .io import _datatree_to_netcdf

        _datatree_to_netcdf(
            self,
            filepath,
            mode=mode,
            encoding=encoding,
            unlimited_dims=unlimited_dims,
            **kwargs,
        )

    def to_zarr(self, store, mode: str = "w", encoding=None, **kwargs):
        """
        Write datatree contents to a netCDF file.

        Parameters
        ---------
        store : MutableMapping, str or Path, optional
            Store or path to directory in file system
        mode : {{"w", "w-", "a", "r+", None}, default: "w"
            Persistence mode: “w” means create (overwrite if exists); “w-” means create (fail if exists);
            “a” means override existing variables (create if does not exist); “r+” means modify existing
            array values only (raise an error if any metadata or shapes would change). The default mode
            is “a” if append_dim is set. Otherwise, it is “r+” if region is set and w- otherwise.
        encoding : dict, optional
            Nested dictionary with variable names as keys and dictionaries of
            variable specific encodings as values, e.g.,
            ``{"root/set1": {"my_variable": {"dtype": "int16", "scale_factor": 0.1}, ...}, ...}``.
            See ``xarray.Dataset.to_zarr`` for available options.
        kwargs :
            Addional keyword arguments to be passed to ``xarray.Dataset.to_zarr``
        """
        from .io import _datatree_to_zarr

        _datatree_to_zarr(
            self,
            store,
            mode=mode,
            encoding=encoding,
            **kwargs,
        )

    def plot(self):
        raise NotImplementedError


DataNode = DataTree._init_single_datatree_node
