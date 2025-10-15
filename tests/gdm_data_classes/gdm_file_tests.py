from tests.common import get_example_data_root_path
from view.python_core.gdm_generation.gdm_data_classes import GDMFile
import pathlib as pl

def get_test_path():

    return pl.Path(__file__).parent.parent / "test_files" / "GDMFiles"

def test_read_from_csv_all():
    """
    Checking reading function from CSV with metadata_only set to False
    """

    test_file = get_test_path() / "simple_small1.gdm.csv"
    gdm_file = GDMFile.load_from_csv(test_file, metadata_only=False)

    assert all(v is not None for v in gdm_file.data_dict.values())

def test_read_from_csv_metadata_only():
    """
    Checking reading function from CSV with metadata_only set to True
    """

    test_file = get_test_path() / "simple_small1.gdm.csv"
    gdm_file = GDMFile.load_from_csv(test_file, metadata_only=True)

    assert all(v is None for v in gdm_file.data_dict.values())

    return gdm_file

def test_read_data_later_based_on_metadata():
    """
    Checking reading a CSV in metadata_only mode and then loading data for all indices
    """

    gdm_file = test_read_from_csv_metadata_only()

    gdm_file.check_load_data_if_missing()

    assert all(v is not None for v in gdm_file.data_dict.values())


def test_read_data_later_based_on_metadata_select_indices():
    """
    Checking reading a CSV in metadata_only mode and then loading data for select indices
    """

    indices_to_read = (1, 3)

    gdm_file = test_read_from_csv_metadata_only()

    gdm_file.check_load_data_if_missing(indices_to_check=indices_to_read)

    assert all(
        v is not None
        if k in indices_to_read
        else v is None
        for k, v in gdm_file.data_dict.items()
    )

def test_read_data_later_in_gdm_file_from_multiple_csv_files():
    """
    Checking reading gdm files from different CSVs in metadata_only mode, combining them and reading data later
    """

    test_file1 = get_test_path() / "simple_small1.gdm.csv"
    test_file2 = get_test_path() / "simple_small2.gdm.csv"

    gdm_file1 = GDMFile.load_from_csv(test_file1, metadata_only=True)
    gdm_file2 = GDMFile.load_from_csv(test_file2, metadata_only=True)

    orig_size1 = gdm_file1.metadata_df.shape[0]
    orig_size2 = gdm_file2.metadata_df.shape[0]

    gdm_file1.append_from_a_gdm_file(gdm_file2)

    assert gdm_file1.metadata_df.shape[0] == orig_size1 + orig_size2

    gdm_file1.check_load_data_if_missing()

    assert all(v is not None for v in gdm_file1.data_dict.values())


if __name__ == '__main__':

    # test_read_from_csv_metadata_only()
    test_read_data_later_based_on_metadata_select_indices()