from common import get_example_data_root_path, initialize_test_yml_list_measurement

from view.python_core.flags import FlagsManager
from view.python_core.paths import get_existing_raw_data_filename
from view.python_core.view_object import VIEW
from view.python_core.p1_class import get_empty_p1


def load_calc_data(yml_file, animal, measus=None, flags=None):

    vo = VIEW()
    vo.update_flags_from_ymlfile(yml_filename=yml_file)
    if isinstance(flags, dict):
        vo.update_flags(flags)

    vo.initialize_animal(animal=animal)

    for measu in vo.get_measus_for_current_animal(analyze_values_to_use=(1, 2)):
        if measus is None or measu in measus:
            print(f"Doing animal={animal}, measu={measu}")
            vo.load_measurement_data_from_current_animal(measu=measu)
            vo.calculate_signals()

    return vo


def test_loading_all_data():

    yml_animal_dict = {
        "FakeData/test_defaults.yml": ["FakeData"],
        "HS_Till/usage_till.yml": ["HS_bee_PELM_180416b", "HS_bee_PELM_180424b"],
        "IP_Fura/usage_till.yml": ["190112_locust_ip", "190112_locust_ip2", "190529_locust_ip31"],
        "LM_Till_only_FID/usage_till.yml":
            ["LM_GC-FID_or22a_170816a", "LM_GC-FID_or22a_170816b", "LM_GC-FID_or22a_170816c"],
        "MR_Till/usage_till.yml": ["MR_190613c_or47a", "MR_190614a_or47a"],
        "MS_LSM/usage_lsm.yml": ["2020_02_06_OK107_GCaMP6f", "testview"],
        "Or47a_test/usage_till_test.yml":
            ["AL_190506a_or47a", "MR_190510b_or47a", "MR_190515b_or47a", "PG_190702a_or47a"],
        "SS_LSM/usage_lsm.yml": ["2019_08_15_locust_oregon green"],
        "Bente_Test/Bente_Test_2021.yml": ["190815_h2_El_test"],
        "MP_LIF/LIF_test.yml": ["sNPF_210623_bee07_res"]
    }

    example_data_root_path = get_example_data_root_path()

    for yml_relative_path, animals in yml_animal_dict.items():

        yml_file = str(example_data_root_path / yml_relative_path)

        for animal in animals:

            load_calc_data.description \
                = f"Testing loading data and signal calculation with yml={yml_relative_path} and animal={animal}"

            yield load_calc_data, yml_file, animal


def test_loading_data_without_measurement_list():
    """Testing loading data without measurement list"""
    example_data_root_path = get_example_data_root_path()
    yml_file = example_data_root_path / "HS_Till" / "usage_till.yml"
    animal = "HS_bee_PELM_180416b"

    flags = FlagsManager()
    flags.read_flags_from_yml(yml_file)

    view_obj = VIEW(flags=flags)

    raw_data_file \
        = example_data_root_path / "HS_Till" / "data" / "HS_bee_PELM_180416b.pst" / "dbb12DF.pst"

    view_obj.load_measurement_data_without_list_file(
        LE_loadExp=3,
        raw_data_files=[raw_data_file],
        sampling_rate=1 / 0.6,
        animal=animal)


if __name__ == '__main__':

    # load_calc_data(
    #     yml_file="/home/ajay/SharedWithWindows/view_test_data/HS_Till/usage_till.yml",
    #     animal="HS_bee_PELM_180416b")

    # load_calc_data(
    #     yml_file="/home/ajay/SharedWithWindows/view_test_data/FakeData/test_defaults.yml",
    #     animal="FakeData", flags={"LE_CalcMethod": 4})

    # load_calc_data(yml_file="/mnt/data/ViewData/IP_Fura/view_flags_all_defaultsFURA.yml",
    #                animal="190112_locust_ip2", flags={"LE_ScatteredLightFactor": 1})

    # load_calc_data(
    #     yml_file="/home/aj/SharedWithWindows/SS_LSM/usage_lsm.yml",
    #     animal="2019_08_09_locust_calcium green")

    load_calc_data(
        yml_file="/home/ajay/pyview_test_data/Bente_Test/Bente_Test_2021.yml",
        animal="190815_h2_El_test")

    # test_loading_data_without_measurement_list()

