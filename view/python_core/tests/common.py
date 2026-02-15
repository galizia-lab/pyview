import pathlib as pl

from view.gui.application_settings import get_view_qsettings_manager
from view.python_core.get_internal_files import get_internal_test_files_path


def get_example_data_root_path():

    settings = get_view_qsettings_manager()
    if settings.contains("view_test_data_path"):
        existing_test_data_path_str = settings.value("view_test_data_path")
        existing_test_data_path = pl.Path(existing_test_data_path_str)

        if existing_test_data_path.is_dir():
            return existing_test_data_path

        else:
            raise FileNotFoundError(
                f"Could not find the following folder, to which VIEW is configured for storing test data.\n\n{existing_test_data_path_str}.\n\nPlease download and register test data with VIEW as described in https://github.com/galizia-lab/pyview/wiki/Download-and-register-test-data"
            )

    else:
        raise ValueError(
            "pyVIEW needs some data for testing. Please download and register test data with VIEW "
            "as described in https://github.com/galizia-lab/pyview/wiki/Download-and-register-test-data"
        )


def get_example_dataset_roots():
    example_data_root = get_example_data_root_path()

    dataset_roots = []
    for child in example_data_root.iterdir():
        if child.is_dir() and any(
            x.name.lower().find("list") > 0
            or x.name.lower().find("settings") > 0
            for x in child.iterdir()
        ):
            dataset_roots.append(child)

    return dataset_roots


def initialize_test_yml_list_measurement(tiny_dataset=False):

    example_data_path = get_example_data_root_path()

    if tiny_dataset:
        example_dataset_moaf = example_data_path / "FakeData_tiny"
    else:
        example_dataset_moaf = example_data_path / "FakeData"

    test_yml = example_dataset_moaf / "test_defaults.yml"
    test_animal = "FakeData"
    test_measu = 8

    return str(test_yml), test_animal, test_measu


def get_synthetic_data_yml_path():

    return (
        pl.Path(get_internal_test_files_path())
        / "synthetic_data"
        / "view_synthetic_666.yml"
    )
