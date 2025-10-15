from tests.common import get_example_data_root_path
from view.python_core.gdm_generation.gdm_data_classes import GDMFile
import pathlib as pl

def common_run_func(csv_to_collapse: pl.Path, csv_after_collapsing_expected: pl.Path, collapsing_options: dict):

    gdm_file = GDMFile.load_from_csv(csv_to_collapse)
    gdm_file_collapsed = gdm_file.collapse_GDM(**collapsing_options)
    gdm_file_collapsed_expected = GDMFile.load_from_csv(csv_after_collapsing_expected)
    assert gdm_file_collapsed.__eq__(gdm_file_collapsed_expected)


def collapse_tests():

    test_folder = get_example_data_root_path() / "gdm_collapsing" / "nanmedian-alignstarts"

    common_run_func(
        csv_to_collapse=test_folder / "to_collapse.csv",
        csv_after_collapsing_expected=test_folder / "after_collapsing_expected.csv",
        collapsing_options={
            "collapse_using": "nanmedian", "temporal_alignment": "align_starts",
            "groupby": ["polarity", "Stimulus", "Odour", "trace type"]
        }
    )

if __name__ == '__main__':
    collapse_tests()

