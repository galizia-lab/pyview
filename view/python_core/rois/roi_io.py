import logging
from abc import ABC, abstractmethod
from view.python_core.areas import AreaMaskIO
from view.python_core.flags import FlagsManager
from view.python_core.io import read_tif_2Dor3D
from view.python_core.paths import check_get_file_existence_in_folder
from view.python_core.rois.idl_rois import SquareIDLROIData, TIFFIDLROIData
from view.python_core.rois.iltis_rois import CircleILTISROIData, PolygonILTISROIData, SpatialFootprintROIData
import typing

from view.python_core.rois.non_file_based_rois import UniformROIData


class BaseROIIO(ABC):

    def __init__(self):

        super().__init__()

    @classmethod
    @abstractmethod
    def read(cls, flags: FlagsManager, measurement_label: str = "") -> typing.Tuple[dict, str]:

        return  # to be implemented in subclass


class ROIFileIO(BaseROIIO, ABC):

    def __init__(self):

        super().__init__()

    @classmethod
    def read(cls, flags: FlagsManager, measurement_label: str = "") -> typing.Tuple[dict, str]:
        """
        Read ROI data from a ROI file indicated by <flags> and optionally <measurement_label>
        :param flags: view flags object
        :param measurement_label: str, optional
        :return: roi_data_dict, roi_file
        roi_data_dict: dict with roi labels as keys and ROI Data objects as values
        roi_file: str, name of the file from which ROI data was read
        """

        parent_folders = cls.get_parent_dirs(flags)

        for parent_folder in parent_folders:
            roi_file = check_get_file_existence_in_folder(
                folder=parent_folder, possible_extensions=[cls.get_extension()],
                stems=flags.get_file_stem_hierarchy(measurement_label)
            )
            if roi_file is not None:
                break
        else:
            raise FileNotFoundError(
                f"Could not find a ROI file\nin any of {parent_folders}\nfor animal={flags['STG_ReportTag']}"
                f"\nand measurement_label={measurement_label}\nwith extension={cls.get_extension()}"
            )

        logging.getLogger("VIEW").info(f"Loading ROI data from {roi_file}")
        roi_data_list = cls.read_roi_file(roi_file, flags)

        # look for duplicate labels and issue warning
        roi_data_dict = {}
        for roi_data in roi_data_list:

            if roi_data.label in roi_data_dict:
                logging.getLogger("VIEW").warning(
                    f"Multiple glomeruli found with label {roi_data.label} in {roi_file}. Ignoring the "
                    f"second one")

            roi_data_dict[roi_data.label] = roi_data

        return roi_data_dict, roi_file

    @classmethod
    @abstractmethod
    def get_extension(cls):

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def read_roi_file(cls, roi_file, flags):

        raise NotImplementedError

    @classmethod
    @abstractmethod
    def write(cls, filename, roi_datas):

        raise NotImplementedError

    @classmethod
    def get_parent_dirs(cls, flags):

        return [flags.get_coor_dir_str()]


class IDLCoorFileIO(ROIFileIO):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_extension(cls):

        return ".coor"

    @classmethod
    def read_roi_file(cls, roi_file, flags):
        """
        Read coor file and return a list of objects containing information of square ROIs in it.
        :param roi_file: str, path to a coor file on the file system
        :param flags: view flags object
        :return: list of SquareIDLROIData objects
        """
        with open(roi_file) as fh:
            text_lines = fh.readlines()

        n_rois = int(text_lines[0])
        assert len(text_lines) - 1 >= n_rois, f"The number of ROIs indicated in the first line exceeds the number" \
                                              f"of ROI lines that follow in {roi_file}"
        roi_data = []
        for roi_ind in range(n_rois):
            roi = SquareIDLROIData.read_from_text_line(text_lines[1 + roi_ind])
            roi.half_width = flags["RM_Radius"]
            roi.roi_file = roi_file
            roi_data.append(roi)

        return roi_data

    @classmethod
    def write(cls, filename, roi_datas):

        raise NotImplementedError


class IDLAREAFileIO(ROIFileIO):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_extension(cls):

        return ".Area"

    @classmethod
    def read_roi_file(cls, roi_file, flags):
        """
        Read IDL AREA file and return a list with one SpatialFootprintROIData object
        :param roi_file: str, path to a AREA file on the file system
        :param flags: view flags object
        :return: list of one SpatialFootprintROIData object
        """

        idl_tiff_frame = AreaMaskIO().read_footprint(roi_file)

        roi_data = TIFFIDLROIData(idl_tiff_frame=idl_tiff_frame, label="Area0")
        return [roi_data]

    @classmethod
    def write(cls, filename, roi_datas):
        raise NotImplementedError

    @classmethod
    def get_parent_dirs(cls, flags):
        return [flags.get_area_dir_str(), flags.get_coor_dir_str()]


