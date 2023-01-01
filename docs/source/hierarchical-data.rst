.. _hierarchical data:

Working With Hierarchical Data
==============================

Why Hierarchical Data?
----------------------

Many real-world datasets are composed of multiple differing components,
and it can often be be useful to think of these in terms of a hierarchy of related groups of data.
Examples of data which one might want organise in a grouped or hierarchical manner include:

- Simulation data at multiple resolutions,
- Observational data about the same system but from multiple different types of sensors,
- Mixed experimental and theoretical data,
- A systematic study recording the same experiment but with different parameters,
- Heterogenous data, such as demographic and metereological data,

or even any combination of the above.

Often datasets like this cannot easily fit into a single ``xarray.Dataset`` object,
or are more usefully thought of as groups of related ``xarray.Dataset`` objects.
For this purpose we provide the ``DataTree`` class.

This page explains in detail how to understand and use the different features of the ``DataTree`` class for your own heirarchical data needs.

.. _creating a family tree:

Creating a Family Tree
----------------------

The three main ways of creating a ``DataTree`` object are described briefly in :ref:`creating a datatree`.
Here we go into more detail about how to create a tree node-by-node, using a family tree as an example.

This could perhaps go in a tutorial?

(i.e. how to create and manipulate a tree structure from scratch node-by-node, with no data in it).

Create Simpson's family tree

Start with Homer, Bart and Lisa

Add Maggie by setting children on homer

check that this also set's Maggie's parent

Add long-lost relations

add Abe by setting

(Abe's father, Homer's cousin?)

add Herbert by setting

.. _navigating trees:

Navigating Trees
----------------

Node Relationships
~~~~~~~~~~~~~~~~~~

Root, ancestors, parent, children, leaves

Tree of life?

leaves are either currently living or died out with no descendants
Root is beginning of life
ancestors are evolutionary history

find common ancestor

Alien life not in same tree?

Filesystem-like Paths
~~~~~~~~~~~~~~~~~~~~~

file-like access via paths


.. _manipulating trees:

Manipulating Trees
------------------

Altering Tree Branches
~~~~~~~~~~~~~~~~~~~~~~

pruning, grafting

Tree of life?

Graft new discoveries onto the tree?

Prune when we realise something is in the wrong place?

Save our updated tree out with ``to_dict``

Subsetting Tree Nodes
~~~~~~~~~~~~~~~~~~~~~

subset, filter

Filter the Simpsons by age?

Subset only the living leaves of the evolutionary tree?


.. _tree computation:

Computation
-----------

Operations on Trees
~~~~~~~~~~~~~~~~~~~

Mapping of methods


Mapping Custom Functions Over Trees
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.subtree, map_over_subtree


.. _multiple trees:

Operating on Multiple Trees
---------------------------

Comparing trees
~~~~~~~~~~~~~~~

isomorphism

Mapping over Multiple Trees
~~~~~~~~~~~~~~~~~~~~~~~~~~~

map_over_subtree with binary function
