import numpy as np
import typing


class Excluder2D(object):

    def __init__(self, cutborder_x=0, cutborder_y=0):

        self.cutborder_x = cutborder_x
        self.cutborder_y = cutborder_y

    def check_if_cutborder_too_large(self, frame_size):
        if self.cutborder_x >= 0.5 * frame_size[0]:
            raise ValueError(
                f"Specified value of cutborder_x={self.cutborder_x} is too large of data of frame size {frame_size}")
        if self.cutborder_y >= 0.5 * frame_size[1]:
            raise ValueError(
                f"Specified value of cutborder_y={self.cutborder_y} is too large of data of frame size {frame_size}")

    def exclude_from_frame(self, frame_data: np.ndarray):
        """
        Returns an XY numpy array with data along X and Y excluded
        :param frame_data: numpy.ndarray, in XY format
        :return: numpy.ndarray
        """

        self.check_if_cutborder_too_large(frame_data.shape)
        return frame_data[
                       self.cutborder_x: frame_data.shape[0] - self.cutborder_x,
                       self.cutborder_y: frame_data.shape[1] - self.cutborder_y
               ]

    def revise_frame_size(self, frame_size):
        """
        Revises frame size by excluding pixels along X and Y
        :param frame_size: tuple of size 2
        :return: tuple of size 2
        """
        self.check_if_cutborder_too_large(frame_size)
        revised_frame = frame_size[0] - 2 * self.cutborder_x, frame_size[1] - 2 * self.cutborder_y
        return revised_frame

    def get_exclusion_mask_2D(self, frame_size):
        """
        returns a boolean 2D array with True for pixels that are to be retained and False for those that are to be cut
        :param frame_size: tuple of size 2
        :return: boolean numpy ndarray of shape `frame_size`
        """

        mask = np.ones(frame_size, dtype=bool)
        mask[
                self.cutborder_x: frame_size[0] - self.cutborder_x,
                self.cutborder_y: frame_size[1] - self.cutborder_y
        ] = False

        return mask


class Excluder3D(Excluder2D):

    def __init__(self, mv_FirstFrame=0, mv_LastFrame=0, cutborder_x=0, cutborder_y=0):

        super().__init__(cutborder_x=cutborder_x, cutborder_y=cutborder_y)

        # invalid first frame defaults to first frame
        self.t_slice_start = mv_FirstFrame if mv_FirstFrame >= 0 else 0
        # invalid last frame defaults to None, which will later be interpreted as the last frame of the movie
        self.t_slice_end = mv_LastFrame + 1 if mv_LastFrame > 0 else None

    def check_revise_framecut(self, movie_size):

        # default to end of movie if slice end is None
        t_slice_end = movie_size[2] if self.t_slice_end is None else self.t_slice_end

        t_slice_start = np.clip(self.t_slice_start, 0, movie_size[2])
        t_slice_end = np.clip(t_slice_end, 0, movie_size[2])

        if t_slice_start >= t_slice_end:
            raise ValueError(f"Specified values for mv_FirstFrame and mv_LastFrame are not valid for movie_data of size"
                             f"{movie_size}. Please check!")

        return t_slice_start, t_slice_end

    def exclude_from_movie(self, movie_data: np.ndarray):
        """
        Returns an XYT numpy array with data along X, Y and T axes excluded
        :param movie_data: numpy.ndarray, in XYT format
        :return: numpy.ndarray
        """

        self.check_if_cutborder_too_large(movie_data.shape[:2])
        t_slice_start, t_slice_end = self.check_revise_framecut(movie_data.shape)
        return movie_data[self.cutborder_x: movie_data.shape[0] - self.cutborder_x,
                          self.cutborder_y: movie_data.shape[1] - self.cutborder_y,
                          t_slice_start: t_slice_end]

    def revise_movie_size(self, movie_size):
        """
        Revises frame size by excluding pixels along X, Y and T
        :param movie_size: tuple of size 3
        :return: tuple of size 3
        """
        revised_frame_size = self.revise_frame_size(movie_size[:2])
        revised_frame_start_end = self.revised_frame_start_end(movie_size)
        revised_frame_count = revised_frame_start_end[1] - revised_frame_start_end[0] + 1
        return revised_frame_size[0], revised_frame_size[1], revised_frame_count

    def revised_frame_start_end(self, movie_size):
        """
        Returns the first frame and last frame retained after exclusion as a tuple
        :param movie_size: tuple of size 3
        :return: tuple of size 2
        """

        slice_start, slice_end = self.check_revise_framecut(movie_size)
        return slice_start + 1, slice_end