class ILTISTextROIFileIO(ROIFileIO):

    def __init__(self):

        super().__init__()

    @classmethod
    def get_extension(cls):

        return ".roi"

    @classmethod
    def read_roi_file(cls, roi_file, flags):
        """
        Read .roi file and return information as list of roi objects
        :param roi_file: str, path to a AREA file on the file system
        :param flags: view flags object
        :return: list of roi objects, belonging to one of the classes: PolygonILTISROIData, CircleILTISROIData
        """
        with open(roi_file) as fh:
            text_lines = fh.readlines()

        roi_data = []
        for text_line in text_lines:
            if text_line.startswith("circle"):
                class_to_use = CircleILTISROIData
            elif text_line.startswith("polygon"):
                class_to_use = PolygonILTISROIData
            else:
                raise NotImplementedError

            roi_data.append(class_to_use.read_from_text_line(text_line))

        return roi_data

    @classmethod
    def write(cls, filename: str, roi_datas: list):
        """
        Write information in ROIs <roi_datas> into the file <filename> as text.
        :param filename: str, path of a file on filesystem
        :param roi_datas: list of objects, belonging to one of the classes: PolygonILTISROIData, CircleILTISROIData
        :return: None
        """
        lines_to_write = [roi_data.write_to_text_line() for roi_data in roi_datas]

        with open(filename, "w") as fh:

            fh.writelines(lines_to_write)


class ILTISTiffROIFileIO(ROIFileIO):

    def __init__(self):

        super().__init__()

    @classmethod
    def read(cls, flags: FlagsManager, measurement_label: str = "", labels=()) -> typing.Tuple[dict, str]:
        """
        Read ROI data from a ROI file indicated by <flags> and optionally <measurement_label>
        :param flags: view flags object
        :param measurement_label: str, optional
        :param labels: iterable, of str. Must have same number of elements as the number of pages in <file>
        :return: roi_data_dict, roi_file
        roi_data_dict: dict with roi labels as keys and ROI Data objects as values
        roi_file: str, name of the file from which ROI data was read
        """
        roi_data_dict_temp, roi_file = super().read(flags=flags, measurement_label=measurement_label)

        roi_data_dict = {}
        if len(labels) == 0:
            roi_data_dict = roi_data_dict_temp
        elif len(labels) == len(roi_data_dict_temp):
            for label, (roi_label, roi_data) in zip(labels, roi_data_dict_temp.items()):
                roi_data.label = label
                roi_data_dict[label] = roi_data
        else:
            logging.getLogger("VIEW").warning(
                f"The specified tiff file, {roi_file}, has {len(roi_data_dict_temp)}, "
                f"while {len(labels)} were specified. Ignoring the labels specified")
            roi_data_dict = roi_data_dict_temp

        return roi_data_dict, roi_file

    @classmethod
    def get_extension(cls):

        return ".roi.tif"

    @classmethod
    def read_roi_file(cls, roi_file, flags):
        """
        Read spatial footprints of ROIs in the tiff file <file>. Spatial footprints are individually normalized by
        dividing by their maximum pixel values and all pixels with value lower than <thresh> will be considered to
        belong to the ROI.
        :param roi_file: str, path to a TIFF file on file system
        :param flags, view flags object
        :returns: list, of SpatialFootprintROIData
        """

        roi_footprints, labels = read_tif_2Dor3D(roi_file, return_3D=True)

        if labels is None:
            labels = [str(x) for x in range(roi_footprints.shape[2])]

        roi_data = []

        for roi_ind, label in enumerate(labels[:roi_footprints.shape[2]]):
            roi = SpatialFootprintROIData(
                spatial_footprint=roi_footprints[:, :, roi_ind],
                thresh=flags["RM_ROIThreshold"], label=label)
            roi_data.append(roi)

        return roi_data

    @classmethod
    def write(cls, filename, roi_datas):

        raise NotImplementedError


class ILTISAreaROIFileIO(ILTISTiffROIFileIO):

    def __init__(self):

        super().__init__()

    @classmethod
    def get_extension(cls):

        return ".area.tif"

    @classmethod
    def write(cls, filename, roi_datas):
        raise NotImplementedError

    @classmethod
    def get_parent_dirs(cls, flags):
        return [flags.get_area_dir_str(), flags.get_coor_dir_str()]


class NonFileUniformROIIO(BaseROIIO):

    def __init__(self):

        super().__init__()

    @classmethod
    def read(cls, flags: FlagsManager, measurement_label: str = ""):
        """
        returns a one member dict with a fake label as key and a fake ROI data object representing uniform ROI covering
        the entire frame
        :param flags: view flags object
        :param measurement_label: str, optional
        :return: roi_data_dict, roi_file
        roi_data_dict: dict with roi labels as keys and ROI Data objects as values
        roi_file: str, name of the file from which ROI data was read
        """

        logging.getLogger("VIEW").info(f"Create fictive uniform ROI data")
        roi_data = UniformROIData()
        roi_data_dict = {roi_data.label: roi_data}

        return roi_data_dict, None


def get_roi_io_class(RM_ROITrace):

    if RM_ROITrace == 0:
        io_class = IDLCoorFileIO

    elif RM_ROITrace == 2:
        io_class = IDLAREAFileIO

    elif RM_ROITrace == 3:

        io_class = ILTISTextROIFileIO

    elif RM_ROITrace == 4:

        io_class = ILTISTiffROIFileIO

    elif RM_ROITrace == 5:

        io_class = ILTISAreaROIFileIO

    elif RM_ROITrace == 6:

        io_class = NonFileUniformROIIO

    else:
        raise NotImplementedError(f"RM_ROITrace={RM_ROITrace}")

    return io_class
