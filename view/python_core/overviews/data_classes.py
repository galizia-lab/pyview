from __future__ import annotations

import typing
from dataclasses import dataclass

import numpy as np

if typing.TYPE_CHECKING:
    from view.python_core.overviews import OverviewColorizerAnnotator


@dataclass
class OverviewData:
    """Container class for raw overview created from sig, processed version of it and related values"""

    overview_frame: np.ndarray = None
    overview_frame_preprocessed: np.ndarray = None
    overview_frame_colorized_with_frame: np.ndarray = None
    data_limits: tuple = None
    overview_generator: OverviewColorizerAnnotator = None


@dataclass
class OverviewDataForOutput(OverviewData):
    """
    Extends OverviewData to add `overview_frame_for_output`
    """

    overview_frame_for_output: np.ndarray = None

    @classmethod
    def init_from_overview_data(cls, overview_data):

        return OverviewDataForOutput(
            overview_frame=overview_data.overview_frame,
            overview_frame_preprocessed=overview_data.overview_frame_preprocessed,
            overview_frame_colorized_with_frame=overview_data.overview_frame_colorized_with_frame,
            data_limits=overview_data.data_limits,
            overview_generator=overview_data.overview_generator,
        )


def prep_overview_for_output(
    overview_data: OverviewData,
) -> OverviewDataForOutput:
    """
    Prepare overview image for output as TIFs or as a frame of a movie and writes into self.overview_frame_for_output
    uses overview_frame_colorized_with_frame numpy.ndarray overview: float64 X,Y,Color format with origin at bottom left
    :rtype: numpy.ndarray
    :returns: uint8; Y,X, Color format with origin at top left
    """

    overview_data_for_output = OverviewDataForOutput.init_from_overview_data(
        overview_data=overview_data
    )

    overview_data_for_output.overview_frame_for_output = (
        prep_np_array_for_output(
            overview_data_for_output.overview_frame_colorized_with_frame
        )
    )

    return overview_data_for_output


def prep_np_array_for_output(np_array):
    """
    Prepare overview image for output as TIFs or as a frame of a movie

    :param np_array: np.array values, float64, X, Y, Color format with origin at bottom left
    :return: uint8; Y,X, Color format with origin at top left
    :rtype: numpy.ndarray
    """

    # need to swap axes as tiff expects YX
    frame_data_numpy_swapped = np_array.swapaxes(0, 1)

    # need to convert it to 8 bit from float
    frame_data_numpy_swapped_uint8 = np.array(
        frame_data_numpy_swapped * 255, dtype=np.uint8
    )

    # flip Y since origin in tiff is top left
    return np.flip(frame_data_numpy_swapped_uint8, axis=0)
