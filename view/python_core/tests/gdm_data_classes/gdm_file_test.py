from view.python_core.gdm_generation import GDMFile
from view.python_core.tests.gdm_data_classes.common import read_tst_file


def test_read_from_csv_all():
    """
    Checking reading function from CSV with metadata_only set to False
    """

    gdm_file = read_tst_file("simple_small1.gdm.csv", metadata_only=False)

    assert all(v is not None for v in gdm_file.data_dict.values())


def test_read_from_csv_metadata_only():
    """
    Checking reading function from CSV with metadata_only set to True
    """

    gdm_file = read_tst_file("simple_small1.gdm.csv", metadata_only=True)

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
        v is not None if k in indices_to_read else v is None
        for k, v in gdm_file.data_dict.items()
    )


def test_read_data_later_in_gdm_file_from_multiple_csv_files():
    """
    Checking reading gdm files from different CSVs in metadata_only mode, combining them and reading data later
    """

    gdm_file1 = read_tst_file("simple_small1.gdm.csv", metadata_only=True)
    gdm_file2 = read_tst_file("simple_small2.gdm.csv", metadata_only=True)

    orig_size1 = gdm_file1.metadata_df.shape[0]
    orig_size2 = gdm_file2.metadata_df.shape[0]

    gdm_file1.append_from_a_gdm_file(gdm_file2)

    assert gdm_file1.metadata_df.shape[0] == orig_size1 + orig_size2

    gdm_file1.check_load_data_if_missing()

    assert all(v is not None for v in gdm_file1.data_dict.values())


def test_groupby_function():
    """
    Testing Groupby function of GDMFiles
    """

    gdm_file1 = read_tst_file("simple_small1.gdm.csv", metadata_only=False)

    grouping_column_sets = ["Animal", ["Animal", "Measu"]]
    grouping_inds_expected_sets = [
        ["animal1", "animal2"],
        [("animal1", 1), ("animal1", 2), ("animal2", 1), ("animal2", 2)],
    ]
    group_gdm_file_sizes_expected_sets = [[2, 2], [1, 1, 1, 1]]

    for (
        grouping_cols,
        grouping_inds_expected,
        group_gdm_file_sizes_expected,
    ) in zip(
        grouping_column_sets,
        grouping_inds_expected_sets,
        group_gdm_file_sizes_expected_sets,
    ):
        for serial_ind, (grouping_inds, group_gdm_file) in enumerate(
            gdm_file1.groupby(grouping_cols)
        ):
            assert grouping_inds == grouping_inds_expected[serial_ind]
            assert isinstance(group_gdm_file, GDMFile)
            assert (
                len(group_gdm_file.data_dict)
                == group_gdm_file_sizes_expected[serial_ind]
            )


if __name__ == "__main__":
    # test_read_from_csv_metadata_only()
    # test_read_data_later_based_on_metadata_select_indices()
    test_groupby_function()
