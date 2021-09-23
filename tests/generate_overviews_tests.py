from common import initialize_test_yml_list_measurement
from view import VIEW
import tifffile
import pathlib as pl
from nose.tools import raises


class OverviewsGenerator(object):

    def __init__(self):
        self.test_yml, self.test_animal, self.test_measu = initialize_test_yml_list_measurement()

        self.view = VIEW()

        self.view.update_flags_from_ymlfile(self.test_yml)
        self.view.update_flags(get_default_overview_flags_hack())

    def generate(self, flags_to_update, suffix):

        self.view.update_flags(flags_to_update)
        self.view.load_measurement_data(self.test_animal, self.test_measu)
        self.view.calculate_signals()
        frame_data2write, data_limits = self.view.generate_overview_for_output_for_current_measurement()

        test_folder = pl.Path(self.view.flags["STG_OdorReportPath"]) / "test_single_overviews"

        if not test_folder.is_dir():
            test_folder.mkdir()

        op_file_name = test_folder / f"{self.view.flags['STG_ReportTag']}_{self.view.p1.metadata.ex_name}{suffix}.tif"

        tifffile.imsave(op_file_name, data=frame_data2write, photometric="rgb")


def get_default_overview_flags_hack():

    return {"SO_Method": 0, "CTV_Method": 22, "CTV_firstframe": 25, "CTV_lastframe": 35}


def generate_overviews(flags_to_update, suffix):

    og = OverviewsGenerator()
    og.generate(flags_to_update, suffix)


def test_defaults():

    generate_overviews(flags_to_update={}, suffix="_defaults")


def test_no_colorbar():

    generate_overviews(flags_to_update={"CTV_scalebar": 0}, suffix="_no_scalebar")


def test_rotate_flags():
    """
    Testing generating overview with different rotate flags
    """

    flags = {"SO_individualScale": 3, "SO_indiScale3factor": 0.25}

    for rot in range(1, 8):

        flags["SO_rotateImage"] = rot
        generate_overviews(flags, f"SO_rotateImage_{rot}")

    flags["SO_reverseIt"] = True
    generate_overviews(flags, "SO_reverseIt_True")


def test_scale_flags():
    """
    Testing generating overviews with different scale flags
    """

    percentile_value = 20
    flags_with_percentile = {"SO_percentileScale": True, "SO_percentileValue": percentile_value}
    flags_without_percentile = {}

    cutborder = 5
    flags_with_cutborder = {"SO_cutborder": cutborder}

    flag_types = {f"_percentileValue{percentile_value}": flags_with_percentile,
                  "": flags_without_percentile,
                  f"_cutborder{cutborder}": flags_with_cutborder}

    for label, flags_to_copy in flag_types.items():
        for indiscale in [1, 2, 4, 5, 6,
                          11, 12, 14, 15, 16,
                          21, 22, 24, 25, 26]:
            flags = flags_to_copy.copy()
            flags["SO_individualScale"] = indiscale
            generate_overviews(flags, f"SO_individualScale{indiscale}{label}")

        for indiscale in [3, 13, 23]:
            flags = flags_to_copy.copy()
            flags["SO_individualScale"] = indiscale
            flags["SO_indiScale3factor"] = 0.25
            generate_overviews(flags, f"SO_individualScale{indiscale}_factor0p25{label}")

            flags = flags_to_copy.copy()
            flags["SO_individualScale"] = indiscale
            flags["SO_indiScale3factor"] = 0.4
            generate_overviews(flags, f"SO_individualScale{indiscale}_factor0p4{label}")

            flags = flags_to_copy.copy()
            flags["SO_individualScale"] = indiscale
            flags["SO_indiScale3factor"] = 0
            generate_overviews(flags, f"SO_individualScale{indiscale}_factor0{label}")

@raises(ValueError)
def test_large_bordercut():
    """
    Testing generation of overview when SO_cutborder is inappropriately large
    """

    generate_overviews({"SO_cutborder": 106}, "_impossible")



def test_filters():
    """
    Testing generating overviews with spatial filters
    """

    generate_overviews({"Signal_Signal_FilterSpaceFlag": True, "Signal_Signal_FilterSpaceSize": 3, "SO_individualScale": 3,
                        "SO_indiScale3factor": 0.25}, "space_filter_3")

    generate_overviews({"Signal_Signal_FilterSpaceFlag": True, "Signal_Signal_FilterSpaceSize": 3, "SO_withinArea": True},
                       "space_filter_3_withinArea_true")


