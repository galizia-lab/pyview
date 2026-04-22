import typing

import numpy as np
from skimage.draw import rectangle

from view.python_core.rois.base_classes import BaseROIData
from view.python_core.rois.iltis_rois.text_based import BaseTextROIData


class SquareIDLROIData(BaseTextROIData):
    def __init__(
        self,
        label: str,
        center_x: int,
        center_y: int,
        half_width: int,
        basic_text_description="A square IDL ROI",
    ):
        """
        Initialize a square ROI object
        :param label: str, unique identifier for the ROI
        :param center_x: int, X coordinate of the center of the square, as written in .coor file
        :param center_y: int, Y coordinate of the center of the square, as written in .coor file
        :param half_width: int, half of the side of the square
        """
        super().__init__(label, basic_text_description)
        self.center_x = int(center_x)
        self.center_y = int(center_y)
        self.half_width = int(half_width)

    @classmethod
    def read_from_text_line(cls, text_line):
        """
        Initialize a square ROI object from a line of text. Note: Only information about the center of the square,
        i.e., <self.center_x> and <self.center_y> are set. Half width <self.half_width> is set to zero and
        needs to be manually set before the ROI object can be used.
        :param text_line: str, possibly ending with a '\n'
        :return: SquareIDLROIData object
        """
        text_line = text_line.rstrip("\n")
        text_parts = cls.split_line(text_line)
        label = text_parts[2].lstrip("\t ")
        x, y = (int(temp) for temp in text_parts[:2])
        return cls(
            label=label,
            center_x=x,
            center_y=y,
            half_width=0,
            basic_text_description=text_line,
        )

    def write_to_text_line(self) -> str:

        raise NotImplementedError  # TODO

    def get_boolean_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a boolean numpy array with pixels on the the perimeter of the polygon set to True and all else to False.
        :param frame_size: 2-member tuple of ints
        :return: numpy.ndarray
        """
        mask = np.zeros(frame_size, dtype=bool)

        # clip to within frame, in case values extend outside
        x_start, x_end = np.clip(
            [self.center_x - self.half_width, self.center_x + self.half_width],
            0,
            frame_size[0],
        )
        y_start, y_end = np.clip(
            [self.center_y - self.half_width, self.center_y + self.half_width],
            0,
            frame_size[1],
        )

        # function rectangle draws a rectangle that includes both start and end points
        rr, cc = rectangle(start=(x_start, y_start), end=(x_end, y_end))
        rr, cc = rr.astype(int), cc.astype(int)
        mask[rr, cc] = True
        return np.flip(mask, axis=1)

    def to_napari_shape_vertices_and_type(
        self, frame_size: tuple[int, int]
    ) -> typing.Tuple[list, str]:
        """
        Convert SquareIDLROIData to napari shape vertices and type.

        :param frame_size: Size of the frame (height, width)
        :return: Tuple of (shape_vertices, shape_type) where shape_vertices is a list of vertices
                 and shape_type is a string representing the napari shape type
        :raises ValueError: If any vertex coordinate is outside the image bounds
        """
        # vertices format: [y, x]
        square_bounding_vertices = [
            # SquareIDLROIData have their Y values measured from top
            [
                self.center_y - self.half_width,
                self.center_x - self.half_width,
            ],
            [
                self.center_y + self.half_width,
                self.center_x - self.half_width,
            ],
            [
                self.center_y + self.half_width,
                self.center_x + self.half_width,
            ],
            [
                self.center_y - self.half_width,
                self.center_x + self.half_width,
            ],
        ]

        # Check if any vertex is outside the image bounds
        for vertex in square_bounding_vertices:
            if (
                vertex[0] < 0
                or vertex[1] < 0
                or vertex[0] >= frame_size[0]
                or vertex[1] >= frame_size[1]
            ):
                raise ValueError(
                    f"This {__class__.__name__} object has ROIs with coordinates outside the specified frame. Please check the data."
                )

        return square_bounding_vertices, "rectangle"


class TIFFIDLROIData(BaseROIData):
    def __init__(
        self,
        label: str,
        idl_tiff_frame: np.ndarray,
        basic_text_description="AREA TIFF IDL ROI",
    ):

        super().__init__(label, basic_text_description)
        self.idl_tiff_frame = idl_tiff_frame

    def get_boolean_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a boolen array with all pixels belonging to the ROI set to True and False otherwise.
        :param frame_size: two member iterable of ints. Output mask will have this shape
        :return: numpy.ndarray
        """

        return self.idl_tiff_frame > 0
