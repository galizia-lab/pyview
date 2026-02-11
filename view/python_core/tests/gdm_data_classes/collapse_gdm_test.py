import pathlib as pl
from collections.abc import Callable
from typing import Sequence

import pandas as pd
import pytest
from matplotlib import pyplot as plt

from view.python_core.gdm_generation.gdm_data_classes import GDMFile
from view.python_core.tests.common import get_example_data_root_path


def load_csvs_and_collapse(
    csvs_to_collapse: Sequence[pl.Path],
    csv_loading_options: dict,
    collapsing_options: dict,
    groupby: str | Sequence[str],
    metadata_filter: Callable[[pd.DataFrame], pd.Series] = None,
    write_reports_to: pl.Path = None,
):
    """
    Loads a list of csvs, collapses them and return the results
    :param csvs_to_collapse:
    :param csv_loading_options: the key value pairs of this dictionary will be passed to GDMFile.load_from_csv(..)
    when loading csvs as additional kwargs
    :param collapsing_options: the key value pairs of this dictionary will be passed to GDMFile.collapse_GDM(..)
    when loading csvs as additional kwargs
    :param groupby: will be passed to GDMFile.groupby for grouping by before collapsing
    :param metadata_filter: will be used to filter out rows before collapsing, see GDMFile.subset_based_on_callable
    :param write_reports_to: if not None, this folder will be created and reports created and written into it
    """
    gdm_file_all = GDMFile()
    for csv_to_collapse in csvs_to_collapse:
        gdm_file = GDMFile.load_from_csv(
            csv_to_collapse, **(csv_loading_options or {})
        )
        # TIL OR operator can be used for False-like coalescing
        # https://docs.python.org/3/reference/expressions.html#boolean-operations

        gdm_file_filtered = (
            gdm_file.subset_based_on_callable(metadata_filter=metadata_filter)
            if metadata_filter
            else gdm_file
        )

        gdm_file_all.append_from_a_gdm_file(gdm_file_filtered)

    collapsed_gdm_file_all = GDMFile()
    for grouping_inds, grouping_gdm_file in gdm_file_all.groupby(groupby):
        if write_reports_to:
            write_reports_to.mkdir(exist_ok=True)
            fig_alignment, axs_alignment = plt.subplots(
                nrows=2, ncols=1, figsize=(12, 8), layout="constrained"
            )
            fig_collapsing, ax_collapsing = plt.subplots(
                nrows=1, ncols=1, figsize=(12, 8), layout="constrained"
            )
            report_axes = [axs_alignment[0], axs_alignment[1], ax_collapsing]
        else:
            report_axes = None

        collapsed_gdm_row = grouping_gdm_file.collapse_GDM(
            **(collapsing_options or {}), report_axes=report_axes
        )
        collapsed_gdm_file_all.append_gdm_row(collapsed_gdm_row)

        if write_reports_to:
            grouping_inds_str = "_".join([str(x) for x in grouping_inds])
            fig_alignment.savefig(
                write_reports_to / f"Report_{grouping_inds_str}_Alignment.png",
                dpi=300,
            )
            fig_collapsing.savefig(
                write_reports_to
                / f"Report_{grouping_inds_str}_Collapsing.png",
                dpi=300,
            )

    return collapsed_gdm_file_all


def get_tst_paths():

    test_folder = get_example_data_root_path() / "gdm_collapsing"
    animals = ("HC_201125b", "HC_201126a", "HC_201126c")
    csv_paths = [
        test_folder / f"{animal}.gloDatamix.csv" for animal in animals
    ]

    return test_folder, csv_paths


def gen_collapsing_configs():

    test_folder, csv_paths = get_tst_paths()

    csv_loading_option_values = [
        {"metadata_only": False},
        {"metadata_only": True},
    ]

    def metadata_filter(df):
        return df["Odour"].apply(lambda x: x in ["HX2L", "ZHAE"])

    for csv_loading_options in csv_loading_option_values:
        collapsed_gdm_file = load_csvs_and_collapse(
            csvs_to_collapse=csv_paths,
            csv_loading_options=csv_loading_options,
            collapsing_options={
                "collapse_using": "nanmedian",
                "temporal_alignment": "align_starts",
            },
            groupby=["polarity", "Odour", "OConc", "trace type"],
            metadata_filter=metadata_filter,
        )

        expected_csv = (
            test_folder
            / "nanmedian_alignstarts"
            / "after_collapsing_expected.csv"
        )

        # compare_gdm_file_with_expected_csv_file.description \
        #     = f"Testsing GDM Collapsing: data initially read with {csv_loading_options}"
        # TODO port descriptions for use with pytest

        yield collapsed_gdm_file, expected_csv


configs = list(gen_collapsing_configs())


@pytest.mark.parametrize("gdm_file, expected_csv", configs)
def test_compare_gdm_file_with_expected_csv_file(
    gdm_file: GDMFile, expected_csv: pl.Path
):
    """
    Loads a GDMFile object from `expected_csv` and asserts if it's equal to `gdm_file` according to the "__eq__"
    operator defined for the class GDMFile
    """

    gdm_file_expected = GDMFile.load_from_csv(expected_csv)
    assert gdm_file == gdm_file_expected


def generate_reports_check():
    """
    Function for manually testing report generation feature of GDMFile.collapse_GDM, not yet automatized
    """
    test_folder, csv_paths = get_tst_paths()

    output_dir = pl.Path("/tmp/gdm_collapsing_report")

    load_csvs_and_collapse(
        csvs_to_collapse=csv_paths,
        csv_loading_options={"metadata_only": False},
        collapsing_options={
            "collapse_using": "nanmedian",
            "temporal_alignment": "align_starts",
        },
        groupby=["polarity", "Odour", "OConc", "trace type"],
        write_reports_to=output_dir,
    )


if __name__ == "__main__":
    test_compare_gdm_file_with_expected_csv_file(*configs[0])

    # generate_reports_check()