def test_SO_withinArea():
    """
    Testing generating overviews with SO_withinArea set
    """

    generate_overviews({'SO_withinArea': True,
                        'SO_individualScale': 3,
                        "SO_indiScale3factor": 0.25},
                        "SO_within_area_True")

    generate_overviews({'SO_withinArea': True,
                        'SO_thresholdShowImage': "bgColor",
                        'SO_individualScale': 3,
                        "SO_indiScale3factor": 0.25},
                       "SO_within_area_True_Image_bgColor")

    generate_overviews({'SO_withinArea': True,
                        'SO_individualScale': 3,
                        "SO_indiScale3factor": 0.25,
                        "SO_cutborder": 5},
                        "SO_within_area_True_cutBorder5")


def test_thresholdOn():
    """
    Testing generating overviews with different values of SO_thresholdOn
    """

    for within_area in (True, False):

        threshold_on_vals = {"foto1": [("a1000", "a400"), ("r50", "r30")],
                             "overview": [("a0.05","a-0.05"), ("r50", "r30")]}
        for threshold_on, threshold_vals in threshold_on_vals.items():
            for (threshold_pos, threshold_neg) in threshold_vals:
                generate_overviews({'SO_withinArea': within_area,
                                    'SO_thresholdOn': threshold_on,
                                    'SO_lowerThreshPositiveResps': threshold_pos,
                                    'SO_upperThreshNegativeResps': threshold_neg,
                                    'SO_individualScale': 3,
                                    "SO_indiScale3factor": 0.25},
                                    f"SO_thresholdOn_{threshold_on}"
                                    f"_vals_{threshold_pos}{threshold_neg}"
                                    f"_withinArea_{within_area}")


def test_thresholdShowImage():
    """
    Testing generating overviews with different settings for SO_thresholdShowImage and SO_threshold_scale
    """

    for threshold_show_image in ["foto1", "bgColor"]:
        for threshold_scale in ["full", "onlyShown"]:

            generate_overviews({"SO_thresholdShowImage": threshold_show_image,
                                "SO_thresholdScale": threshold_scale,
                                'SO_thresholdOn': "foto1",
                                'SO_thresholdOnValue': -1000,
                                'SO_individualScale': 3,
                                "SO_indiScale3factor": 0.25
                                },
                                f"SO_thresholdOn_foto1_val_-1000_Image_"
                                f"{threshold_show_image}_scale_{threshold_scale}")


def test_bgColor():
    """
    Testing generating overviews with SO_bgColor set
    """

    generate_overviews({'SO_withinArea': True,
                        'SO_thresholdShowImage': "bgColor",
                        'SO_individualScale': 3,
                        "SO_bgColor": 'g',
                        "SO_indiScale3factor": 0.25},
                       "SO_within_area_True_Image_bgColor_green")

def test_bgColor_fgColor():
    """
    Testing generating overviews with SO_bgColor set
    """

    generate_overviews({
                        "SO_bgColor": 'y',
                        "SO_fgColor": 'r'
                        },
                       "_bgColor_yellow_fg_color_red")


def test_scale_legend_factor():
    """
    Testing setting SO_scaleLegendFactor
    """

    for factor in (10, 100):
        generate_overviews({"SO_individualScale": 2,
                            "SO_percentileScale": True,
                            "SO_percentileValue": 20,
                            "SO_scaleLegendFactor": factor},
                           f"_scaleLegendFactor{factor}")


def test_showROIs():
    """
    Testing overview generation with different types of perimeters
    """

    test_values = [10, 13, 14, 15, 20, 23, 24, 25]

    for test_value in test_values:
        print(f"Testing with SO_showROIs={test_value}")
        og = OverviewsGenerator()

        og.generate(flags_to_update={"SO_showROIs": test_value}, suffix=f"_showROI{test_value}")

    og = OverviewsGenerator()
    og.generate({"SO_showROIs": 15, "SO_cutborder": 5}, "showROIs15_cutborder5")


# def test_fgColor():
#     """
#     Testing generating movies with SO_fgColor set
#     """
#
#     generate_overviews({"SO_fgColor": "m"},
#                         "SO_with_fgColor_magenta")


if __name__ == '__main__':
    # test_defaults()
    # test_thresholdOn()
    # test_scale_flags()
    test_showROIs()


