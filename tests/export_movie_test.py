from common import initialize_test_yml_list_measurement
from view import VIEW
import logging
import pathlib as pl
import shutil
from nose.tools import raises


def export_fake_data_movie(flags_to_update, movie_name_suffix):

    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    view = VIEW()

    view.update_flags_from_ymlfile(test_yml)
    view.update_flags(flags_to_update)
    view.load_measurement_data(test_animal, test_measu)
    view.calculate_signals()
    op_filename = view.export_movie_for_current_measurement()

    test_movies_folder = pl.Path(view.flags["STG_OdorReportPath"]) / "test_movies"

    if not test_movies_folder.is_dir():
        test_movies_folder.mkdir()

    op_filepath = pl.Path(op_filename)
    test_movie_path = test_movies_folder / f"{op_filepath.stem}{movie_name_suffix}{op_filepath.suffix}"

    if test_movie_path.is_dir():
        shutil.rmtree(test_movie_path)

    op_filepath.replace(test_movie_path)


def test_defaults():
    """
    Testing exporting movie with default flags
    """

    export_fake_data_movie({}, "defaults")


def test_rotate_flags():
    """
    Testing export_movie with different rotate flags
    """

    for rot in range(1, 8):

        flags = {"mv_rotateImage": rot}
        export_fake_data_movie(flags, f"mv_rotateImage_{rot}")

    flags = {"mv_reverseIt": True}
    export_fake_data_movie(flags, "mv_reverseIt_True")


def test_scale_flags():
    """
    Testing export_movie with different scale flags
    """

    percentile_value = 20
    flags_with_percentile = {"mv_percentileScale": True, "mv_percentileValue": percentile_value}
    flags_without_percentile = {}

    cutborder = 5
    flags_with_cutborder = {"mv_cutborder": cutborder}

    flag_types = {f"_percentileValue{percentile_value}": flags_with_percentile,
                  "": flags_without_percentile,
                  f"_cutborder{cutborder}": flags_with_cutborder}

    for label, flags_to_copy in flag_types.items():
        for indiscale in [1, 2, 4, 5, 6,
                          11, 12, 14, 15, 16,
                          21, 22, 24, 25, 26]:
            flags = flags_to_copy.copy()
            flags["mv_individualScale"] = indiscale
            export_fake_data_movie(flags, f"mv_individualScale{indiscale}{label}")

        for indiscale in [3, 13, 23]:
            flags = flags_to_copy.copy()
            flags["mv_individualScale"] = indiscale
            flags["mv_indiScale3factor"] = 0.25
            export_fake_data_movie(flags, f"mv_individualScale{indiscale}_factor0p25{label}")

            flags = flags_to_copy.copy()
            flags["mv_individualScale"] = indiscale
            flags["mv_indiScale3factor"] = 0.4
            export_fake_data_movie(flags, f"mv_individualScale{indiscale}_factor0p4{label}")

            flags = flags_to_copy.copy()
            flags["mv_individualScale"] = indiscale
            flags["mv_indiScale3factor"] = 0
            export_fake_data_movie(flags, f"mv_individualScale{indiscale}_factor0{label}")


def test_displayTime_flags():
    """
    Testing export movie with different flags for displaying frame time
    """

    export_fake_data_movie({"mv_displayTime": 0}, "without_frame_time")
    export_fake_data_movie({"mv_displayTime": 0.8}, "with_frame_time")
    export_fake_data_movie({"mv_displayTime": 0.5}, "with_frame_time_0p5")
    export_fake_data_movie({"mv_displayTime": 0.25}, "with_frame_time_0p25")
    export_fake_data_movie({"mv_displayTime": 0.8, "mv_suppressMilliseconds": True}, "with_frame_time_no_ms")


def test_mark_stimulus_flags():
    """
    Testing export movie with different mark stimulus flags
    """

    possible_values = [0, 1, 2, 3, 21]

    for ms in possible_values:
        export_fake_data_movie({"mv_markStimulus": ms}, f"with_mark_stimulus_{ms}")


def test_different_export_formats():
    """
    Testing export movie with different export formats
    """

    export_fake_data_movie({"mv_exportFormat": "libx264", 'mv_individualScale': 2}, "_indScale2_libx264")
    export_fake_data_movie({"mv_exportFormat": "single_tif", 'mv_individualScale': 2}, "_indScale2")
    export_fake_data_movie({"mv_exportFormat": "ayuv", 'mv_individualScale': 2}, "_indScale2_ayuv")

def test_filters():
    """
    Testing export movie with temporal and spatial filters
    """

    export_fake_data_movie({"Signal_Signal_FilterSpaceFlag": True, "Signal_Signal_FilterSpaceSize": 3}, "space_filter_3")
    export_fake_data_movie({"Signal_Signal_FilterTimeFlag": True, "Signal_Signal_FilterTimeSize": 3}, "time_filter_3")


