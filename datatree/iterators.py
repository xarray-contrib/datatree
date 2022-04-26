from collections import abc
from abc import abstractmethod

"""These iterators are copied from anytree.iterators with minor modifications."""


class AbstractIter(abc.Iterator):
    def __init__(self, node, filter_=None, stop=None, maxlevel=None):
        """
        Iterate over tree starting at `node`.
        Base class for all iterators.
        Keyword Args:
            filter_: function called with every `node` as argument, `node` is returned if `True`.
            stop: stop iteration at `node` if `stop` function returns `True` for `node`.
            maxlevel (int): maximum descending in the node hierarchy.
        """
        self.node = node
        self.filter_ = filter_
        self.stop = stop
        self.maxlevel = maxlevel
        self.__iter = None

    def __init(self):
        node = self.node
        maxlevel = self.maxlevel
        filter_ = self.filter_ or AbstractIter.__default_filter
        stop = self.stop or AbstractIter.__default_stop
        children = [] if AbstractIter._abort_at_level(1, maxlevel) else AbstractIter._get_children(node.children, stop)
        return self._iter(children, filter_, stop, maxlevel)

    @staticmethod
    def __default_filter(node):
        return True

    @staticmethod
    def __default_stop(node):
        return False

    def __iter__(self):
        return self

    def __next__(self):
        if self.__iter is None:
            self.__iter = self.__init()
        return next(self.__iter)

    @staticmethod
    @abstractmethod
    def _iter(children, filter_, stop, maxlevel):
        ...

    @staticmethod
    def _abort_at_level(level, maxlevel):
        return maxlevel is not None and level > maxlevel

    @staticmethod
    def _get_children(children, stop):
        return [child for child in children if not stop(child)]


class PreOrderIter(AbstractIter):
    """
    Iterate over tree applying pre-order strategy starting at `node`.
    Start at root and go-down until reaching a leaf node.
    Step upwards then, and search for the next leafs.
    >>> from anytree import Node, RenderTree, AsciiStyle, PreOrderIter
    >>> f = Node("f")
    >>> b = Node("b", parent=f)
    >>> a = Node("a", parent=b)
    >>> d = Node("d", parent=b)
    >>> c = Node("c", parent=d)
    >>> e = Node("e", parent=d)
    >>> g = Node("g", parent=f)
    >>> i = Node("i", parent=g)
    >>> h = Node("h", parent=i)
    >>> print(RenderTree(f, style=AsciiStyle()).by_attr())
    f
    |-- b
    |   |-- a
    |   +-- d
    |       |-- c
    |       +-- e
    +-- g
        +-- i
            +-- h
    >>> [node.name for node in PreOrderIter(f)]
    ['f', 'b', 'a', 'd', 'c', 'e', 'g', 'i', 'h']
    >>> [node.name for node in PreOrderIter(f, maxlevel=3)]
    ['f', 'b', 'a', 'd', 'g', 'i']
    >>> [node.name for node in PreOrderIter(f, filter_=lambda n: n.name not in ('e', 'g'))]
    ['f', 'b', 'a', 'd', 'c', 'i', 'h']
    >>> [node.name for node in PreOrderIter(f, stop=lambda n: n.name == 'd')]
    ['f', 'b', 'a', 'g', 'i', 'h']
    """

    @staticmethod
    def _iter(children, filter_, stop, maxlevel):
        for child_ in children:
            if stop(child_):
                continue
            if filter_(child_):
                yield child_
            if not AbstractIter._abort_at_level(2, maxlevel):
                descendantmaxlevel = maxlevel - 1 if maxlevel else None
                for descendant_ in PreOrderIter._iter(child_.children, filter_, stop, descendantmaxlevel):
                    yield descendant_


class LevelOrderIter(AbstractIter):
    """
    Iterate over tree applying level-order strategy starting at `node`.
    >>> from anytree import Node, RenderTree, AsciiStyle, LevelOrderIter
    >>> f = Node("f")
    >>> b = Node("b", parent=f)
    >>> a = Node("a", parent=b)
    >>> d = Node("d", parent=b)
    >>> c = Node("c", parent=d)
    >>> e = Node("e", parent=d)
    >>> g = Node("g", parent=f)
    >>> i = Node("i", parent=g)
    >>> h = Node("h", parent=i)
    >>> print(RenderTree(f, style=AsciiStyle()).by_attr())
    f
    |-- b
    |   |-- a
    |   +-- d
    |       |-- c
    |       +-- e
    +-- g
        +-- i
            +-- h
    >>> [node.name for node in LevelOrderIter(f)]
    ['f', 'b', 'g', 'a', 'd', 'i', 'c', 'e', 'h']
    >>> [node.name for node in LevelOrderIter(f, maxlevel=3)]
    ['f', 'b', 'g', 'a', 'd', 'i']
    >>> [node.name for node in LevelOrderIter(f, filter_=lambda n: n.name not in ('e', 'g'))]
    ['f', 'b', 'a', 'd', 'i', 'c', 'h']
    >>> [node.name for node in LevelOrderIter(f, stop=lambda n: n.name == 'd')]
    ['f', 'b', 'g', 'a', 'i', 'h']
    """

    @staticmethod
    def _iter(children, filter_, stop, maxlevel):
        level = 1
        while children:
            next_children = []
            for child in children:
                if filter_(child):
                    yield child
                next_children += AbstractIter._get_children(child.children, stop)
            children = next_children
            level += 1
            if AbstractIter._abort_at_level(level, maxlevel):
                break
