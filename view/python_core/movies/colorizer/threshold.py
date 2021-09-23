import numpy as np
from .aux_funcs import stack_duplicate_frames, resolve_thresholdOnValue
from view.python_core.foto import get_foto1_data


class Mask(object):

    def __init__(self, area_masker, threshold_masker):
        super().__init__()
        self.area_masker = area_masker
        self.threshold_masker = threshold_masker

    def get_mask_2D(self, data):

        return self.area_masker.get_area_mask_2D() & self.threshold_masker.get_thresh_mask_2D(data)

    def get_mask_3D(self, data):

        return self.area_masker.get_area_mask_3D() & self.threshold_masker.get_thresh_mask_3D(data)

    def get_mask(self, data):

        if len(data.shape) == 2:
            return self.get_mask_2D(data)
        elif len(data.shape) == 3:
            return self.get_mask_3D(data)


class AreaMaskBlank(object):

    def __init__(self, movie_size):

        super().__init__()
        self.movie_size = movie_size

    def get_area_mask_3D(self):

        return np.ones(self.movie_size, dtype=bool)

    def get_area_mask_2D(self):

        return np.ones(self.movie_size[:2], dtype=bool)


class AreaMask(AreaMaskBlank):

    def __init__(self, movie_size, frame_mask):

        super().__init__(movie_size)
        self.area_mask = frame_mask

    def get_area_mask_3D(self):
        return stack_duplicate_frames(self.area_mask, self.movie_size[2])

    def get_area_mask_2D(self):
        return self.area_mask


def apply_threshold(threshold_on, threshold_pos, threshold_neg):
    threshold_pos = resolve_thresholdOnValue(threshold_on, threshold_pos)
    threshold_neg = resolve_thresholdOnValue(threshold_on, threshold_neg)
    return (threshold_on > threshold_pos) | (threshold_on < threshold_neg)


class ThresholdMaskBlank(object):

    def __init__(self, data_size):

        super().__init__()
        self.data_size = data_size

    def get_thresh_mask_2D(self, data):

        return np.ones(self.data_size[:2], dtype=bool)

    def get_thresh_mask_3D(self, data):
        frame_mask = self.get_thresh_mask_2D(data)
        return stack_duplicate_frames(frame_mask, self.data_size[2])


class ThresholdMaskStatic(ThresholdMaskBlank):

    def __init__(self, threshold_on, threshold_pos, threshold_neg, data_size):

        super().__init__(data_size)
        self.thresh_mask = apply_threshold(threshold_on, threshold_pos, threshold_neg)

    def get_thresh_mask_2D(self, data):

        return self.thresh_mask


class ThresholdMaskDynamic(ThresholdMaskBlank):

    def __init__(self, threshold_on, threshold_pos, threshold_neg, data_size):

        super().__init__(data_size)
        self.thresh_mask = apply_threshold(threshold_on, threshold_pos, threshold_neg)

    def get_thresh_mask_2D(self, data):

        raise AttributeError("ThresholdMaskDynamic object cannot generate a 2D mask, it should only be used "
                             "to threshold on 3D data")

    def get_thresh_mask_3D(self, data):

        return self.thresh_mask


class ThresholdMaskRunTime(ThresholdMaskBlank):

    def __init__(self, threshold_pos, threshold_neg, data_size):

        super().__init__(data_size)
        self.threshold_pos = threshold_pos
        self.threshold_neg = threshold_neg

    def get_thresh_mask_2D(self, data):

        return apply_threshold(data, threshold_pos=self.threshold_pos, threshold_neg=self.threshold_neg)

    def get_thresh_mask_3D(self, data):

        return apply_threshold(data, threshold_pos=self.threshold_pos, threshold_neg=self.threshold_neg)


def get_thresholder_3D(flags, p1, area_mask_excluded, excluder):

    revised_movie_size = excluder.revise_movie_size((p1.metadata.format_x, p1.metadata.format_y, p1.metadata.frames))

    if flags["mv_withinArea"]:
        area_masker = AreaMask(movie_size=revised_movie_size, frame_mask=area_mask_excluded)
    else:
        area_masker = AreaMaskBlank(movie_size=revised_movie_size)

    mv_thresholdPos = flags["mv_lowerThreshPositiveResps"]
    mv_thresholdNeg = flags["mv_upperThreshNegativeResps"]

    if flags["mv_thresholdOn"] in ("none", "None", "NONE"):
        threshold_masker = ThresholdMaskBlank(data_size=revised_movie_size)
    elif flags["mv_thresholdOn"] == "foto1":
        foto1_data = get_foto1_data(flags, p1)
        threshold_masker = ThresholdMaskStatic(data_size=revised_movie_size, threshold_on=foto1_data,
                                               threshold_pos=mv_thresholdPos, threshold_neg=mv_thresholdNeg)
    elif flags["mv_thresholdOn"] == "raw1":
        threshold_masker = ThresholdMaskDynamic(data_size=revised_movie_size, threshold_on=p1.raw1,
                                                threshold_pos=mv_thresholdPos, threshold_neg=mv_thresholdNeg)

    elif flags["mv_thresholdOn"] == "sig1":
        threshold_masker = ThresholdMaskDynamic(data_size=revised_movie_size, threshold_on=p1.sig1,
                                                threshold_pos=mv_thresholdPos, threshold_neg=mv_thresholdNeg)
    else:
        raise NotImplementedError

    return Mask(area_masker=area_masker, threshold_masker=threshold_masker)


def get_thresholder_2D(flags, p1, area_mask_excluded, excluder):

    revised_movie_size = excluder.revise_frame_size((p1.metadata.format_x, p1.metadata.format_y))

    if flags["SO_withinArea"]:
        area_masker = AreaMask(movie_size=revised_movie_size, frame_mask=area_mask_excluded)
    else:
        area_masker = AreaMaskBlank(movie_size=revised_movie_size)

    so_thresholdPos = flags["SO_lowerThreshPositiveResps"]
    so_thresholdNeg = flags["SO_upperThreshNegativeResps"]

    if flags["SO_thresholdOn"] in ("none", "None", "NONE"):
        threshold_masker = ThresholdMaskBlank(data_size=revised_movie_size)
    elif flags["SO_thresholdOn"] == "foto1":
        foto1_data = get_foto1_data(flags, p1)
        threshold_masker = ThresholdMaskStatic(data_size=revised_movie_size, threshold_on=foto1_data,
                                               threshold_pos=so_thresholdPos, threshold_neg=so_thresholdNeg)
    elif flags["SO_thresholdOn"] == "overview":
        threshold_masker = ThresholdMaskRunTime(data_size=revised_movie_size, threshold_pos=so_thresholdPos,
                                                threshold_neg=so_thresholdNeg)
    else:
        raise NotImplementedError(f"The value of the flag 'SO_thresholdOn' was set to {flags['SO_thresholdOn']}"
                                  f", which is invalid. Valid values are 'foto1' and 'overview'. Look at the VIEW wiki "
                                  f"for more information")

    return Mask(area_masker=area_masker, threshold_masker=threshold_masker)




