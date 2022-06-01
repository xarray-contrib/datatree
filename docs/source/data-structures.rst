.. _data structures:

Data Structures
===============

.. ipython:: python
    :suppress:

    import numpy as np
    import pandas as pd
    import xarray as xr
    import datatree

    np.random.seed(123456)
    np.set_printoptions(threshold=10)

.. note::

    This page builds on the information given in xarray's main page on
    `data structures <https://docs.xarray.dev/en/stable/user-guide/data-structures.html>`_, so it is suggested that you
    are familiar with those first.

DataTree
--------

:py:class:``DataTree`` is xarray's highest-level data structure, able to organise heterogeneous data which
could not be stored inside a single ``Dataset`` object. This includes representing the recursive structure of multiple
`groups`_ within a netCDF file or `Zarr Store`_.

.. _groups: https://www.unidata.ucar.edu/software/netcdf/workshops/2011/groups-types/GroupsIntro.html
.. _Zarr Store: https://zarr.readthedocs.io/en/stable/tutorial.html#groups

Each ``DataTree`` object (or "node") contains the same data that a single ``xarray.Dataset`` would (i.e. ``DataArray`` objects
stored under hashable keys), and so has the same key properties:

- ``dims``: a dictionary mapping of dimension names to lengths, for the variables in this node,
- ``data_vars``: a dict-like container of DataArrays corresponding to variables in this node,
- ``coords``: another dict-like container of DataArrays, corresponding to coordinate variables in this node,
- ``attrs``: dict to hold arbitary metadata relevant to data in this node.

A single ``DataTree`` object acts much like a single ``Dataset`` object, and has a similar set of dict-like methods
defined upon it. However, ``DataTree``'s can also contain other ``DataTree`` objects, so they can be thought of as nested dict-like
containers of both ``xarray.DataArray``'s and ``DataTree``'s.

A single datatree object is known as a "node", and its position relative to other nodes is defined by two more key
properties:

- ``children``: An ordered dictionary mapping from names to other ``DataTree`` objects, known as its' "child nodes".
- ``parent``: The single ``DataTree`` object whose children this datatree is a member of, known as its' "parent node".

Each child automatically knows about its parent node, and a node without a parent is known as a "root" node
(represented by the ``parent`` attribute pointing to ``None``).
Nodes can have multiple children, but as each child node has at most one parent, there can only ever be one root node in a given tree.

The overall structure is technically a `connected acyclic undirected rooted graph`, otherwise known as a
`"Tree" <https://en.wikipedia.org/wiki/Tree_(graph_theory)>`_.

.. note::

    Technically a ``DataTree`` with more than one child node forms an `"Ordered Tree" <https://en.wikipedia.org/wiki/Tree_(graph_theory)#Ordered_tree>`_,
    because the children are stored in an Ordered Dictionary. However, this distinction only really matters for a few
    edge cases involving operations on multiple trees simultaneously, and can safely be ignored by most users.


``DataTree`` objects can also optionally have a ``name`` as well as ``attrs``, just like a ``DataArray``.
Again these are not normally used unless explicitly accessed by the user.


Creating a DataTree
~~~~~~~~~~~~~~~~~~~

There are two ways to create a ``DataTree`` from scratch. The first is to create each node individually,
specifying the nodes' relationship to one another as you create each one.

The ``DataTree`` constructor takes:

- ``data``: The data that will be stored in this node, represented by a single ``xarray.Dataset``, or a named ``xarray.DataArray``.
- ``parent``: The parent node (if there is one), given as a ``DataTree`` object.
- ``children``: The various child nodes (if there are any), given as a mapping from string keys to ``DataTree`` objects.
- ``name``: A string to use as the name of this node.

Let's make a datatree node without anything in it:

.. ipython:: python

    from datatree import DataTree

    # create root node
    node1 = DataTree(name="Oak")

    node1

At this point our node is also the root node, as every tree has a root node.

We can add a second node to this tree either by referring to the first node in the constructor of the second:

.. ipython:: python

    # add a child by referring to the parent node
    node2 = DataTree(name="Little Bonsai", parent=node1)

or by dynamically updating the attributes of one node to refer to another:

.. ipython:: python

    # add a grandparent by updating the .parent property of an existing node
    node0 = DataTree(name="General Sherman")
    node1.parent = node0

Our tree now has a new root:

.. ipython:: python

    node2.root

Is is at tree construction time that consistency checks are enforced. For instance, if we try to create a `cycle` the constructor will raise an error:

.. ipython:: python
    :okexcept:

    node0.parent = node2

The second way is to build the tree from a dictionary of filesystem-like paths and corresponding ``xarray.Dataset` objects.
This relies on




If you have a file containing data on disk (such as a netCDF file or a Zarr Store), you can also create a datatree by opening the
file using ``:py:func::~datatree.open_datatree``.


DataTree Contents
~~~~~~~~~~~~~~~~~

Now let's add some data to our tree.

.. ipython:: python

    # create some data
    ds1 = xr.Dataset({"a": ("x", [1, 2, 3])})

    ds1


You can see that the data in the node is displayed in the same way that the contents of the xarray Dataset we added would have been.



Navigating the Tree
~~~~~~~~~~~~~~~~~~~

Root, ancestors, parent, children, leaves, file-like access

Mapping Operations Over the Tree
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