def test_cutters():
    """
    Testing export movie with temporal and spatial cutters
    """

    export_fake_data_movie({"mv_FirstFrame": 5, "mv_LastFrame": 75,
                            'mv_individualScale': 3,
                            "mv_indiScale3factor": 0.25
                            }, "five_frame_cut_start_end")
    export_fake_data_movie({"mv_cutborder": 5,
                            'mv_individualScale': 3,
                            "mv_indiScale3factor": 0.25
                            }, "mv_cutborder_5")


def test_correct_stimulus_onset():
    """
    Testing export movie with stimulus onset correction
    """

    export_fake_data_movie({"mv_correctStimulusOnset": 10, "mv_markStimulus": 1}, "mv_correct_stimulus_onset_10")
    export_fake_data_movie({"mv_correctStimulusOnset": 1300, "mv_markStimulus": 1}, "mv_correct_stimulus_onset_1300")


def test_thresholdOn():
    """
    Testing export movie with different values of mv_thresholdOn
    """

    threshold_on_vals = {"foto1": [("a1000", "a400"), ("r50", "r30")],
                         "raw1": [("a1000", "a400"), ("r60", "r10")],
                         "sig1": [("a0.75", "a0.65"), ("r60", "r10")]}

    for within_area in (True, False):

        for threshold_on, threshold_vals in threshold_on_vals.items():
            for (threshold_pos, threshold_neg) in threshold_vals:

                export_fake_data_movie({
                                        'mv_withinArea': within_area,
                                        'mv_thresholdOn': threshold_on,
                                        'mv_lowerThreshPositiveResps': threshold_pos,
                                        'mv_upperThreshNegativeResps': threshold_neg,
                                        'mv_individualScale': 3,
                                        "mv_indiScale3factor": 0.25},
                                        f"mv_thresholdOn_{threshold_on}"
                                        f"_vals_{threshold_pos}{threshold_neg}_withinArea_{within_area}")


def test_thresholdShowImage():
    """
    Testing export movie with different settings for mv_thresholdShowImage
    """

    for threshold_show_image in ["foto1", "raw1", "bgColor"]:
        for threshold_scale in ["full", "onlyShown"]:

            export_fake_data_movie({"mv_thresholdShowImage": threshold_show_image,
                                    "mv_thresholdScale": threshold_scale,
                                    'mv_thresholdOn': "foto1",
                                    'mv_lowerThreshPositiveResps': "a1000",
                                    'mv_individualScale': 3,
                                    "mv_indiScale3factor": 0.25
                                    },
                                    f"mv_thresholdOn_foto1_posVal_a1000_Image_"
                                    f"{threshold_show_image}_scale_{threshold_scale}")

def test_withinArea():
    """
    Testing export movie with mv_withinArea set
    """

    export_fake_data_movie({'mv_withinArea': True,
                            'mv_individualScale': 3,
                            "mv_indiScale3factor": 0.25},
                           "mv_within_Mask_True")

    export_fake_data_movie({'mv_withinArea': True,
                            'mv_individualScale': 3,
                            "mv_indiScale3factor": 0.25,
                            "mv_cutborder": 5},
                           "mv_within_Mask_True_cutBorder5")


def test_bgColor():
    """
    Testing export movie with mv_bgColor set
    """

    export_fake_data_movie({"mv_bgColor": "g"},
                           "mv_with_bgColor_green")


def test_fgColor():
    """
    Testing export movie with mv_fgColor set
    """

    export_fake_data_movie({"mv_fgColor": "m"},
                           "mv_with_fgColor_magenta")


def test_mark_rois():
    """
    Testing export movie with ROIs marked
    """

    base_flags = {'mv_individualScale': 3, "mv_indiScale3factor": 0.25}

    test_values = [10, 13, 14, 15]

    for test_value in test_values:
        flags2use = base_flags.copy()
        flags2use["mv_showROIs"] = test_value
        export_fake_data_movie(flags_to_update=flags2use, movie_name_suffix=f"mv_showROIs{test_value}")

        flags2use_new = flags2use.copy()
        flags2use_new["mv_rotateImage"] = 3
        export_fake_data_movie(flags_to_update=flags2use_new, movie_name_suffix=f"mv_showROIs{test_value}_rotate3")

        flags2use_new = flags2use.copy()
        flags2use_new["mv_cutborder"] = 5
        export_fake_data_movie(flags_to_update=flags2use_new, movie_name_suffix=f"mv_showROIs{test_value}_cutborder5")

@raises(ValueError)
def test_large_bordercut():
    """
    Testing export movie when mv_cutborder is inappropriately large
    """

    export_fake_data_movie({"mv_cutborder": 106}, "mv_impossible")


