.. currentmodule:: datatree
.. _terminology:

Terminology
===========

.. glossary::

    DataTree
        A tree-like collection of ``Dataset`` objects. A *tree* is made up of one or more *nodes*,
        each of which can store the same information as a single ``Dataset`` (accessed via `.ds`).
        This data is stored in the same way as in a ``Dataset``, i.e. in the form of data variables (see **Variable** below),
        dimensions, coordinates, and attributes.

        The nodes in a tree are linked to one another, and each node is it's own instance of ``DataTree`` object.
        Each node can have zero or more *children* (stored in a dictionary-like manner under their corresponding *names*),
        and those child nodes can themselves have children.
        If a node is a child of another node that other node is said to be its *parent*. Nodes can only have one parent,
        and if a node has no parent it is said to be the *root* node of that *tree*.

    Subtree
        A section of a *tree*, consisting of a *node* along with all the child nodes below it
        (and the child nodes below them, i.e. all so-called *descendant* nodes).
        Excludes the parent node and all nodes above.

    Group
        Another word for a subtree - analogous to a single `netCDF group <https://www.unidata.ucar.edu/software/netcdf/workshops/2011/groups-types/GroupsIntro.html>`_.
