import typing
import numpy as np
from abc import ABC, abstractmethod
from view.python_core.areas import frame_mask2perim


class BaseROIData(ABC):
    """
    Abstract class to define ROI Data API
    """

    def __init__(self, label, basic_text_description="A ROI"):
        """
        Initialize label
        :param label: str
        """

        super().__init__()
        self.label = label
        self.basic_text_description = basic_text_description
        self.roi_file = None

    def get_text_description(self, frame_size):
        return self.basic_text_description

    @abstractmethod
    def get_boolean_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a boolen array with all pixels belonging to the ROI set to True and False otherwise.
        :param frame_size: two member iterable of ints. Output mask will have this shape
        :return: numpy.ndarray
        """
        pass

    def get_weighted_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a float numpy array whose pixels indicate the extent to which a pixel belongs to the
        ROI. Pixel values add up to 1.
        :param frame_size:  two member iterable of ints. Output array will have this shape
        :return: numpy.ndarray
        """

        float_mask = self.get_boolean_mask(frame_size).astype(float)
        return float_mask / np.nansum(float_mask)

    def get_weighted_mask_considering_area(self, area_mask: np.ndarray) -> np.ndarray:
        """
        Returns a numpy.ndarray similar to `get_weighted_mask`, but with values of pixels with `area_mask` is False
        set to 0. The returned ndarray adds up to 1 as well.
        :param numpy.ndarray area_mask: boolean array with shape
        :return: numpy.ndarray
        """

        weighted_mask = self.get_weighted_mask(area_mask.shape)
        weighted_mask[~area_mask] = 0
        return weighted_mask / np.nansum(weighted_mask)

    def get_perimeter_mask(self, frame_size: typing.Iterable[int]) -> typing.Tuple[np.ndarray, np.ndarray]:
        """
        Returns a boolean numpy array with pixels on the the perimeter of the ROI set to True and all else to False.
        :param frame_size: two member iterable of ints. Output mask will have this shape
        :return: numpy.ndarray
        """
        boolean_mask = self.get_boolean_mask(frame_size)
        return frame_mask2perim(boolean_mask), boolean_mask

    def get_boolean_mask_without_perimeter(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a boolean numpy array with all pixels belonging to the ROI and not on it's perimeter set to True
        and False otherwise
        :param frame_size: two member iterable of ints. Output mask will have this shape
        :return: numpy.ndarray
        """
        perimeter_mask, boolean_mask = self.get_perimeter_mask(frame_size=frame_size)

        mask_without_perimeter = np.logical_and(boolean_mask, np.logical_not(perimeter_mask))

        return mask_without_perimeter

