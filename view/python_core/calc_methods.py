import numpy as np
from ..idl_translation_core.ViewCalcData import calc_deltaF


def calc_method_0(raw_data: list, background_frames: list, area_mask: np.ndarray):
    """
    Calculate signal from raw data as: sig1 = raw1 / 1000
    :param list raw_data: list of numpy.ndarrays, raw data in format XYT
    :param list background_frames: list of two integers indicating the start and end frames of background
    :param numpy.ndarray area_mask: boolean numpy ndarray in format XY, with 0 indicating pixels
    outside the tissue of interest
    :return: numpy.ndarray in format XYT, the same size as any member of <raw_data>
    :rtype: numpy.ndarray
    """
    error = "Calc Method 0 could not handle the raw data provided. It expects a list of " \
            "at least one numpy ndarray, the first of which will be used"
    assert isinstance(raw_data, list) and len(raw_data) >= 1, error
    assert isinstance(raw_data[0], np.ndarray), error

    return raw_data[0].astype(float) / 1000


def calc_method_1(raw_data: list, background_frames: list, area_mask: np.ndarray):
    """
    Calculate signal from raw data as: sig1 = raw2 / 1000
    :param list raw_data: list of numpy.ndarrays, raw data in format XYT
    :param list background_frames: list of two integers indicating the start and end frames of background
    :param numpy.ndarray area_mask: boolean numpy ndarray in format XY, with 0 indicating pixels
    outside the tissue of interest
    :return: numpy.ndarray in format XYT, the same size as any member of <raw_data>
    :rtype: numpy.ndarray
    """
    error = "Calc Method 1 could not handle the raw data provided. It expects a list of " \
            "at least one numpy ndarray, the second of which will be used"
    assert isinstance(raw_data, list) and len(raw_data) >= 1, error
    assert isinstance(raw_data[0], np.ndarray), error

    return raw_data[1].astype(float) / 1000


def calc_method_3(raw_data: list, background_frames: list, area_mask: np.ndarray):
    """
    Calculate signal from raw data as: sig1 = deltaF/F0; F0=average intensity during <background_frames>
    :param list raw_data: list of numpy.ndarrays, raw data in format XYT
    :param list background_frames: list of two integers indicating the start and end frames of background
    :param numpy.ndarray area_mask: boolean numpy ndarray in format XY, with 0 indicating pixels
    outside the tissue of interest
    :return: numpy.ndarray in format XYT, the same size as any member of <raw_data>
    :rtype: numpy.ndarray
    """
    error = "Calc Method 3 could not handle the raw data provided. It expects a list of " \
            "at least one numpy ndarray, the first of which will be used"

    assert isinstance(raw_data, list) and len(raw_data) >= 1, error
    assert isinstance(raw_data[0], np.ndarray), error

    return calc_deltaF(raw_data[0], background_frames)


def calc_method_4(raw_data: list, background_frames: list, area_mask: np.ndarray):
    """
    Calculate signal from raw data as: sig1 = raw1/raw2 - (raw1/raw2 averaged over <background_frames>)
    :param list raw_data: list of numpy.ndarrays, raw data in format XYT
    :param list background_frames: list of two integers indicating the start and end frames of background
    :param numpy.ndarray area_mask: boolean numpy ndarray in format XY, with 0 indicating pixels
    outside the tissue of interest
    :return: numpy.ndarray in format XYT, the same size as any member of <raw_data>
    :rtype: numpy.ndarray
    """
    error = "Calc Method 4 could not handle the raw data provided. It expects a list of " \
            "at least two numpy ndarrays, the first two of which will be used"

    assert isinstance(raw_data, list) and len(raw_data) >= 2, error
    assert isinstance(raw_data[0], np.ndarray), error
    assert isinstance(raw_data[1], np.ndarray), error

    bg_start, bg_end = background_frames
    raw1, raw2 = raw_data[:2]

    # normalizing by average background pixel intensity to nullify the effects of exposure time differences
    # on ratio calculation
    raw1_background_average = raw1[area_mask, bg_start: bg_end + 1].mean()
    raw2_background_average = raw2[area_mask, bg_start: bg_end + 1].mean()

    normalized_raw1 = raw1 / raw1_background_average
    normalized_raw2 = raw2 / raw2_background_average

    ratio = normalized_raw1 / normalized_raw2

    background_ratio = ratio[:, :, bg_start: bg_end + 1].mean(axis=2)

    # convert from XYT to format TXY as it is easy to subtract background frame from ratio
    ratio_txy = np.moveaxis(ratio, source=-1, destination=0)

    relative_ratio_txy = ratio_txy - background_ratio

    # convert back to XYT
    relative_ratio_xyt = np.moveaxis(relative_ratio_txy, source=0, destination=-1)

    return relative_ratio_xyt


def get_calc_method(flags):

    calc_method = flags["LE_CalcMethod"]

    if calc_method == 0:
        return calc_method_0
    if calc_method == 1:
        return calc_method_1
    elif calc_method == 3 or 3000 <= calc_method < 4000:
        return calc_method_3
    elif calc_method == 4 or 4000 <= calc_method < 5000:
        return calc_method_4
    else:
        raise NotImplementedError


