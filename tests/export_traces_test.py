from common import initialize_test_yml_list_measurement
from view import VIEW
import pathlib as pl
import shutil
from view.python_core.ctvs import get_all_available_ctvs
from view.python_core.gdm_generation.gdm_data_classes import GDMFile


class TraceExporter(object):

    def __init__(self):

        super().__init__()
        test_yml, self.test_animal, self.test_measu = initialize_test_yml_list_measurement()

        self.view = VIEW()

        self.view.update_flags_from_ymlfile(test_yml)

    def load_and_export(self, flags_to_update, file_suffix, flags_suffix):

        self.view.update_flags(flags_to_update)

        self.view.initialize_animal(self.test_animal)

        roi_data_dict, roi_file = self.view.get_roi_info_for_current_animal()

        # initialize and empty data frame to accumulate data
        gdm_file = GDMFile()

        # iterate over measurements of the animal
        for measu in self.view.get_measus_for_current_animal(analyze_values_to_use=(1,)):

            # load a measurement for the animal
            self.view.load_measurement_data_from_current_animal(measu)

            # calculate signals
            self.view.calculate_signals()

            # create glodatamix for the loaded measurement
            gdm_file_this_measu, _ = self.view.get_gdm_file_for_current_measurement(roi_data_dict)

            # accumulate
            gdm_file.append_from_a_gdm_file(gdm_file_this_measu)

        # compose output file name
        output_file = self.view.flags.get_gloDatamix_file_for_current_animal()

        output_file_path = pl.Path(output_file)

        test_gdm_folder =\
            pl.Path(self.view.flags["STG_OdorReportPath"]) / "test_gdms" / \
            f"{output_file_path.stem}{file_suffix}"

        if not test_gdm_folder.is_dir():
            test_gdm_folder.mkdir(parents=True)

        test_output_file = test_gdm_folder / f"gdm{flags_suffix}{output_file_path.suffix}"

        # save gloDatamix file
        gdm_file.write_to_csv(test_output_file)


def test_export_traces_rois():
    """
    Testing exporting traces using .roi files
    """

    exporter = TraceExporter()

    coor_path = pl.Path(exporter.view.flags["STG_OdormaskPath"])
    dest_roi_file = coor_path / "Fake_data.roi"

    for fle in coor_path.iterdir():

        if fle.name.startswith("FakeData") and fle.suffix == ".roi":

            shutil.copy(str(fle), str(dest_roi_file))

            exporter.load_and_export(
                flags_to_update={"RM_ROITrace": 3},
                file_suffix=f"_from_roi{fle.stem.lstrip('FakeData')}",
                flags_suffix="_defaults"
            )

            dest_roi_file.unlink()


def test_export_traces_mask_tif():
    """
    Testing exporting traces using .roi.tif files
    """

    exporter = TraceExporter()
    exporter.load_and_export(
        flags_to_update={"RM_ROITrace": 4},
        file_suffix="_from_roi_tif",
        flags_suffix="_defaults"
    )


def test_export_traces_different_ctvs():
    """
    Testing exporting traces with different CTVs
    """

    exporter = TraceExporter()
    for ctv in get_all_available_ctvs():
        exporter.load_and_export(
            flags_to_update={"RM_ROITrace": 3, "CTV_Method": ctv},
            file_suffix=f"_from_roi",
            flags_suffix=f"_ctv{ctv}"
        )


def test_export_traces_within_ROI():
    """
    Testing exporting traces considering the area file
    """

    exporter = TraceExporter()
    exporter.load_and_export(
        flags_to_update={"RM_ROITrace": 3, "GDM_withinArea": True},
        file_suffix="_from_roi",
        flags_suffix="_withinArea_True"
    )


def test_export_traces_chunks_only():
    """
    Testing exporting traces considering the area file
    """

    exporter = TraceExporter()
    exporter.load_and_export(
        flags_to_update=
        {
            "RM_ROITrace": 3,
            "GDM_outputType": "chunks_only",
            "GDM_chunkPostStim": 2,  # in seconds
            "GDM_chunkPreStim": 2,  # in seconds
        },
        file_suffix="_chunks_only",
        flags_suffix="_2secPrePostStim"
    )

    exporter.load_and_export(
        flags_to_update=
        {
            "RM_ROITrace": 3,
            "GDM_outputType": "chunks_only",
            "GDM_chunkPostStim": 100,  # in seconds
            "GDM_chunkPreStim": 100,  # in seconds
        },
        file_suffix="_chunks_only",
        flags_suffix="_full"
    )


if __name__ == '__main__':

    test_export_traces_rois()
    # test_export_traces_mask_tif()
    # test_export_traces_within_ROI()
    test_export_traces_chunks_only()