import numpy as np
from view.python_core.misc import class_mixer
from view.python_core.flags import FlagsManager


class CalculatorDefault(object):

    def __init__(self):

        super().__init__()

    def subsetter(self, data):

        return data

    def get_min(self, data):

        subsetted_data = self.subsetter(data)
        return self.min(subsetted_data)

    def get_max(self, data):

        subsetted_data = self.subsetter(data)
        return self.max(subsetted_data)

    def min(self, data):

        pass

    def max(self, data):

        pass

    def get_data_limit(self, data):

        return self.get_min(data), self.get_max(data)


class CalculatorFixedMin(CalculatorDefault):

    def __init__(self, SO_MV_scalemin, **kwargs):

        super().__init__(**kwargs)
        self.SO_MV_scalemin = SO_MV_scalemin

    def min(self, data):

        return self.SO_MV_scalemin


class CalculatorFixedMax(CalculatorDefault):

    def __init__(self, SO_MV_scalemax, **kwargs):

        super().__init__(**kwargs)
        self.SO_MV_scalemax = SO_MV_scalemax

    def max(self, data):

        return self.SO_MV_scalemax


class CalculatorNormalMax(CalculatorDefault):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def max(self, data):

        return data.max()


class CalculatorNormalMin(CalculatorDefault):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def min(self, data):
        return data.min()


class CalculatorPercentileMax(CalculatorDefault):

    def __init__(self, percentile_value_from_top, **kwargs):
        super().__init__(**kwargs)
        self.percentile_value = percentile_value_from_top

    def max(self, data):
        return np.percentile(data, 100 - self.percentile_value)


class CalculatorPercentileMin(CalculatorDefault):

    def __init__(self, percentile_value_from_bottom, **kwargs):
        super().__init__(**kwargs)
        self.percentile_value = percentile_value_from_bottom

    def min(self, data):
        return np.percentile(data, self.percentile_value)


class SquareSubsetter2D(CalculatorDefault):

    def __init__(self, fractional_margin, **kwargs):

        super().__init__(**kwargs)
        self.fractional_margin = fractional_margin

    def subsetter(self, data):

        xborder = int(data.shape[0] * self.fractional_margin)
        yborder = int(data.shape[1] * self.fractional_margin)
        return data[xborder: data.shape[0] - xborder, yborder: data.shape[1] - yborder]


class SquareSubsetter3D(CalculatorDefault):

    def __init__(self, fractional_margin, **kwargs):

        super().__init__(**kwargs)
        self.fractional_margin = fractional_margin

    def subsetter(self, data):

        xborder = int(data.shape[0] * self.fractional_margin)
        yborder = int(data.shape[1] * self.fractional_margin)
        return data[xborder: data.shape[0] - xborder, yborder: data.shape[1] - yborder, :]


class AreaSubsetter2D(CalculatorDefault):

    def __init__(self, frame_mask, **kwargs):

        super().__init__(**kwargs)
        self.frame_mask = frame_mask

    def subsetter(self, data):

        return np.ma.MaskedArray(data=data, mask=~self.frame_mask)


class AreaSubsetter3D(CalculatorDefault):

    def __init__(self, frame_mask, **kwargs):

        super().__init__(**kwargs)
        self.frame_mask = frame_mask

    def subsetter(self, data):

        mask_3D = np.stack([self.frame_mask] * data.shape[-1], axis=2)
        return np.ma.MaskedArray(data=data, mask=~mask_3D)


def get_data_limit_decider_3D(flags: FlagsManager, frame_mask):

    min_max_decider = flags["mv_individualScale"] % 10

    if flags["mv_percentileScale"] == 1:
        min_class, max_class = CalculatorPercentileMin, CalculatorPercentileMax
        min_kwargs, max_kwargs = [{"percentile_value_from_bottom": flags["mv_percentileValue"]},
                                  {"percentile_value_from_top": flags["mv_percentileValue"]}]
    else:
        min_class, max_class = CalculatorNormalMin, CalculatorNormalMax
        min_kwargs, max_kwargs = [{}, {}]

    if min_max_decider in [0, 1]:

        mixed_class = class_mixer(CalculatorFixedMin, CalculatorFixedMax)
        return mixed_class(SO_MV_scalemin=flags["SO_MV_scalemin"], SO_MV_scalemax=flags["SO_MV_scalemax"])

    elif min_max_decider == 2:

        mixed_class = class_mixer(min_class, max_class)
        return mixed_class(**min_kwargs, **max_kwargs)

    elif min_max_decider == 3:

        mixed_class = class_mixer(SquareSubsetter3D, min_class, max_class)
        return mixed_class(fractional_margin=flags["mv_indiScale3factor"], **min_kwargs, **max_kwargs)

    elif min_max_decider == 4:

        mixed_class = class_mixer(CalculatorFixedMin, max_class)
        return mixed_class(SO_MV_scalemin=flags["SO_MV_scalemin"], **max_kwargs)

    elif min_max_decider == 5:

        mixed_class = class_mixer(AreaSubsetter3D, min_class, max_class)
        return mixed_class(frame_mask=frame_mask, **min_kwargs, **max_kwargs)

    elif min_max_decider == 6:

        mixed_class = class_mixer(AreaSubsetter3D, CalculatorFixedMin, max_class)
        return mixed_class(frame_mask=frame_mask, SO_MV_scalemin=flags["SO_MV_scalemin"], **max_kwargs)

    else:
        raise NotImplementedError


def get_data_limit_decider_2D(flags: FlagsManager, frame_mask):

    min_max_decider = flags["SO_individualScale"] % 10

    if flags["SO_percentileScale"] == 1:
        min_class, max_class = CalculatorPercentileMin, CalculatorPercentileMax
        min_kwargs, max_kwargs = [{"percentile_value_from_bottom": flags["SO_percentileValue"]},
                                  {"percentile_value_from_top": flags["SO_percentileValue"]}]
    else:
        min_class, max_class = CalculatorNormalMin, CalculatorNormalMax
        min_kwargs, max_kwargs = [{}, {}]

    if min_max_decider in [0, 1]:

        mixed_class = class_mixer(CalculatorFixedMin, CalculatorFixedMax)
        return mixed_class(SO_MV_scalemin=flags["SO_MV_scalemin"], SO_MV_scalemax=flags["SO_MV_scalemax"])

    elif min_max_decider == 2:

        mixed_class = class_mixer(min_class, max_class)
        return mixed_class(**min_kwargs, **max_kwargs)

    elif min_max_decider == 3:

        mixed_class = class_mixer(SquareSubsetter2D, min_class, max_class)
        return mixed_class(fractional_margin=flags["SO_indiScale3factor"], **min_kwargs, **max_kwargs)

    elif min_max_decider == 4:

        mixed_class = class_mixer(CalculatorFixedMin, max_class)
        return mixed_class(SO_MV_scalemin=flags["SO_MV_scalemin"], **max_kwargs)

    elif min_max_decider == 5:

        mixed_class = class_mixer(AreaSubsetter2D, min_class, max_class)
        return mixed_class(frame_mask=frame_mask, **min_kwargs, **max_kwargs)

    elif min_max_decider == 6:

        mixed_class = class_mixer(AreaSubsetter2D, CalculatorFixedMin, max_class)
        return mixed_class(frame_mask=frame_mask, SO_MV_scalemin=flags["SO_MV_scalemin"], **max_kwargs)

    else:
        raise NotImplementedError
