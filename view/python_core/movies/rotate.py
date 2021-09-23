import numpy as np
from scipy import ndimage as spimage
from view.python_core.misc import class_mixer


class BaseTransform(object):

    def __init__(self):

        super().__init__()

    def transpose(self, frame_data: np.ndarray):

        return frame_data

    def transform_frame_size(self, frame_size):

        return frame_size

    def flip_x(self, frame_data: np.ndarray):

        return frame_data

    def flip_y(self, frame_data: np.ndarray):

        return frame_data

    def transform(self, frame_data: np.ndarray):

        temp = self.transpose(frame_data)
        temp1 = self.flip_x(temp)
        temp2 = self.flip_y(temp1)

        return temp2


class Transpose(BaseTransform):

    def __init__(self):

        super().__init__()

    def transpose(self, frame_data: np.ndarray):

        return frame_data.swapaxes(0, 1)

    def transform_frame_size(self, frame_size):

        return frame_size[1], frame_size[0]


class MirrorX(BaseTransform):

    def __init__(self):

        super().__init__()

    def flip_x(self, frame_data: np.ndarray):

        return np.fliplr(frame_data)


class MirrorY(BaseTransform):

    def __init__(self):

        super().__init__()

    def flip_y(self, frame_data: np.ndarray):

        return np.flipud(frame_data)


def get_frame_rotator(rotate, reverse):

    classes2mix = []
    if rotate == 0:

        pass

    elif rotate == 1:

        classes2mix += [Transpose, MirrorX]

    elif rotate == 2:

        classes2mix += [MirrorY, MirrorX]

    elif rotate == 3:

        classes2mix += [Transpose, MirrorY]

    elif rotate == 4:

        classes2mix += [Transpose]

    elif rotate == 5:

        classes2mix += [MirrorY]

    elif rotate == 6:

        classes2mix += [Transpose, MirrorX, MirrorY]

    elif rotate == 7:

        classes2mix += [MirrorX]

    if reverse:

        if MirrorY in classes2mix:
            classes2mix.remove(MirrorY)
        else:
            classes2mix += [MirrorY]

    if not classes2mix:
        return BaseTransform()
    else:
        return class_mixer(*classes2mix)()




# def rotate_IDL(frame_data, direction):
#     """
#     reimplementation of the function ROTATE of IDL (http://www.harrisgeospatial.com/docs/ROTATE.html)
#     :param image: numpy.ndarray
#     :param value: int in [0, 7]
#     :return: numpy.ndarray
#     """
#
#     assert direction in range(8), f"Invalid value {direction} for direction"
#
#     direction_transpose_enumerate = [False, False, False, False, True, True, True, True]
#     direction_rotation_enumerate = [0, 90, 180, 270, 0, 90, 180, 270]
#
#     frame_data_output = frame_data.copy()
#     if direction_transpose_enumerate[direction]:
#
#         frame_data_output = np.swapaxes(frame_data_output, 0, 1)
#
#     frame_data_output = spimage.rotate(frame_data_output, -direction_rotation_enumerate[direction],
#                                        reshape=True)
#
#     return frame_data_output
#
#
# def get_frame_rotater(flags):
#
#     def frame_rotater(frame_data):
#
#         # apply rotation/transposition (see for interpretation of "mv_rotateImage"
#         # http://www.harrisgeospatial.com/docs/ROTATE.html)
#         rotated_frame_data = rotate_IDL(frame_data, flags["mv_rotateImage"])
#
#         # flip the frame vertically if required.
#         if flags["mv_reverseIt"]:
#             rotated_flipped_frame_data = np.fliplr(rotated_frame_data)
#         else:
#             rotated_flipped_frame_data = rotated_frame_data
#
#         return rotated_flipped_frame_data
#
#     return frame_rotater