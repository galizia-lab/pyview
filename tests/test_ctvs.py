from common import initialize_test_yml_list_measurement
from view import VIEW
from view.python_core import ctvs
from view.python_core.overviews import generate_overview_frame
import inspect
import pathlib as pl
import numpy as np


def ctv_signatures_test():
    """
    Check if signatures of all csv functions are equal
    """
    ctv_funcs = [x for x in inspect.getmembers(ctvs) if callable(x)]

    for ctv_func in ctv_funcs[1:]:

        assert inspect.signature(ctv_func) == inspect.signature(ctv_funcs[0])


def check_ctv_generic(ctv_method):

    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    view = VIEW()

    view.update_flags_from_ymlfile(test_yml)

    view.update_flags({"CTV_Method": ctv_method, "SO_Method": 0})
    view.load_measurement_data(test_animal, test_measu)
    view.calculate_signals()

    overview_frames = generate_overview_frame(flags=view.flags, p1=view.p1)
    overview = overview_frames[0, :, :]

    expected_overview_fle_path = \
        pl.Path(view.flags["STG_MotherOfAllFolders"]) / "test_files" / f"ctv{ctv_method}_expected.npz"

    expected_overview = np.load(str(expected_overview_fle_path))["expected_overview"]
    assert np.allclose(overview, expected_overview)


def test_ctv_22():
    """
    Testing CTV 22 with FakeData
    """

    check_ctv_generic(22)


def test_ctv_35():
    """
    Testing CTV 35 with FakeData
    """

    check_ctv_generic(35)


if __name__ == '__main__':
    test_ctv_35()
