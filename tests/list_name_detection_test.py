from view.python_core.flags import FlagsManager
from common import get_example_data_root_path


def check_list_name_detection(yml_name, animal, expected_list_name):

    flags = FlagsManager()
    flags.read_flags_from_yml(yml_name)
    flags.update_flags({"STG_ReportTag": animal})

    assert expected_list_name == flags.get_existing_lst_file()


def test_FID_setting_only():
    """
    Testing finding existing list file for the case when only settings.xls files are present
    :return:
    """

    data_root = get_example_data_root_path()

    project_root = data_root / "LM_Till_only_FID"
    test_yml = str(project_root/ "usage_till.yml")
    animal = "LM_GC-FID_or22a_170816a"
    expected_list = str(project_root / "lists" / "LM_GC-FID_or22a_170816a.settings.xls")

    check_list_name_detection(yml_name=test_yml, animal=animal, expected_list_name=expected_list)


def test_FID_LSTMixed():
    """
    Testing finding existing list file for the case when lst.xls and .lst files are present
    :return:
    """

    data_root = get_example_data_root_path()

    project_root = data_root / "HS_Till"
    test_yml = str(project_root / "usage_till.yml")
    animal = "HS_bee_PELM_180416b"
    expected_list = str(project_root / "IDLlist" / "HS_bee_PELM_180416b.lst.xls")

    check_list_name_detection(yml_name=test_yml, animal=animal, expected_list_name=expected_list)


def test_FID_XLSMixed():
    """
    Testing finding existing list file for the case when lst.xls and .settings.xls files are present
    :return:
    """

    data_root = get_example_data_root_path()

    project_root = data_root / "Or47a_test"
    test_yml = str(project_root / "usage_till_test.yml")
    animal = "AL_190506a_or47a"
    expected_list = str(project_root / "02_SETTINGS" / "AL_190506a_or47a.lst.xls")

    check_list_name_detection(yml_name=test_yml, animal=animal, expected_list_name=expected_list)


def test_FID_LSTXLS_only():
    """
    Testing finding existing list file for the case when only lst.xls files are present
    :return:
    """

    data_root = get_example_data_root_path()

    project_root = data_root / "SS_LSM"
    test_yml = str(project_root / "usage_lsm.yml")
    animal = "2019_08_15_locust_oregon green"
    expected_list = str(project_root / "Lists" / "2019_08_15_locust_oregon green.lst.xls")

    check_list_name_detection(yml_name=test_yml, animal=animal, expected_list_name=expected_list)


if __name__ == '__main__':

    test_FID_setting_only()