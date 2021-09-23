from PIL import ImageDraw, ImageFont, Image
import numpy as np
from typing import Sequence


def add_string(image, position, font_size: int, text, fill_color_for_pil: str, font_file,
               horizontal_alignment="left", vertical_alignment="top"):
    """
    Add a string to a PIL image
    :param PIL.Image image: PIL Image
    :param sequence position: 2-membered, coordinates as required by PIL (assuming origin at top right)
    :param str text: text to be added
    :param str fill_color_for_pil: PIL color to fill text
    :param str font_file: absolute path of a font file on disk
    """
    assert horizontal_alignment in ["left", "center", "right"], "unknown setting for horizontal alignment"
    assert vertical_alignment in ["top", "center", "bottom"], "unknown setting for vertical alignment"

    image_draw_obj = ImageDraw.Draw(image)

    corrected_font_size = 8 * round(font_size / 8)

    font = ImageFont.truetype(font=font_file, size=corrected_font_size)
    text_width, text_height = font.getsize(text)

    x_pos, y_pos = position
    if horizontal_alignment == "right":
        x_pos -= text_width
    elif horizontal_alignment == "center":
        x_pos -= int(text_width / 2)

    if vertical_alignment == "bottom":
        y_pos -= text_height
    elif vertical_alignment == "center":
        y_pos -= int(text_height / 2)

    image_draw_obj.text((x_pos, y_pos), text, fill=fill_color_for_pil, font=font)

    return image


def numpy_to_pil_image(image_np: np.ndarray):
    """
    convert an image from numpy to PIL
    :param numpy.ndarray image_np: format X, Y, Color; Color format RGBA. Origin at bottom left, i.e. X=0, Y=0
    :rtype: PIL.Image
    :return: equivalent PIL Image in RGBA mode, with origin at top right
    """

    # swap axes as we have axis order XY and PIL expects YX
    frame_data_YX = image_np.swapaxes(0, 1)

    # convert to uint8
    frame_data_for_YX_uint8 = np.array(frame_data_YX * 255, dtype="uint8")

    # flip Y as origin in PIL is top left
    frame_data_for_pil = np.flip(frame_data_for_YX_uint8, axis=0)

    # import into PIL
    return Image.fromarray(frame_data_for_pil, mode="RGBA")


def pil_image_to_numpy(image_PIL):
    """
    convert an image from PIL to numpy
    :param PIL.Image image_PIL: PIL Image in RGBA mode, with origin at top right
    :rtype: numpy.ndarray
    :return: equivalent image in numpy format X, Y, Color; Color format RGBA. Origin at bottom left, i.e. X=0, Y=0
    """

    # convert frame back to numpy.ndarray, float in range [0, 1]
    frame_data = np.array(np.array(image_PIL) / 255, dtype=np.float)

    # swap the axes as PIL return YX
    frame_dataXY = frame_data.swapaxes(0, 1)

    # flip Y as origin in PIL is top left
    frame_data_Y_flipped = np.flip(frame_dataXY, axis=1)

    return frame_data_Y_flipped


def draw_lines(image_PIL: Image, point_sequence: Sequence, color_for_PIL: str):
    """
    Draw line on a PIL Image replacing underlying pixels
    :param PIL.Image image_PIL: PIL Image
    :param Sequence point_sequence: each 2-membered, format XY as expected by PIL, i.e., origin at top left
    :param str color_for_PIL: PIL color
    """

    image_draw_obj = ImageDraw.Draw(image_PIL)
    alpha = image_PIL.getchannel("A")

    image_draw_obj.line(xy=point_sequence, fill=color_for_PIL)
    image_PIL.putalpha(alpha)

    return image_PIL

