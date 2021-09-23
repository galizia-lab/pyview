from scipy.io.idl import readsav
from .io import read_tif_2Dor3D
from scipy.ndimage.morphology import binary_erosion
import numpy as np


def get_area(flags):
    """
    Get the area mask for the flags given
    Raises
    :param flags: FlagsManager object
    :return:
    """
    mask_path = flags.get_existing_area_filepath()
    if mask_path is None:
        raise FileNotFoundError("Could not find area file")

    frame_mask = read_area_file(str(mask_path))
    return frame_mask


def frame_mask2perim(frame_mask):

    eroded_mask = binary_erosion(frame_mask)
    return frame_mask & (~eroded_mask)


def read_area_file(fle):

    if fle.endswith(".Area"):

        return AreaMaskIO.read_mask_from_file(fle)

    elif fle.endswith(".area.tif"):

        return TIFMaskIO.read_mask_from_file(fle)

    else:
        raise NotImplementedError


class BaseMaskIO(object):

    def __init__(self):

        super().__init__()

    @classmethod
    def read_mask_from_file(cls, file):

        pass

    @classmethod
    def write_mask_to_file(cls, frame_data, file):

        pass


class AreaMaskIO(BaseMaskIO):

    def __init__(self):

        super().__init__()

    @classmethod
    def read_mask_from_file(cls, file):
        """
        Read and returns a boolean mask for VIEW from `file`
        :param str file: path to an AREA file
        :return: boolean 2D mask
        :rtype: numpy.ndarray
        """
        mask_uint8_XY_y_flipped = cls.read_footprint(file)

        mask_XY_y_flipped = mask_uint8_XY_y_flipped > 0

        return mask_XY_y_flipped

    @classmethod
    def read_footprint(cls, file):
        """
        Reads the AREA file in `file` and returns a 2D ndarray of type uint8
        :param str file: path to an AREA file
        :return: uint8 2D array
        :rtype: numpy.ndarray
        """

        mask_uint8_YX = readsav(file).maskframe

        mask_uint8_XY = mask_uint8_YX.swapaxes(0, 1)

        mask_uint8_XY_y_flipped = np.flip(mask_uint8_XY, axis=1)

        return mask_uint8_XY_y_flipped


    @classmethod
    def write_mask_to_file(cls, frame_data, file):

        raise NotImplementedError


class TIFMaskIO(BaseMaskIO):

    def __init__(self):

        super().__init__()

    @classmethod
    def read_mask_from_file(cls, file):

        frame_mask_float, _ = read_tif_2Dor3D(file)

        frame_mask = (frame_mask_float > 0).any(axis=2)

        return frame_mask

    @classmethod
    def write_mask_to_file(cls, frame_data, file):

        raise NotImplementedError


def get_area_for_p1(frame_size, flags):

    try:
        area = get_area(flags)
    except FileNotFoundError as fnfe:
        area = np.ones(frame_size, dtype=bool)

    return area


def get_area_for_bleach_correction(area_mask, LE_BleachCutBorder, LE_BleachExcludeArea):

    if LE_BleachExcludeArea:
        mask_frame = area_mask
    else:
        frame_size = area_mask.shape
        mask_frame = np.zeros(frame_size, dtype=bool)
        x_to_cut = round(frame_size[0] * LE_BleachCutBorder / 100)
        y_to_cut = round(frame_size[1] * LE_BleachCutBorder / 100)
        mask_frame[x_to_cut: frame_size[0] - x_to_cut, y_to_cut: frame_size[1] - y_to_cut] = True

    return mask_frame



