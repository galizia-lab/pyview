from common import initialize_test_yml_list_measurement
from view import create_tapestry
from view.python_core.flags import FlagsManager
import pathlib as pl
import platform


def test_non_default():
    """
    Generating tapestries with non-default tapestry configs
    """
    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    flags_dummy = FlagsManager()
    flags_dummy.read_flags_from_yml(test_yml)

    def text_below(row):
        return f"{row['Odour']}_{row['OConc']}_{row['Pharma']}"

    progs_path = pl.Path(flags_dummy["STG_MotherOfAllFolders"]) / "IDLprogs" / "tapestry_configs"
    for child in progs_path.iterdir():
        if child.suffix == ".yml" and child.name != "defult.yml":

            if child.name.lower().find("linux") >= 0 and platform.system() != "Linux":
                continue
            elif child.name.lower().find("windows") >= 0 and platform.system() != "Windows":
                continue

            create_tapestry.description = f"Generating tapestry with {child.name}"
            yield create_tapestry, str(child), test_yml, text_below


def run_with_yml_name(yml_name):

    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    flags_dummy = FlagsManager()
    flags_dummy.read_flags_from_yml(test_yml)

    def text_below(row):
        return f"{row['Odour']}_{row['OConc']}_{row['Pharma']}"

    tapestry_config = pl.Path(flags_dummy["STG_MotherOfAllFolders"]) / "IDLprogs" / "tapestry_configs" / f"{yml_name}.yml"
    create_tapestry(init_yml_flags_file=test_yml, tapestry_config_file=str(tapestry_config),
                    text_below_func=text_below)


def test_default():
    """
    Generating tapestries with default tapestry configs
    """

    run_with_yml_name("default")


if __name__ == '__main__':
    # test_default()
    # run_with_yml_name("different_animals")
    # run_with_yml_name("with_movies_stack_tif")
    # run_with_yml_name("with_movies_libx264")
    run_with_yml_name("custom_csv_linux")
    # run_with_yml_name("custom_csv_windows")
    # run_with_yml_name("different_flags")