import numpy as np


class DataLimitsWithoutMask(object):

    def __init__(self):

        super().__init__()

    def get_limits(self, data):

        return data.min(), data.max()


class DataLimitsWithMask(DataLimitsWithoutMask):

    def __init__(self, thresholder):

        super().__init__()
        self.thresholder = thresholder

    def get_limits(self, data):

        data_masked_inside = np.ma.MaskedArray(data, mask=self.thresholder.get_mask(data))
        return data_masked_inside.min(), data_masked_inside.max()


def get_data_limit_decider(mv_thresholdScale, thresholder):

    if mv_thresholdScale == "full":

        return DataLimitsWithoutMask()

    elif mv_thresholdScale == "onlyShown":

        return DataLimitsWithMask(thresholder)

