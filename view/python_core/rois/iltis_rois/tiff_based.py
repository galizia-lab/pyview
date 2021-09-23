from ..base_classes import BaseROIData
from skimage.measure import find_contours
import numpy as np
import typing


class SpatialFootprintROIData(BaseROIData):
    """
    Class for storing ROI data available as spatial footprints in TIFF files
    """
    def __init__(
            self, label, spatial_footprint: np.ndarray, thresh=75, basic_text_description="A spatial footprint ROI"):
        """
        Spatial footprints are normalized to sum up to 1. When creating a boolean mask for this ROI,
        all pixels with value higher than the <thresh>th percentile will be considered to belong to the ROI.
        :param label: str, a label for the ROI
        :param spatial_footprint: numpy.ndarray, of float values
        :param thresh: float, between 0 and 100.
        """
        super().__init__(label=label, basic_text_description=basic_text_description)

        self.thresh = thresh

        self.spatial_footprint_norm = spatial_footprint / np.nansum(spatial_footprint)

        self.value_at_thresh_percentile = np.nanpercentile(self.spatial_footprint_norm, self.thresh)

    def get_text_description(self, frame_size):
        return \
            f'File: {self.roi_file}; Pixels: {self.get_boolean_mask(frame_size).sum()}; ' \
            f'Label;{self.label};{self.basic_text_description}'

    def get_perimeter_mask(self, frame_size: typing.Iterable[int] = None) -> typing.Tuple[np.ndarray, np.ndarray]:

        if frame_size is not None:
            assert frame_size == self.spatial_footprint_norm.shape, \
                f"This SpatialFootprintROI has a shape of {self.spatial_footprint_norm.shape}, while the requested " \
                f"perimeter mask shape is {frame_size}"
        else:
            frame_size = self.spatial_footprint_norm.shape

        perimeter_mask = np.zeros(frame_size, dtype=bool)

        for contour_coords in find_contours(self.spatial_footprint_norm, self.value_at_thresh_percentile):
            contour_coords_int = contour_coords.astype(int)
            perimeter_mask[contour_coords_int[:, 0], contour_coords_int[:, 1]] = True

        return perimeter_mask, self.get_boolean_mask(frame_size)

    def get_weighted_mask(self, frame_size: typing.Iterable[int] = None) -> np.ndarray:

        if frame_size is not None:
            assert frame_size == self.spatial_footprint_norm.shape, \
                f"This SpatialFootprintROI has a shape of {self.spatial_footprint_norm.shape}, while the requested " \
                f"mask shape is {frame_size}"

        return self.spatial_footprint_norm

    def get_boolean_mask(self, frame_size: typing.Iterable[int] = None) -> np.ndarray:

        if frame_size is not None:
            assert frame_size == self.spatial_footprint_norm.shape, \
                f"This SpatialFootprintROI has a shape of {self.spatial_footprint_norm.shape}, while the requested " \
                f"mask shape is {frame_size}"

        return self.spatial_footprint_norm >= self.value_at_thresh_percentile

    def get_boolean_mask_without_perimeter(self, frame_size: typing.Iterable[int] = None) -> np.ndarray:

        if frame_size is None:
            return super().get_boolean_mask_without_perimeter(frame_size=self.spatial_footprint_norm.shape)
        else:
            return super().get_boolean_mask_without_perimeter(frame_size)

