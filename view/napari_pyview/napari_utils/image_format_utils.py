import numpy as np


def convert_view_image_to_tif_2D(image: np.ndarray) -> np.ndarray:
    """
    Convert a 2D numpy.ndarray from view internal representation to one that is compatible with tif file format.

    :param image: Image to convert, 2D np.ndarray, XY, origin at bottom left
    :return: Converted image, 2D np.ndarray, YX, origin at top left
    """

    assert image.ndim == 2, "Image must be 2D"

    # convert from format XYT to TXY
    image_YX = image.swapaxes(0, 1)

    # flip Y axis to match napari convention
    image_YX_Y_flipped = np.flip(image_YX, axis=0)

    return image_YX_Y_flipped


def convert_view_image_to_tif_3D(image: np.ndarray) -> np.ndarray:
    """
    Convert a 3D numpy.ndarray from view internal representation to one that is compatible with tif file format.

    :param image: Image to convert, 3D np.ndarray, XYT, origin at bottom left
    :return: Converted image, 3D np.ndarray, TYX, origin at top left
    """

    assert image.ndim == 3, "Image must be 3D"

    # convert from format XYT to TXY
    image_TYX = image.swapaxes(0, 2)

    # flip Y axis to match napari convention
    image_TYX_Y_flipped = np.flip(image_TYX, axis=1)

    return image_TYX_Y_flipped
