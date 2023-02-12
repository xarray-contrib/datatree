import os

import pytest

from datatree.io import open_datatree
from datatree.testing import assert_equal
from datatree.tests import requires_h5netcdf, requires_netCDF4, requires_zarr

zarr_test_versions = [None, 2]
if os.getenv("ZARR_V3_EXPERIMENTAL_API", False):
    zarr_test_versions.append(3)


class TestIO:
    @requires_netCDF4
    def test_to_netcdf(self, tmpdir, simple_datatree):
        filepath = str(
            tmpdir / "test.nc"
        )  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree
        original_dt.to_netcdf(filepath, engine="netcdf4")

        roundtrip_dt = open_datatree(filepath)
        assert_equal(original_dt, roundtrip_dt)

    @requires_netCDF4
    def test_netcdf_encoding(self, tmpdir, simple_datatree):
        filepath = str(
            tmpdir / "test.nc"
        )  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree

        # add compression
        comp = dict(zlib=True, complevel=9)
        enc = {"/set2": {var: comp for var in original_dt["/set2"].ds.data_vars}}

        original_dt.to_netcdf(filepath, encoding=enc, engine="netcdf4")
        roundtrip_dt = open_datatree(filepath)

        assert roundtrip_dt["/set2/a"].encoding["zlib"] == comp["zlib"]
        assert roundtrip_dt["/set2/a"].encoding["complevel"] == comp["complevel"]

        enc["/not/a/group"] = {"foo": "bar"}
        with pytest.raises(ValueError, match="unexpected encoding group.*"):
            original_dt.to_netcdf(filepath, encoding=enc, engine="netcdf4")

    @requires_h5netcdf
    def test_to_h5netcdf(self, tmpdir, simple_datatree):
        filepath = str(
            tmpdir / "test.nc"
        )  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree
        original_dt.to_netcdf(filepath, engine="h5netcdf")

        roundtrip_dt = open_datatree(filepath)
        assert_equal(original_dt, roundtrip_dt)

    @requires_zarr
    @pytest.mark.parametrize("zarr_version", zarr_test_versions)
    def test_to_zarr(self, tmpdir, simple_datatree, zarr_version):
        filepath = str(
            tmpdir / "test.zarr"
        )  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree
        original_dt.to_zarr(filepath, zarr_version=zarr_version)

        roundtrip_dt = open_datatree(filepath, engine="zarr", zarr_version=zarr_version)
        assert_equal(original_dt, roundtrip_dt)

    @requires_zarr
    @pytest.mark.parametrize("zarr_version", zarr_test_versions)
    def test_zarr_encoding(self, tmpdir, simple_datatree, zarr_version):
        import zarr

        filepath = str(
            tmpdir / "test.zarr"
        )  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree

        comp = {"compressor": zarr.Blosc(cname="zstd", clevel=3, shuffle=2)}
        enc = {"/set2": {var: comp for var in original_dt["/set2"].ds.data_vars}}
        original_dt.to_zarr(filepath, encoding=enc, zarr_version=zarr_version)
        roundtrip_dt = open_datatree(filepath, engine="zarr", zarr_version=zarr_version)

        print(roundtrip_dt["/set2/a"].encoding)
        assert roundtrip_dt["/set2/a"].encoding["compressor"] == comp["compressor"]

        enc["/not/a/group"] = {"foo": "bar"}
        with pytest.raises(ValueError, match="unexpected encoding group.*"):
            original_dt.to_zarr(
                filepath, encoding=enc, engine="zarr", zarr_version=zarr_version
            )

    @requires_zarr
    @pytest.mark.parametrize("zarr_version", zarr_test_versions)
    def test_to_zarr_zip_store(self, tmpdir, simple_datatree, zarr_version):
        if zarr_version == 3:
            from zarr import ZipStoreV3 as ZipStore
        else:
            from zarr.storage import ZipStore

        filepath = str(
            tmpdir / "test.zarr.zip"
        )  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree
        store = ZipStore(filepath)
        original_dt.to_zarr(store, zarr_version=zarr_version)

        roundtrip_dt = open_datatree(store, engine="zarr", zarr_version=zarr_version)
        assert_equal(original_dt, roundtrip_dt)

    @requires_zarr
    def test_to_zarr_not_consolidated(self, tmpdir, simple_datatree):
        filepath = tmpdir / "test.zarr"
        zmetadata = filepath / ".zmetadata"
        s1zmetadata = filepath / "set1" / ".zmetadata"
        filepath = str(filepath)  # casting to str avoids a pathlib bug in xarray
        original_dt = simple_datatree
        original_dt.to_zarr(filepath, consolidated=False)
        assert not zmetadata.exists()
        assert not s1zmetadata.exists()

        with pytest.warns(RuntimeWarning, match="consolidated"):
            roundtrip_dt = open_datatree(filepath, engine="zarr")
        assert_equal(original_dt, roundtrip_dt)
