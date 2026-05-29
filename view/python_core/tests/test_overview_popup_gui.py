import pytest

from view import VIEW
from view.python_core.overviews import pop_show_overview
from view.python_core.tests.common import initialize_test_yml_list_measurement


def gen_different_configs():
    """
    Generate different configurations of GUI pop up window for overviews
    """

    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    vo = VIEW()
    vo.update_flags_from_ymlfile(test_yml)
    vo.load_measurement_data(animal=test_animal, measu=test_measu)
    vo.calculate_signals()

    vo.update_flags({"CTV_Method": "22and35", "SO_individualScale": 3})

    # pop_show_overview.description = "Testing defaults"
    # TODO port descriptions for use with pytest
    yield vo.flags, vo.p1, None, None

    for stim_nr, feature_nr in [
        ([0], [0]),
        ([0], "all"),
        ("all", [0]),
        ("all", "all"),
    ]:
        # pop_show_overview.description = f"Testing stimulus number={stim_nr} and feature number={feature_nr}"
        # TODO port descriptions for use with pytest
        yield vo.flags, vo.p1, stim_nr, feature_nr


configs = list(gen_different_configs())


@pytest.mark.parametrize("flags,p1,stim_nr,feature_nr", configs)
def test_different_configs(flags, p1, stim_nr, feature_nr):

    pop_show_overview(flags, p1, "test", stim_nr, feature_nr)


if __name__ == "__main__":
    for args in gen_different_configs():
        test_different_configs(*args)
        input("Press any key to close figure and continue...")
