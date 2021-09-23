import numpy as np
import re


def apply_colormaps_based_on_mask(mask, data_for_inside_mask, data_for_outside_mask,
                                  colormap_inside_mask, colormap_outside_mask):
    """
    Returns the combination of applying two colormaps to two datasets on two mutually exclusive sets of pixels
    as follows. Applies <colormap_inside_mask> to <data_for_inside_mask> for pixels where <thresh_mask> is True and applies
    <colormap_outside_mask> to <data_for_outside_mask> for pixels where <thresh_mask> is False.
    :param mask: boolean numpy.ndarray
    :param data_for_inside_mask: float numpy.ndarray, having the same shape as thresh_mask
    :param data_for_outside_mask: float numpy.ndarray, having the same shape as thresh_mask
    :param colormap_inside_mask: matplotlib colormap
    :param colormap_outside_mask: matplotlib colormap
    :return: numpy.ndarray, having the same shape as thresh_mask
    """
    assert data_for_inside_mask.shape == data_for_outside_mask.shape, f"data_within_mask and data_outside_mask " \
                                                                      f"must have " \
                                                              f"the same shape. Given: {data_for_inside_mask.shape} " \
                                                              f"and {data_for_outside_mask.shape}"

    assert mask.shape == data_for_inside_mask.shape, f"The shape of given thresh_mask ({mask.shape}) " \
                                                        f"does not match shape of data given " \
                                                        f"({data_for_inside_mask.shape})"

    data_colorized = np.empty(list(data_for_inside_mask.shape) + [4])

    data_colorized[mask, :] = colormap_inside_mask(data_for_inside_mask[mask])
    data_colorized[~mask, :] = colormap_outside_mask(data_for_outside_mask[~mask])

    return data_colorized
    #
    # data_masked_inside = np.ma.MaskedArray(data_for_outside_mask, mask, fill_value=0)
    # data_masked_outside = np.ma.MaskedArray(data_for_inside_mask, ~mask, fill_value=0)
    #
    # data_colorized_outside = colormap_outside_mask(data_masked_inside)
    # data_colorized_inside = colormap_inside_mask(data_masked_outside)
    #
    # return data_colorized_inside + data_colorized_outside


def stack_duplicate_frames(frame, depth):
    """
    Retuns a numpy.ndarray formed by stacking <frame> along the third axis
    :param frame: numpy.ndarray, of 2 dimensions
    :param depth: int
    :return: numpy.ndarray of shape (frame.shape[0], frame.shape[1], depth)
    """

    return np.stack([frame] * depth, axis=2)


def resolve_thresholdOnValue(data, mv_thresholdOnValue):
    """
    Interprets <mv_thresholdOnValue> in the context of <data>, calculates the threshold and returns it
    :param data: numpy.ndarray
    :param mv_thresholdOnValue: str
    :return: float
    """

    assert re.fullmatch(r"[ra][\-\.0-9]+", mv_thresholdOnValue) is not None, f"{mv_thresholdOnValue} is not a valid" \
                                                                          f"threshold indicator. Valid formats are " \
                                                                          f"'rxxx' for relative threshold and 'ayyy' " \
                                                                          f" for absolute threshold where 'xxx' and" \
                                                                          f"'yyy' represent numbers. " \
                                                                          f"E.g.: a123.123, r0.4 and r-0.12533"

    threshold_value = float(mv_thresholdOnValue[1:])
    if mv_thresholdOnValue.startswith("r"):

        thres_pc = np.clip(threshold_value, 0, 100)
        data_min, data_max = data.min(), data.max()

        threshold = data_min + 0.01 * thres_pc * (data_max - data_min)

    elif mv_thresholdOnValue.startswith("a"):
        threshold = threshold_value
    else:
        # Should not come here
        raise ValueError()

    return threshold



