import typing
import numpy as np
from skimage.draw import circle_perimeter, polygon
from abc import ABC, abstractmethod
from view.python_core.rois.base_classes import BaseROIData


class BaseTextROIData(BaseROIData, ABC):
    """
    Abstract class to define API for text based ROI Data
    """
    _splitter = '\t'

    def __init__(self, label: str, basic_text_description="A text based ROI"):
        super().__init__(label, basic_text_description)

    @classmethod
    @abstractmethod
    def read_from_text_line(cls, text_line):
        pass

    @abstractmethod
    def write_to_text_line(self) -> str:
        pass

    @classmethod
    def split_line(cls, text_line) -> list:
        return text_line.split(cls._splitter)

    def compose_line(self, text_line_parts) -> str:
        return self._splitter.join(text_line_parts)

    def get_text_description(self, frame_size):
        return \
            f'File: {self.roi_file}; Pixels: {self.get_boolean_mask(frame_size).sum()}; ' \
            f'Label;{self.label};{self.basic_text_description}'


class CircleILTISROIData(BaseTextROIData):

    def __init__(self, label: str, x: float, y: float, d: float, basic_text_description="A circular ILTIS ROI"):
        """
        Initialize the circle ROI data with the X and Y coordinates of the center and the diameter of the circle
        :param label: str, unique identifier for the ROI
        :param x: float, X coordinates of the center
        :param y: float, Y coordinates of the center
        :param d: float, diameter of the circle
        """
        super().__init__(label, basic_text_description)
        self.x, self.y, self.d = x, y, d

    @classmethod
    def read_from_text_line(cls, text_line):
        """
        Initialize a circle ROI object from a line of text
        :param text_line: str, possibly ending with a '\n'
        :return: CircleILTISROIData object
        """
        text_line = text_line.rstrip("\n")
        text_parts = cls.split_line(text_line)
        label = text_parts[1]
        x, y, d = (float(temp) for temp in text_parts[2:5])
        return cls(label, x, y, d, text_line)

    def write_to_text_line(self) -> str:
        """
        Returns ROI information formatted as a line of text. Output lines are tab delimited and
        always start with the keyword 'circle', followed by the X and Y coordinates of the circle, followed by the
        diameter of the circle. The line is terminated with a '\n'
        :return: str
        """
        to_write_parts = ["circle", str(self.label),
                          f"{self.x:.2f}", f"{self.y:.2f}", f"{self.d:.2f}"]
        return self.compose_line(to_write_parts) + "\n"

    def get_boolean_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a boolean numpy array of shape <unexcluded_frame_size>, with all pixels within the circle set to True,
        and all pixels outside to False
        :param frame_size: 2-member tuple of ints
        :return: numpy.ndarray
        """
        mask = np.zeros(frame_size, dtype=bool)
        rr, cc = circle_perimeter(
            r=int(self.x), c=int(self.y), radius=int(self.d / 2), shape=frame_size)
        mask[rr, cc] = True
        return mask


class PolygonILTISROIData(BaseTextROIData):

    def __init__(self, label: str, list_of_vertices: list, basic_text_description: str = 'An ILTIS polygon ROI'):
        """
        Initialize a polygon ROI object
        :param label: str, unique identifier for the ROI
        :param list_of_vertices: list of tuples, where each tuple represents a vertex, in the form of two ints,
        the X and Y coordinates of the vertex
        """
        super().__init__(label, basic_text_description)
        self.list_of_vertices = np.array(list_of_vertices, dtype=int)

    @classmethod
    def read_from_text_line(cls, text_line):
        """
        Initialize a polygon ROI object from a line of text
        :param text_line: str, possibly ending with a '\n'
        :return: PolygonILTISROIData object
        """
        text_line = text_line.rstrip("\n")
        text_parts = cls.split_line(text_line)
        label = text_parts[1]
        n_remaining_parts = len(text_parts) - 2
        n_vertices = int(np.floor(n_remaining_parts / 2))
        list_of_vertices = []
        for ind in range(n_vertices):
            x, y = round(float(text_parts[2 + 2 * ind])), round(float(text_parts[3 + 2 * ind]))
            list_of_vertices.append((x, y))

        return cls(label, list_of_vertices, text_line)

    def write_to_text_line(self) -> str:
        """
        Returns ROI information formatted as a line of text. Output lines are tab delimited and
        always start with the keyword 'polygon', followed by X1, Y1, X2, Y2, ... where (X1, Y1), (X2, Y2),.. represent
        vertices such every consecutive pair of vertices form a side of the polygon. The line is terminated with a '\n'
        :return: str
        """
        to_write_parts = ["polygon", str(self.label)]
        for vertex in self.list_of_vertices:
            to_write_parts += [f"{vertex[0]:.2f}", f"{vertex[1]:.2f}"]
        return self.compose_line(to_write_parts) + "\n"

    def get_boolean_mask(self, frame_size: typing.Iterable[int]) -> np.ndarray:
        """
        Returns a boolean numpy array of shape <unexcluded_frame_size>, with all pixels within the polygon set to True,
        and all pixels outside to False
        :param frame_size: 2-member tuple of ints
        :return: numpy.ndarray
        """
        mask = np.zeros(frame_size, dtype=bool)
        x_coors, y_coors = zip(*self.list_of_vertices)
        rr, cc = polygon(r=x_coors, c=y_coors)
        mask[rr, cc] = True
        return mask
