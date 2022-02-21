from __future__ import annotations

from abc import ABC
from typing import Hashable, Iterable, Sequence, Tuple, Union, Mapping, Iterator,
from collections import OrderedDict

import anytree

PathType = Union[Hashable, Sequence[Hashable]]


class TreeError(Exception):
    """Exception type raised when user attempts to create an invalid tree in some way."""
    ...


class FamilyTreeNode:
    """
    Base class representing a node of a tree, with methods for traversing and altering the tree.

    This class stores no data, it has only parents and children attributes, and various methods.

    Stores child nodes in an Ordered Dictionary, which is necessary to ensure that equality checks between two trees
    also check that the order of child nodes is the same. Nodes themselves are unnamed.
    """

    # TODO replace all type annotations that use "TreeNode" with "Self", so it's still correct when subclassed (requires python 3.11)
    _parent: TreeNode | None
    _children: OrderedDict[str, TreeNode]

    @property
    def parent(self) -> TreeNode | None:
        return self._parent

    @parent.setter
    def parent(self, new_parent: TreeNode | None):
        if new_parent is not None and not isinstance(new_parent, TreeNode):
            raise TypeError("Parent nodes must be of type DataTree or None, "
                            f"not type {type(new_parent)}")

        old_parent = self._parent
        if new_parent is not old_parent:
            self._check_loop(new_parent)
            self._detach(old_parent)
            self._attach(new_parent)

    def _check_loop(self, new_parent: TreeNode | None):
        if new_parent is not None:
            if new_parent is self:
                raise TreeError(f"Cannot set parent, as node {self} cannot be a parent of itself.")

            if any(child is self for child in self.iter_lineage_reverse()):
                raise TreeError(f"Cannot set parent, as node {self} is already a descendant of node {new_parent}.")

    def _detach(self, parent: TreeNode | None):
        if parent is not None:
            self._pre_detach(parent)
            parents_children = parent.children
            parent._children = [child for child in parents_children.values() if child is not self]
            self._parent = None
            self._post_detach(parent)

    def _attach(self, parent: TreeNode):
        raise NotImplementedError

    @property
    def children(self) -> OrderedDict[str, TreeNode]:
        return self._children

    @staticmethod
    def _check_children(children: Mapping[str, TreeNode]):
        """Check children for correct types and for any duplicates."""
        seen = set()
        for name, child in children.items():
            if not isinstance(child, TreeNode):
                raise TypeError(f"Cannot add object {name}. It is of type {type(child)}, "
                                "but can only add children of type DataTree")
            childid = id(child)
            if childid not in seen:
                seen.add(childid)
            else:
                raise TreeError(f"Cannot add node {name} multiple times as child.")

    @children.setter
    def children(self, children: Mapping[str, TreeNode]):
        children = OrderedDict(**children)
        self._check_children(children)
        old_children = self.children
        del self.children
        try:
            self._pre_attach_children(children)
            for child in children:
                child.parent = self
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
        for child in self.children:
            child.parent = None
        assert len(self.children) == 0
        self._post_detach_children(children)

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

    def iter_lineage_reverse(self) -> Iterator[TreeNode]:
        # TODO should this instead return an OrderedDict, so as to include node names?
        """Iterate up the tree from the current node."""
        node = self
        while node is not None:
            yield node
            node = node.parent

    @property
    def ancestors(self) -> Tuple[TreeNode, ...]:
        """All parent nodes and their parent nodes, starting with the most distant."""
        if self.parent is None:
            return tuple()
        else:
            ancestors = tuple(reversed(list(self.iter_lineage_reverse())))
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
        Dict of nodes with the same parent.
        """
        parent = self.parent
        if parent is None:
            return OrderedDict()
        else:
            return OrderedDict(**{name: child for name, child in parent.children.items() if child is not self})

    @property
    def subtree(self) -> Iterator[TreeNode]:
        """An iterator over all nodes in this tree, including both self and all descendants."""
        return anytree.iterators.PreOrderIter(self)

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


class PathLikeAccessMixin:
    """
    Allows access to any other node in the tree via unix-like paths, including upwards referencing via '../'.
    """

    def get_node(self, path: str) -> TreeNode:
        """
        Returns the node lying at the given path.

        Raises a KeyError if there is no node at the given path.
        """
        path = NodePath(path)
        self._get_node(path)

    def _get_node(self, path: NodePath):
        ...

    def set_node(self, path: str, node: TreeNode):
        ...

    def del_node(self, path: str):
        ...


class TreeNode(FamilyTreeNode, PathLikeAccessMixin):
    ...
