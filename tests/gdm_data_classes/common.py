import pathlib as pl

from view.python_core.gdm_generation import GDMFile


def get_tst_path():

    return pl.Path(__file__).parent.parent / "test_files" / "GDMFiles"


def read_tst_file(filename, metadata_only):

    test_file = get_tst_path() / filename
    return GDMFile.load_from_csv(test_file, metadata_only=metadata_only)