import numpy as np
from scipy import ndimage as spimage


class SpatialNoFilter(object):

    def __init__(self):

        super().__init__()

    def filter_3D(self, data):

        return data

    def filter_2D(self, data):

        return data


class SpatialFilterAbstract(SpatialNoFilter):

    def __init__(self):

        super().__init__()

    def filter_3D(self, data):
        filtered_data = np.empty_like(data)

        for index in range(data.shape[-1]):
            filtered_data[:, :, index] = self.filter_2D(data[:, :, index])

        return filtered_data


class SpatialGaussianFilter(SpatialFilterAbstract):

    def __init__(self, Signal_FilterSpaceSize):

        super().__init__()
        self.filter_space_size = Signal_FilterSpaceSize

    def filter_2D(self, data):

        return spimage.gaussian_filter(data, self.filter_space_size)


def get_spatial_processor(filter_space_flag, filter_space_size):

    if filter_space_flag and filter_space_size > 0:

        return SpatialGaussianFilter(filter_space_size)

    else:

        return SpatialNoFilter()