def test_fonts():
    """
    Testing export movie with different fonts
    """
    export_fake_data_movie({"mv_markStimulus": 2, "mv_fontName": "DroidSerif-Bold"}, "mv_fontName_DroidSerifBold")
    export_fake_data_movie({"mv_markStimulus": 2, "mv_fontName": "OpenSans-Regular"}, "mv_fontName_OpenSansRegular")
    export_fake_data_movie({"mv_markStimulus": 2, "mv_fontName": "DejaVuSerif-Bold"}, "mv_fontName_DejaVuSerifBold")


def test_mv_ygap():
    """
    Testing different settings of mv_ygap
    """
    for mv_ygap in [0, 10, 50, 100]:
        export_fake_data_movie({"mv_ygap": mv_ygap}, f"mv_ygap_{mv_ygap}")


def test_scale_legend_factor():
    """
    Testing setting mv_scaleLegendFactor
    """

    for factor in (10, 100):
        export_fake_data_movie({"mv_individualScale": 2,
                                "mv_percentileScale": True,
                                "mv_percentileValue": 20,
                                "mv_scaleLegendFactor": factor},
                               f"_scaleLegendFactor{factor}")


def test_bit_rate():
    """
    Testing setting mv_bitrate
    """

    export_fake_data_movie(
        {
            "mv_individualScale": 2,
            "mv_bitrate": f"{12 * 1024}k",
            "mv_exportFormat": "libx264"
        },
        "_bitrate_12M"
    )

# def test_with_recorded_data():
#     """
#     Testing view.python_core.movies.export_movie with recorded data
#     :return:
#     """
#
#     example_data_path = get_example_data_root_path()
#
#     test_list = example_data_path / "IP_Fura" / "IDLlist" / "190112_locust_ip.lst.xls"
#     test_yml = example_data_path / "IP_Fura" / "usage_till.yml"
#     full_output_name_without_extension = str(example_data_path / "IP_Fura" / "IDLoutput" / "movie_test")
#     test_measu = 0
#
#     # test_list = example_data_path / "20190821_SetupB_Pixel_Calibration"/ "Lists" / "pixel_calibration.lst"
#     # test_yml = example_data_path/ "20190821_SetupB_Pixel_Calibration"/ "calibration.yml"
#     # full_output_name_without_extension = \
#     #     example_data_path/"20190821_SetupB_Pixel_Calibration"/ "IDLoutput"/ "test_movie"
#     # test_measu = 2
#
#
#     # test_list = "/home/aj/SharedWithWindows/Sercan_CalciumGreen/Lists/20190809_SS_locust004_CaGreen.lst.xls"
#     # test_yml = '/home/aj/SharedWithWindows/Sercan_CalciumGreen/usage_till.yml'
#     # full_output_name_without_extension = "/home/aj/SharedWithWindows/Sercan_CalciumGreen/IDLoutput/movie"
#     # test_measu = 0
#
#
#     flags = FlagsManager()
#     flags.read_flags_from_yml(str(test_yml))
#
#
#     # flags.update_flags({"mv_exportFormat": "rawvideo"})
#     # flags.update_flags({"mv_exportFormat": "libx264"})
#     # flags.update_flags({"mv_bitrate": "2M"})
#
#     # flags.update_flags({"mv_exportFormat": "single_tif"})
#
#     flags.update_flags({"mv_exportFormat": "stack_tif"})
#
#     flags.update_flags({"mv_displayTime": True})
#     # flags.update_flags({"mv_markStimulus": 0})
#     # flags.update_flags({"mv_markStimulus": 1})
#     flags.update_flags({"mv_markStimulus": 2})
#
#     flags.update_flags({"mv_individualScale": 2})
#
#     # flags.update_flags({"mv_individualScale": 3})
#     # flags.update_flags({"mv_indiScale3factor": 0.2})
#
#     flags.update_flags({"mv_suppressMilliseconds": False})
#
#     flags.update_flags({"CTV_scalebar": True})
#
#     flags.update_flags({"mv_xgap": 60})
#     flags.update_flags({"mv_ygap": 60})
#
#     # flags.update_flags({"mv_reverseIt": True})
#
#     # flags.update_flags({"mv_rotateImage": 7})
#
#     # flags.update_flags({"mv_SpeedFactor": 0.333})
#
#     # flags.update_flags({"mv_percentileScale": True})
#     # flags.update_flags({"mv_percentileValue": 10})
#
#     measurement_list = MeasurementList(str(test_list), LE_loadExp="3")
#
#     p1 = measurement_list.get_p1_metadata_by_measu(test_measu)
#
#     loadDataMaster(p1=p1, flag=flags.to_series())
#
#     CalcSigMaster(p1=p1, flag=flags.to_series())
#
#     export_movie(p1, flags=flags,
#                  full_filename_without_extension=full_output_name_without_extension)
#


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)
    # test_with_recorded_data()
    # test_scale_flags()
    test_large_bordercut()
    # test_withinArea()
    # test_correct_stimulus_onset()
    # test_mark_rois()
    # test_different_export_formats()
    # test_bit_rate()
