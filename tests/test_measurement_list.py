from common import get_example_dataset_roots
from view.python_core.measurement_list import MeasurementList
from view.python_core.flags import FlagsManager
import pathlib as pl


def measurement_list_manager_loading(ext):

    def exclusion_check(yml_filename):

        yml_filename_lower = yml_filename.lower()

        to_exclude = ["fid_hanna9", "fidor", "log2settings"]

        return any([yml_filename_lower.find(x) >= 0 for x in to_exclude])

    for dataset_root in get_example_dataset_roots():

        yml_files = [x for x in dataset_root.iterdir() if x.suffix == ".yml" and not exclusion_check(x.name)]

        if len(yml_files):

            yml_file = yml_files[0]
            flags = FlagsManager()

            try:
                flags.read_flags_from_yml(yml_file)

                list_dir = pl.Path(flags["STG_OdorInfoPath"])

                if list_dir.is_dir():
                    for fle in list_dir.iterdir():

                        if fle.name.endswith(ext) and not fle.name.startswith("."):

                            measurement_list = MeasurementList.create_from_lst_file(str(fle), LE_loadExp=3)
                            yield measurement_list
            except FileNotFoundError as fnfe:
                pass


def test_reading_lst():
    """
    Testing importing lst files into view.python_core.managers.measurement_list.LSTList
    """

    for lst in measurement_list_manager_loading(".lst"):
        pass


def test_reading_settingsXLS():
    """
    Testing importing settings files into view.python_core.managers.measurement_list.SettingsXLSList
    """

    for lst in measurement_list_manager_loading(".settings.xls"):
        pass


def test_reading_LSTXLS():
    """
    Testing importing settings files into view.python_core.managers.measurement_list.LSTXLSList
    """

    for lst in measurement_list_manager_loading(".lst.xls"):
        pass


def run_get_p1_all(lst):

    for ind, measu in enumerate(lst.get_measus()):

        p1_metadata, extra_metadata = lst.get_p1_metadata_by_index(ind)
        pass


def test_lst2p1():
    """
    Testing metadata in lst files to p1
    """

    for ind, lst in enumerate(measurement_list_manager_loading(".lst")):
        run_get_p1_all(lst)


def test_settings2p1():
    """
    Testing metadata in settings files to p1
    """

    for ind, lst in enumerate(measurement_list_manager_loading(".settings.xls")):
        run_get_p1_all(lst)


def test_lstxls2p1():
    """
    Testing metadata in lst.xls files to p1
    """

    for ind, lst in enumerate(measurement_list_manager_loading(".lst.xls")):
        run_get_p1_all(lst)


if __name__ == "__main__":

    test_reading_lst()

    # print all lists in all test data sets
    # print("Legacy LST files")
    # for ml in measurement_list_manager_loading(".lst"):
    #     print(ml.last_measurement_list_fle)
    #
    # print("LST XLS files")
    # for ml in measurement_list_manager_loading(".lst.xls"):
    #     print(ml.last_measurement_list_fle)
    #
    # print("Settings XLS files")
    # for ml in measurement_list_manager_loading(".settings.xls"):
    #     print(ml.last_measurement_list_fle)



