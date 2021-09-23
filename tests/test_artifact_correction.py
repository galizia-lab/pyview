from view import VIEW
from view.python_core.io import write_tif_2Dor3D
from common import initialize_test_yml_list_measurement


def run_artifact_correction(flags_to_update, output_suffix=None):

    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    flags = {
        "LE_BleachCorrMethod": "None",
        "LE_BleachExcludeStimulus": False,
        "LE_BleachExcludeArea": False,
        "LE_BleachCutBorder": 0,
        "LE_ScatteredLightFactor": 0,
        "LE_ScatteredLightRadius": 50
    }

    flags.update(flags_to_update)

    vo = VIEW()
    vo.update_flags_from_ymlfile(yml_filename=test_yml)
    if isinstance(flags, dict):
        vo.update_flags(flags)

    vo.initialize_animal(animal=test_animal)
    vo.load_measurement_data_from_current_animal(measu=test_measu)

    if output_suffix is not None:
        op_dir = vo.flags.get_processed_data_dir_path() / "Artifact_corrected_raw"
        op_dir.mkdir(exist_ok=True)
        op_filename = op_dir / f"{test_animal}_{test_animal}{output_suffix}.tif"
        write_tif_2Dor3D(array_xy_or_xyt=vo.p1.raw1, tif_file=op_filename)


def test_no_bleach_method():
    """
    testing loading data without bleach correction
    """

    run_artifact_correction(
        flags_to_update={},
        # output_suffix="_BC_None"
    )


def test_no_bleach_with_scatter_light_correction():
    """
    testing loading data without bleach correction, but with scatter light correction
    """

    run_artifact_correction(
        flags_to_update={"LE_ScatteredLightFactor": 1},
        # output_suffix="_BC_None"
    )


def test_log_bleach_pixelwise():
    """
    testing loading data using pixelwise log bleach correction
    """

    run_artifact_correction(
        flags_to_update={
            "LE_BleachCorrMethod": "log_pixelwise"
        },
        # output_suffix="_BC_log_pixelwise"
    )


def test_log_bleach_pixelwise_excluding_area():
    """
    testing loading data using pixelwise log bleach correction with area exclusion
    """

    run_artifact_correction(
        flags_to_update={
            "LE_BleachCorrMethod": "log_pixelwise",
            "LE_BleachExcludeArea": True
        },
        # output_suffix="_BC_log_pixelwise_excludingArea"
    )


def test_log_bleach_pixelwise_excluding_stimulus():
    """
    testing loading data using pixelwise log bleach correction with stimulus exclusion
    """

    run_artifact_correction(
        flags_to_update={
            "LE_BleachCorrMethod": "log_pixelwise",
            "LE_BleachExcludeStimulus": True,
            "LELog_ExcludeSeconds": 5,
            "LE_PrestimEndBackground": 5
        },
        # output_suffix="_BC_log_pixelwise_excludingStimulus"
    )


def test_log_bleach_uniform():
    """
    testing loading data using uniform log bleach correction
    """

    run_artifact_correction(
        flags_to_update={
            "LE_BleachCorrMethod": "log_uniform"
        },
        # output_suffix="_BC_log_uniform"
    )


def test_log_bleach_uniform_excluding_area():
    """
    testing loading data using uniform log bleach correction with area exclusion
    """

    run_artifact_correction(
        flags_to_update={
            "LE_BleachCorrMethod": "log_uniform",
            "LE_BleachExcludeArea": True
        },
        # output_suffix="_BC_log_uniform_excludingArea"
    )


def test_log_bleach_uniform_excluding_stimulus():
    """
    testing loading data using uniform log bleach correction with stimulus exclusion
    """

    run_artifact_correction(
        flags_to_update={
            "LE_BleachCorrMethod": "log_uniform",
            "LE_BleachExcludeStimulus": True,
            "LELog_ExcludeSeconds": 5,
            "LE_PrestimEndBackground": 5
        },
        # output_suffix="_BC_log_uniform_excludingStimulus"
    )


def test_artifact_correction_filters_only():
    """
    testing loading data with no bleach correction, but with median filtering
    """

    flags_to_test = [
        {"Data_Median_Filter": 0},
        {"Data_Median_Filter": 1},
        {"Data_Median_Filter": 2},
        {"Data_Median_Filter": 3, "Data_Median_Filter_space": 2, "Data_Median_Filter_time": 3},
        {"Data_Mean_Filter": 0},
        {"Data_Mean_Filter": 1},
        {"Data_Mean_Filter": 2},
        {"Data_Mean_Filter": 3, "Data_Mean_Filter_space": 10, "Data_Mean_Filter_time": 10}
    ]

    for flags in flags_to_test:

        run_artifact_correction.description = f"Testing raw data filtering with {flags}"
        yield run_artifact_correction, flags


if __name__ == '__main__':

    # test_no_bleach_method()
    # test_log_bleach_pixelwise()
    # test_log_bleach_pixelwise_excluding_stimulus()
    test_log_bleach_uniform()
    # test_log_bleach_uniform_excluding_area()
    # test_log_bleach_uniform_excluding_stimulus()

    # test_no_bleach_with_scatter_light_correction()

    # run_artifact_correction(
    #     flags_to_update={"Data_Median_Filter": 3, "Data_Median_Filter_space": 10, "Data_Median_Filter_time": 10},
    #     output_suffix="_MedianFilteredSpace10Time10"
    # )
    #
    # run_artifact_correction(
    #     flags_to_update={"Data_Mean_Filter": 3, "Data_Mean_Filter_space": 10, "Data_Mean_Filter_time": 10},
    #     output_suffix="_MeanFilteredSpace10Time10"
    # )