.. _hierarchical-data:

Working With Hierarchical Data
==============================

.. ipython:: python
    :suppress:

    import numpy as np
    import pandas as pd
    import xarray as xr
    from datatree import DataTree

    np.random.seed(123456)
    np.set_printoptions(threshold=10)

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
Here we go into more detail about how to create a tree node-by-node, using a famous family tree from the Simpsons cartoon as an example.

Let's start by defining nodes representing the two siblings, Bart and Lisa Simpson:

.. ipython:: python

    bart = DataTree(name="Bart")
    lisa = DataTree(name="Lisa")

Each of these node objects knows their own ``.name``, but they currently have no relationship to one another.
We can connect them by creating another node representing a common parent, Homer Simpson:

.. ipython:: python

    homer = DataTree(name="Homer", children={"Bart": bart, "Lisa": lisa})

Here we set the children of Homer in the node's constructor.
We now have a small family tree

.. ipython:: python

    homer

where we can see how these individual Simpson family members are related to one another.
The nodes representing Bart and Lisa are now connected - we can confirm their sibling rivalry by examining the ``.siblings`` property:

.. ipython:: python

    list(bart.siblings)

But oops, we forgot Homer's third daughter, Maggie! Let's add her by updating Homer's ``.children`` property to include her:

.. ipython:: python

    maggie = DataTree(name="Maggie")
    homer.children = {"Bart": bart, "Lisa": lisa, "Maggie": maggie}
    homer

Let's check that Maggie knows who her Dad is:

.. ipython:: python

    maggie.parent.name

That's good - updating the properties of our nodes does not break the internal consistency of our tree, as changes of parentage are automatically reflected on both nodes.

    These children obviously have another parent, Marge Simpson, but ``DataTree`` nodes can only have a maximum of one parent.
    Genealogical `family trees are not even technically trees <https://en.wikipedia.org/wiki/Family_tree#Graph_theory>`_ in the mathematical sense -
    the fact that distant relatives can mate makes it a directed acyclic graph.
    Trees of ``DataTree`` objects cannot represent this.

Homer is currently listed as having no parent (the so-called "root node" of this tree), but we can update his ``.parent`` property:

.. ipython:: python

    abe = DataTree(name="Abe")
    homer.parent = abe

Abe is now the "root" of this tree, which we can see by examining the ``.root`` property of any node in the tree

.. ipython:: python

    maggie.root.name

We can see the whole tree by printing Abe's node or just part of the tree by printing Homer's node:

.. ipython:: python

    abe
    homer

We can see that Homer is aware of his parentage, and we say that Homer and his children form a "subtree" of the larger Simpson family tree.

In episode 28, Abe Simpson reveals that he had another son, Herbert "Herb" Simpson.
We can add Herbert to the family tree without displacing Homer by ``.assign``-ing another child to Abe:

# TODO write the ``assign`` or ``assign_nodes`` method on ``DataTree`` so that this example works

.. ipython:: python
    :okexcept:

    herb = DataTree(name="Herb")
    abe.assign({"Herbert": herb})

# TODO Name permanence of herb versus herbert (or abe versus abraham)

Certain manipulations of our tree are forbidden, if they would create an inconsistent result.
In episode 51 of the show Futurama, Philip J. Fry travels back in time and accidentally becomes his own Grandfather.
If we try similar time-travelling hijinks with Homer, we get a ``InvalidTreeError`` raised:

.. ipython:: python
    :okexcept:

    abe.parent = homer


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

see relative to of bart to herbert


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

Need to first recreate tree with age data in it

Subset only the living leaves of the evolutionary tree?


.. _tree computation:

Computation
-----------

Operations on Trees
~~~~~~~~~~~~~~~~~~~

Mapping of methods

Arithmetic

cause all Simpsons to age simultaneously


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
