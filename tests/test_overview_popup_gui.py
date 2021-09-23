from common import initialize_test_yml_list_measurement
from view import VIEW
from view.python_core.overviews import pop_show_overview


def test_different_configs():
    """
    Testing different configurations of GUI pop up window for overviews
    """

    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    vo = VIEW()
    vo.update_flags_from_ymlfile(test_yml)
    vo.load_measurement_data(animal=test_animal, measu=test_measu)
    vo.calculate_signals()

    vo.update_flags({"CTV_Method": "22and35", "SO_individualScale": 3})

    pop_show_overview.description = "Testing defaults"
    yield pop_show_overview, vo.flags, vo.p1, "test", None, None

    for stim_nr, feature_nr in [([0], [0]), ([0], "all"), ("all", [0]), ("all", "all")]:
        pop_show_overview.description = f"Testing stimulus number={stim_nr} and feature number={feature_nr}"
        yield pop_show_overview, vo.flags, vo.p1, "test", stim_nr, feature_nr


if __name__ == '__main__':

    for args in test_different_configs():

        args[0](*args[1:])
        input("Press any key to close figure and continue...")

