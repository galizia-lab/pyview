from scipy import ndimage as spimage


class TemporalNoFilter(object):

    def __init__(self):

        super().__init__()

    def filter(self, data):

        return data


class TemporalGaussianFilter(TemporalNoFilter):

    def __init__(self, Signal_FilterTimeSize):

        super().__init__()
        self.Signal_FilterSpaceSize = Signal_FilterTimeSize

    def filter(self, data):

        return spimage.gaussian_filter1d(data, sigma=self.Signal_FilterSpaceSize, axis=-1)


def get_temporal_processor(filter_time_flag, filter_time_size):

    if filter_time_flag and filter_time_size > 0:

        return TemporalGaussianFilter(filter_time_size)

    else:

        return TemporalNoFilter()

