from view.idl_folder_translation.pro2tapestry_conf import parse_pro_file, convert_pro_to_tapestry_config
import pathlib as pl
import textfsm
import pandas as pd
import tempfile


def test_parsing_pro():
    """
    Testing parsing a .pro file
    """

    test_file = pl.Path("tests") / "test_files" / "pro_tests" / "grl_A_5803a.pro"
    pro_data_df = parse_pro_file(test_file)

    expected_csv = pl.Path("tests") / "test_files" / "pro_tests" / "grl_A_5803a_expected.csv"

    pro_data_temp_op = pl.Path(tempfile.gettempdir()) / "grl_A_5803_temp_out.csv"

    pro_data_df.to_csv(pro_data_temp_op)

    # this works for expected files saved from linux when tested on linux and windows, filecmp.cmp does not.
    # might have something to do line terminators
    with open(pro_data_temp_op) as fho:
        with open(expected_csv) as fhe:
            assert fho.read() == fhe.read()


def test_converting_pro():
    """
    Testing converting a .pro file
    :return:
    """

    test_file = pl.Path("tests") / "test_files" / "pro_tests" / "grl_A_5803a.pro"

    test_op_yml = pl.Path(tempfile.gettempdir()) / "grl_A_5803_temp_out.yml"

    convert_pro_to_tapestry_config(
        output_yml_file=test_op_yml, input_pro_file=test_file, animal_tag="A_5803a", flags_to_override={})

    expected_yml = pl.Path("tests") / "test_files" / "pro_tests" / "grl_A_5803a_expected.yml"

    # this works for expected files saved from linux when tested on linux and windows, filecmp.cmp does not.
    # might have something to do line terminators
    with open(expected_yml) as fho:
        with open(test_op_yml) as fhe:
            assert fho.read() == fhe.read()


if __name__ == '__main__':

    # test_parsing_pro()
    test_converting_pro()