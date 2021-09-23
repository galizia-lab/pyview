from .base_classes import BaseROIData
import typing
import numpy as np


class UniformROIData(BaseROIData):

    def __init__(
            self,
            label="Non-file-uniform0",
            basic_text_description="A uniform ROI covering entire frame, not read from a file"):

        super().__init__(label=label, basic_text_description=basic_text_description)

    def get_boolean_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns an all-true boolean array of size <frame_size>
        :param frame_size: two member iterable of ints. Output mask will have this shape
        :return: numpy.ndarray
        """

        return np.ones(frame_size, dtype=bool)
