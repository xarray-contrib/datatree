import pytest
import xarray as xr
from xarray.testing import assert_equal

from datatree.treenode import TreeNode
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
        dt2 = DataTree(data_objects={'a': empty, 'a/b': empty})
        expected_err_str = "'root/a' in the first tree has 0 children, whereas its counterpart node 'root/a' in the " \
                           "second tree has 1 children"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2)

    def test_only_one_has_data(self):
        dt1 = DataTree(data_objects={'a': xr.Dataset({'a': 0})})
        dt2 = DataTree(data_objects={'a': None})
        expected_err_str = "'root/a' in the first tree has data, whereas its counterpart node 'root/a' in the " \
                           "second tree has no data"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2)

    def test_names_different(self):
        dt1 = DataTree(data_objects={'a': xr.Dataset()})
        dt2 = DataTree(data_objects={'b': empty})
        expected_err_str = "'root/a' in the first tree has name 'a', whereas its counterpart node 'root/b' in the " \
                           "second tree has name 'b'"
        with pytest.raises(TreeIsomorphismError, match=expected_err_str):
            _check_isomorphic(dt1, dt2, require_names_equal=True)

    def test_isomorphic_names_equal(self):
        dt1 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        dt2 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        _check_isomorphic(dt1, dt2, require_names_equal=True)

    def test_isomorphic_ordering(self):
        dt1 = DataTree(data_objects={'a': empty, 'b': empty, 'b/d': empty, 'b/c': empty})
        dt2 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        _check_isomorphic(dt1, dt2, require_names_equal=False)

    def test_isomorphic_names_not_equal(self):
        dt1 = DataTree(data_objects={'a': empty, 'b': empty, 'b/c': empty, 'b/d': empty})
        dt2 = DataTree(data_objects={'A': empty, 'B': empty, 'B/C': empty, 'B/D': empty})
        _check_isomorphic(dt1, dt2)

    def test_not_isomorphic_complex_tree(self):
        dt1 = create_test_datatree()
        dt2 = create_test_datatree()
        dt2.set_node('set1/set2', TreeNode('set3'))
        with pytest.raises(TreeIsomorphismError, match="root/set1/set2"):
            _check_isomorphic(dt1, dt2)


class TestMapOverSubTree:
    def test_no_trees_passed(self):
        @map_over_subtree
        def times_ten(ds):
            return 10.0 * ds

        with pytest.raises(TypeError, match="Must pass at least one tree"):
            times_ten("dt")

    def test_not_isomorphic(self):
        dt1 = create_test_datatree()
        dt2 = create_test_datatree()
        dt2['set4'] = None

        @map_over_subtree
        def times_ten(ds1, ds2):
            return ds1 * ds2

        with pytest.raises(TreeIsomorphismError):
            times_ten(dt1, dt2)

    def test_no_trees_returned(self):
        dt1 = create_test_datatree()
        dt2 = create_test_datatree()

        @map_over_subtree
        def bad_func(ds1, ds2):
            return None

        with pytest.raises(TypeError, match="return value of None"):
            bad_func(dt1, dt2)

    def test_single_dt_arg(self):
        dt = create_test_datatree()

        @map_over_subtree
        def times_ten(ds):
            return 10.0 * ds

        expected = create_test_datatree(modify=lambda ds: 10.0 * ds)
        print(expected)
        result_tree = times_ten(dt)
        assert_tree_equal(result_tree, expected)

    def test_single_dt_arg_plus_args_and_kwargs(self):
        dt = create_test_datatree(modify=lambda ds: (10.0 * ds) + 2.0)

        @map_over_subtree
        def multiply_then_add(ds, times, add=0.0):
            return times * ds + add

        result_tree = multiply_then_add(dt, 10.0, add=2.0)
        assert_tree_equal(result_tree, dt)

    def test_multiple_dt_args(self):
        dt1 = create_test_datatree()
        dt2 = create_test_datatree()

        @map_over_subtree
        def add(ds1, ds2):
            return ds1 + ds2

        expected = create_test_datatree(modify=lambda ds: 2.0 * ds)
        result = add(dt1, dt2)
        assert_tree_equal(result, expected)

    def test_dt_as_kwarg(self):
        dt1 = create_test_datatree()
        dt2 = create_test_datatree()

        @map_over_subtree
        def add(ds1, value=0.0):
            return ds1 + value

        expected = create_test_datatree(modify=lambda ds: 2.0 * ds)
        result = add(dt1, value=dt2)
        assert_tree_equal(result, expected)

    def test_return_multiple_dts(self):
        dt1 = create_test_datatree()
        dt2 = create_test_datatree()

        @map_over_subtree
        def minmax(ds):
            return ds.min(), ds.max()

        dt_min, dt_max = minmax(dt1, dt2)
        expected_min = create_test_datatree(modify=lambda ds: ds.min())
        assert_tree_equal(dt_min, expected_min)
        expected_max = create_test_datatree(modify=lambda ds: ds.max())
        assert_tree_equal(dt_max, expected_max)

    def test_return_wrong_type(self):
        dt1 = create_test_datatree()

        @map_over_subtree
        def bad_func(ds1):
            return "string"

        with pytest.raises(TypeError, match="not Dataset or DataArray"):
            bad_func(dt1)

    def test_return_tuple_of_wrong_types(self):
        dt1 = create_test_datatree()

        @map_over_subtree
        def bad_func(ds1):
            return xr.Dataset(), "string"

        with pytest.raises(TypeError, match="not Dataset or DataArray"):
            bad_func(dt1)

    @pytest.mark.xfail
    def test_return_inconsistent_number_of_results(self):
        dt1 = create_test_datatree()
        counter = 0

        @map_over_subtree
        def bad_func(ds1):
            if (counter % 2) == 0:
                counter += 1
                return xr.Dataset()
            else:
                counter += 1
                return xr.Dataset(), xr.Dataset()

        with pytest.raises(TypeError, match="not Dataset or DataArray"):
            bad_func(dt1)

    @pytest.mark.xfail
    def test_trees_with_different_node_names(self):
        raise NotImplementedError

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
