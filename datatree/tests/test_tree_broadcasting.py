import numpy as np
import pytest
import xarray as xr

import datatree.testing as dtt
from datatree.datatree import DataTree

empty = xr.Dataset()

def int_ds(value):
    return xr.Dataset({'data':xr.DataArray(value)})

class TestTreeBroadcasting:

    def test_single_root(self):
        dt1 = DataTree.from_dict(d={'root': int_ds(3)})
        dt2 = DataTree.from_dict(d={"root/a": int_ds(2) , "root/b": int_ds(5)})
        expected = DataTree.from_dict(d={'root/a': int_ds(3*2), 'root/b': int_ds(3*5)})
        dtt.assert_equal(dt1*dt2, expected)

    def test_hollow_level_2(self):
        dt1 = DataTree.from_dict(d={'root/a': int_ds(5), 'root/b': int_ds(4)})
        dt2 = DataTree.from_dict(d={'root/a': int_ds(3), 'root/b/c': int_ds(2), 'root/b/d': int_ds(7)})
        expected = DataTree.from_dict(d={'root/a': int_ds(3*5), 'root/b/c':int_ds(2*4), 'root/b/d': int_ds(7*4)})
        dtt.assert_equal(dt1*dt2, expected)

    def test_dense_level_2(self):
        dt1 = DataTree.from_dict(d={'root/a': int_ds(5), 'root/b': int_ds(4)})
        dt2 = DataTree.from_dict(d={'root/a': int_ds(3), 'root/b': int_ds(9), 'root/b/c': int_ds(2), 'root/b/d': int_ds(7)})
        expected = DataTree.from_dict(d={'root/a': int_ds(3*5), 'root/b':int_ds(9*4)})
        with pytest.raises(ValueError, match='not implemented for non-hollow trees')
        dtt.assert_equal(dt1*dt2, expected)

    def test_hollow_twoway_level_2(self):
        dt1 = DataTree.from_dict(d={'root/a/e': int_ds(5), 'root/a/f': int_ds(20), 'root/b': int_ds(4)})
        dt2 = DataTree.from_dict(d={'root/a': int_ds(3), 'root/b/c': int_ds(2), 'root/b/d': int_ds(7)})
        expected = DataTree.from_dict(d={
            'root/a/e': int_ds(3*5),
            'root/a/f': int_ds(3*20),
            'root/b/c': int_ds(4*2),
            'root/b/d': int_ds(4*7)
            }
            )
        dtt.assert_equal(dt1*dt2, expected)
