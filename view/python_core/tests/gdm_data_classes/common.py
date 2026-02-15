import pathlib as pl

from view.python_core.gdm_generation import GDMFile
from view.python_core.get_internal_files import get_internal_test_files_path


def get_tst_path():

    return pl.Path(get_internal_test_files_path()) / "GDMFiles"


def read_tst_file(filename, metadata_only):

    test_file = get_tst_path() / filename
    return GDMFile.load_from_csv(test_file, metadata_only=metadata_only)
