import sys

import pytest

from datatree import DataTree, tutorial


@pytest.mark.network
class TestLoadSampleData:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.asset = "cesm2-lens"

    @pytest.fixture
    def monkeypatch_import_error(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "pooch", None)

    def test_download(self, tmp_path) -> None:
        cache_dir = tmp_path / tutorial._default_cache_dir_name
        dt = tutorial.open_datatree(self.asset, cache_dir=cache_dir)
        assert isinstance(dt, DataTree)

    def test_pooch_import_error(self, monkeypatch_import_error):
        with pytest.raises(ImportError):
            tutorial.open_datatree(self.asset)

    def test_invalid_datatree_sample_key(self):
        with pytest.raises(KeyError):
            tutorial.open_datatree("invalid")
