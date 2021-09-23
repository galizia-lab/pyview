import pathlib as pl
from view.gui.application_settings import get_view_qsettings_manager


def get_example_data_root_path():

    settings = get_view_qsettings_manager()
    if settings.contains("view_test_data_path"):
        existing_test_data_path_str = settings.value("view_test_data_path")
        existing_test_data_path = pl.Path(existing_test_data_path_str)

        if existing_test_data_path.is_dir():

            return existing_test_data_path

        else:
            raise FileNotFoundError(
                f"Could not find the following folder, to which VIEW is configured for storing test data."
                f"\n\n{existing_test_data_path_str}.\n\nPlease run the script 'setup_testing.py' in the root "
                f"directory of VIEW source code again to download view test data and configure view test path")

    else:
        raise ValueError(
            "pyVIEW needs some data for testing. Please run the script 'setup_testing.py' in the root "
            "directory of VIEW source code again to download view test data and configure view test path")


def get_example_dataset_roots():
    example_data_root = get_example_data_root_path()

    dataset_roots = []
    for child in example_data_root.iterdir():

        if child.is_dir() and any(x.name.lower().find("list") > 0 or x.name.lower().find("settings") > 0
                                  for x in child.iterdir()):

            dataset_roots.append(child)

    return dataset_roots


def initialize_test_yml_list_measurement():

    example_data_path = get_example_data_root_path()

    example_dataset_moaf = example_data_path / "FakeData"
    test_yml = example_dataset_moaf / "test_defaults.yml"
    test_animal = "FakeData"
    test_measu = 8

    return str(test_yml), test_animal, test_measu


