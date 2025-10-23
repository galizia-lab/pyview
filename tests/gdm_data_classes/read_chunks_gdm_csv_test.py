import pandas as pd
import pytest

from tests.gdm_data_classes.common import get_tst_path
from view.python_core.gdm_generation.gdm_data_classes import read_chunks_gdm_csv
import pathlib as pl

def cases_configs():

    test_path = get_tst_path()

    parameter_sets = [{"metadata_only": True}, {"limit_to_rows": [3]}, {"limit_to_rows": [1, 4]}]
    expected_csv_filenames = ["metadata_only.csv", "one_row_only.csv", "two_rows_only.csv"]

    for ind, parameter_set in enumerate(parameter_sets):

        read_csv_df = read_chunks_gdm_csv(
            input_csv=test_path / "simple_small1.gdm.csv",
            **parameter_set
        )

        expected_csv = test_path / "read_chunks_gdm_csv" / expected_csv_filenames[ind]

        # read_csv_assert_equality.description = f"Testsing read_chunks_gdm_csv with {expected_csv_filenames[ind]}"
        # TODO port descriptions for use with pytest

        yield read_csv_df, expected_csv

configs = list(cases_configs())

@pytest.mark.parametrize("csv_df, expected_csv", configs)
def read_csv_assert_equality(csv_df: pd.DataFrame, expected_csv: pl.Path | str):

    expected_csv_df = pd.read_csv(expected_csv, header=0, sep=';')
    csv_df_str = csv_df.astype(str)
    expected_csv_df_str = expected_csv_df.astype(str)
    assert csv_df_str.equals(expected_csv_df_str)