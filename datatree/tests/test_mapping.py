import pytest
import xarray as xr
from xarray.testing import assert_equal

from datatree.datatree import DataNode, DataTree
from datatree.mapping import _check_isomorphic, TreeIsomorphismError, map_over_subtree

from test_datatree import assert_tree_equal, create_test_datatree


empty = xr.Dataset()


class TestCheckTreesIsomorphic:
    def test_not_a_tree(self):
        with pytest.raises(TypeError, match="not a tree"):
            _check_isomorphic('s', 1)

    def test_different_widths(self):
        dt1 = DataTree(data_objects={'a': empty})
        dt2 = DataTree(data_objects={'a': empty, 'b': empty})
        expected_err_str = "'root' in the first tree has 1 children, whereas its counterpart node 'root' in the " \
                           "second tree has 2 children"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2)

    def test_different_heights(self):
        dt1 = DataTree(data_objects={'a': empty})
        print(dt1)
        dt2 = DataTree(data_objects={'a': empty, 'a/b': empty})
        print(dt2)
        expected_err_str = "'root/a' in the first tree has 0 children, whereas its counterpart node 'root/a' in the " \
                           "second tree has 1 children"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2)

    def test_only_one_has_data(self):
        dt1 = DataTree(data_objects={'/': None})
        dt2 = DataTree(data_objects={'a': empty})
        expected_err_str = "'root/a' in the first tree has data, whereas its counterpart node 'root/a' in the " \
                           "second tree has no data"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2)

    def test_names_different(self):
        dt1 = DataTree(data_objects={'a': xr.Dataset()})
        dt2 = DataTree(data_objects={'b': empty})
        expected_err_str = "'root/a' in the first tree has name a, whereas its counterpart node 'root/b' in the " \
                           "second tree has name b"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2, require_names_equal=True)

    def test_isomorphic_names_equal(self):
        dt1 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        dt2 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        expected_err_str = "'root/a' in the first tree has name a, whereas its counterpart node 'root/b' in the " \
                           "second tree has name b"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2, require_names_equal=True)

    def test_isomorphic_names_not_equal(self):
        dt1 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        dt2 = DataTree(data_objects={'A': empty, 'B': empty, 'B/C': empty, 'B/D': empty})
        expected_err_str = "'root/a' in the first tree has name a, whereas its counterpart node 'root/b' in the " \
                           "second tree has name b"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2, require_names_equal=True)


class TestMapOverSubTree:
    def test_no_trees_passed(self):
        ...

    def test_not_isomorphic(self):
        ...

    def test_no_trees_returned(self):
        ...

    def test_single_dt_arg(self):
        dt = create_test_datatree()

        @map_over_subtree
        def times_ten(ds):
            return 10.0 * ds

        result_tree = times_ten(dt)

        # TODO write an assert_tree_equal function
        for (
            result_node,
            original_node,
        ) in zip(result_tree.subtree, dt.subtree):
            assert isinstance(result_node, DataTree)

            if original_node.has_data:
                assert_equal(result_node.ds, original_node.ds * 10.0)
            else:
                assert not result_node.has_data

    def test_single_dt_arg_plus_args_and_kwargs(self):
        dt = create_test_datatree()

        @map_over_subtree
        def multiply_then_add(ds, times, add=0.0):
            return times * ds + add

        result_tree = multiply_then_add(dt, 10.0, add=2.0)

        for (
            result_node,
            original_node,
        ) in zip(result_tree.subtree, dt.subtree):
            assert isinstance(result_node, DataTree)

            if original_node.has_data:
                assert_equal(result_node.ds, (original_node.ds * 10.0) + 2.0)
            else:
                assert not result_node.has_data

    def test_multiple_dt_args(self):
        ds = xr.Dataset({"a": ("x", [1, 2, 3])})
        dt = DataNode("root", data=ds)
        DataNode("results", data=ds + 0.2, parent=dt)

        @map_over_subtree
        def add(ds1, ds2):
            return ds1 + ds2

        expected = DataNode("root", data=ds * 2)
        DataNode("results", data=(ds + 0.2) * 2, parent=expected)

        result = add(dt, dt)

        # dt1 = create_test_datatree()
        # dt2 = create_test_datatree()
        # expected = create_test_datatree(modify=lambda ds: 2 * ds)

        assert_tree_equal(result, expected)

    def test_dt_as_kwarg(self):
        ...

    @pytest.mark.xfail
    def test_return_multiple_dts(self):
        raise NotImplementedError

    def test_return_no_dts(self):
        ...

    def test_dt_method(self):
        dt = create_test_datatree()

        def multiply_then_add(ds, times, add=0.0):
            return times * ds + add

        result_tree = dt.map_over_subtree(multiply_then_add, 10.0, add=2.0)

        for (
            result_node,
            original_node,
        ) in zip(result_tree.subtree, dt.subtree):
            assert isinstance(result_node, DataTree)

            if original_node.has_data:
                assert_equal(result_node.ds, (original_node.ds * 10.0) + 2.0)
            else:
                assert not result_node.has_data


@pytest.mark.xfail
class TestMapOverSubTreeInplace:
    def test_map_over_subtree_inplace(self):
        raise NotImplementedError
