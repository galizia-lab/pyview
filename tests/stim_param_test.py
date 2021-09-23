from view.python_core.measurement_list import MeasurementList
import pathlib as pl
import tempfile


def valid_stim_params_test():
    """
    Testing whether valid stim paramter settings do not cause an error
    :return:
    """

    valid_stim_list = 'tests/test_files/measurement_test_files/190112_locust_ip_VALID_stims.lst.xls'

    ml = MeasurementList.create_from_lst_file(valid_stim_list, LE_loadExp=4)
    for measu_index, measu in enumerate(ml.get_measus()):
        p1_metadata, extra_metadata = ml.get_p1_metadata_by_index(measu_index)


def invalid_stim_params_test():
    """
    Testing whether invalid stim parameter settings do  cause an error
    :return:
    """

    invalid_stim_list = 'tests/test_files/measurement_test_files/190112_locust_ip_INVALID_stims.lst.xls'

    ml = MeasurementList.create_from_lst_file(invalid_stim_list, LE_loadExp=4)
    for measu_index, measu in enumerate(ml.get_measus()):
        try:
            p1_metadata, extra_metadata = ml.get_p1_metadata_by_measu(measu)
        except ValueError as e:
            pass
        except AssertionError as e:
            pass


def stim_spec_test_generator():

    test_root = "tests/test_files/measurement_test_files/valid_files"

    test_root_path = pl.Path(test_root)
    dirs = [child for child in test_root_path.iterdir() if child.is_dir()]

    for direc in dirs:
        for child in direc.iterdir():
            if child.suffix == ".xls":
                try_importing_measurement_list.description = f"Testing with the stimulus specification in " \
                                                             f"{child.relative_to(test_root_path)}"
                yield try_importing_measurement_list, str(child)


def try_importing_measurement_list(xls):

    expected_csv = f"{xls.split('.')[0]}.csv"
    ml = MeasurementList.create_from_lst_file(xls, LE_loadExp=666)
    p1_metadata, extra_metadata = ml.get_p1_metadata_by_measu(1)
    temp_out = str(pl.Path(tempfile.gettempdir()) / "view_temp.csv")
    temp = p1_metadata["pulsed_stimuli_handler"].stimulus_frame.copy()
    del temp["Sampling Period"]
    temp.to_csv(str(temp_out))

    # this works for expected files saved from linux when tested on linux and windows, filecmp.cmp does not.
    # might have something to do line terminators
    with open(temp_out) as fho:
        with open(expected_csv) as fhe:
            assert fho.read() == fhe.read()


if __name__ == "__main__":

    # valid_stim_params_test()
    try_importing_measurement_list("tests/test_files/measurement_test_files/valid_files/"
                                   "one_stim/stimON_stimOFF.lst.xls")
    # try_importing_measurement_list("tests/test_files/measurement_test_files/valid_files/"
    #                                "two_stim_new_mixed/stimON_stimOFF_stimLen.lst.xls")


