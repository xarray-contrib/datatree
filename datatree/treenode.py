from __future__ import annotations

from collections import OrderedDict
from pathlib import PurePosixPath
from typing import Iterator, Mapping, Tuple

from xarray.core.utils import Frozen, is_dict_like


class TreeError(Exception):
    """Exception type raised when user attempts to create an invalid tree in some way."""

    ...


class NodePath(PurePosixPath):
    """Represents a path from one node to another within a tree."""

    def __new__(cls, *args: str | "NodePath") -> "NodePath":
        obj = super().__new__(cls, *args)

        if obj.drive:
            raise ValueError("NodePaths cannot have drives")

        if obj.root not in ["/", ""]:
            raise ValueError('Root of NodePath can only be either "/" or ""')

        return obj


class TreeNode:
    """
    Base class representing a node of a tree, with methods for traversing and altering the tree.

    This class stores no data, it has only parents and children attributes, and various methods.

    Stores child nodes in an Ordered Dictionary, which is necessary to ensure that equality checks between two trees
    also check that the order of child nodes is the same. Nodes themselves are unnamed.

    The parent attribute is read-only: to replace the parent you must set this node as the child of a new parent using
    `new_parent.children[name] = child_node`, or to instead detach from the current parent use `child_node.orphan()`.
    This is because the TreeNode does not have a name attribute.

    Also allows access to any other node in the tree via unix-like paths, including upwards referencing via '../'.

    (This class is heavily inspired by the anytree library's NodeMixin class.)
    """

    # TODO replace all type annotations that use "TreeNode" with "Self", so it's still correct when subclassed (requires python 3.11)
    _parent: TreeNode | None
    _children: OrderedDict[str, TreeNode]

    def __init__(self, children: Mapping[str, TreeNode] = None):
        """Create a parentless node."""
        self._parent = None
        self._children = OrderedDict()
        if children is not None:
            self.children = children

    @property
    def parent(self) -> TreeNode | None:
        """Parent of this node."""
        return self._parent

    def _set_parent(self, new_parent: TreeNode | None, child_name: str = None):
        # TODO is it possible to refactor in a way that removes this private method?

        if new_parent is not None and not isinstance(new_parent, TreeNode):
            raise TypeError(
                "Parent nodes must be of type DataTree or None, "
                f"not type {type(new_parent)}"
            )

        old_parent = self._parent
        if new_parent is not old_parent:
            self._check_loop(new_parent)
            self._detach(old_parent)
            self._attach(new_parent, child_name)

    def _check_loop(self, new_parent: TreeNode | None):
        """Checks that assignment of this new parent will not create a cycle."""
        if new_parent is not None:
            if new_parent is self:
                raise TreeError(
                    f"Cannot set parent, as node {self} cannot be a parent of itself."
                )

            _self, *lineage = list(self.lineage)
            if any(child is self for child in lineage):
                raise TreeError(
                    f"Cannot set parent, as node {self} is already a descendant of node {new_parent}."
                )

    def _detach(self, parent: TreeNode | None):
        if parent is not None:
            self._pre_detach(parent)
            parents_children = parent.children
            parent._children = OrderedDict(
                {
                    name: child
                    for name, child in parents_children.items()
                    if child is not self
                }
            )
            self._parent = None
            self._post_detach(parent)

    def _attach(self, parent: TreeNode | None, child_name: str = None):
        if parent is not None:
            self._pre_attach(parent)
            parentchildren = parent._children
            assert not any(
                child is self for child in parentchildren
            ), "Tree is corrupt."
            parentchildren[child_name] = self
            self._parent = parent
            self._post_attach(parent)
        else:
            self._parent = None

    def orphan(self):
        """Detach this node from its parent."""
        self._set_parent(new_parent=None)

    @property
    def children(self) -> Mapping[str, TreeNode]:
        """Child nodes of this node, stored under a mapping via their names."""
        return Frozen(self._children)

    @children.setter
    def children(self, children: Mapping[str, TreeNode]):
        self._check_children(children)
        children = OrderedDict(children)

        old_children = self.children
        del self.children
        try:
            self._pre_attach_children(children)
            for name, child in children.items():
                child._set_parent(new_parent=self, child_name=name)
            self._post_attach_children(children)
            assert len(self.children) == len(children)
        except Exception:
            # if something goes wrong then revert to previous children
            self.children = old_children
            raise

    @children.deleter
    def children(self):
        # TODO this just detaches all the children, it doesn't actually delete them...
        children = self.children
        self._pre_detach_children(children)
        for child in self.children.values():
            child.orphan()
        assert len(self.children) == 0
        self._post_detach_children(children)

    @staticmethod
    def _check_children(children: Mapping[str, TreeNode]):
        """Check children for correct types and for any duplicates."""
        if not is_dict_like(children):
            raise TypeError(
                "children must be a dict-like mapping from names to node objects"
            )

        seen = set()
        for name, child in children.items():
            if not isinstance(child, TreeNode):
                raise TypeError(
                    f"Cannot add object {name}. It is of type {type(child)}, "
                    "but can only add children of type DataTree"
                )

            childid = id(child)
            if childid not in seen:
                seen.add(childid)
            else:
                raise TreeError(
                    f"Cannot add same node {name} multiple times as different children."
                )

    def _pre_detach_children(self, children: Mapping[str, TreeNode]):
        """Method call before detaching `children`."""
        pass

    def _post_detach_children(self, children: Mapping[str, TreeNode]):
        """Method call after detaching `children`."""
        pass

    def _pre_attach_children(self, children: Mapping[str, TreeNode]):
        """Method call before attaching `children`."""
        pass

    def _post_attach_children(self, children: Mapping[str, TreeNode]):
        """Method call after attaching `children`."""
        pass

    def iter_lineage(self) -> Iterator[TreeNode]:
        """Iterate up the tree, starting from the current node."""
        # TODO should this instead return an OrderedDict, so as to include node names?
        node: TreeNode | None = self
        while node is not None:
            yield node
            node = node.parent

    @property
    def lineage(self) -> Tuple[TreeNode]:
        """All parent nodes and their parent nodes, starting with the closest."""
        return tuple(self.iter_lineage())

    @property
    def ancestors(self) -> Tuple[TreeNode, ...]:
        """All parent nodes and their parent nodes, starting with the most distant."""
        if self.parent is None:
            return tuple()
        else:
            ancestors = tuple(reversed(list(self.lineage)))
            return ancestors

    @property
    def root(self) -> TreeNode:
        """Root node of the tree"""
        node = self
        while node.parent is not None:
            node = node.parent
        return node

    @property
    def is_root(self) -> bool:
        """Whether or not this node is the tree root."""
        return self.parent is None

    @property
    def siblings(self) -> OrderedDict[str, TreeNode]:
        """
        Nodes with the same parent as this node.
        """
        return OrderedDict(
            {
                name: child
                for name, child in self.parent.children.items()
                if child is not self
            }
        )

    @property
    def subtree(self) -> Iterator[TreeNode]:
        """An iterator over all nodes in this tree, including both self and all descendants."""
        # return anytree.iterators.PreOrderIter(self)
        raise NotImplementedError

    def _pre_detach(self, parent: TreeNode):
        """Method call before detaching from `parent`."""
        pass

    def _post_detach(self, parent: TreeNode):
        """Method call after detaching from `parent`."""
        pass

    def _pre_attach(self, parent: TreeNode):
        """Method call before attaching to `parent`."""
        pass

    def _post_attach(self, parent: TreeNode):
        """Method call after attaching to `parent`."""
        pass

    def _get_node(self, path: str | NodePath) -> TreeNode:
        """
        Returns the node lying at the given path.

        Raises a KeyError if there is no node at the given path.
        """
        if isinstance(path, str):
            path = NodePath(path)

        if path.root:
            current_node = self.root
            root, *parts = path.parts
        else:
            current_node = self
            parts = path.parts

        for part in parts:
            if part == "..":
                parent = current_node.parent
                if parent is None:
                    raise KeyError(f"Could not find node at {path}")
                current_node = parent
            elif part in ("", "."):
                pass
            else:
                current_node = current_node.children[part]
        return current_node

    def set_node(self, path: str, node: TreeNode):
        raise NotImplementedError

    def del_node(self, path: str):
        raise NotImplementedError
