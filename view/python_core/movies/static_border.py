from view.python_core.utils.pil_helpers import numpy_to_pil_image, pil_image_to_numpy
from view.python_core.utils.pil_helpers import add_string
import numpy as np
from view.python_core.utils.colors import mpl_color_to_PIL
from PIL.ImageDraw import Draw
from view.python_core.utils.fonts import resolve_font_size, resolve_font_file


class StaticBorder(object):

    def __init__(self, mv_xgap_left, mv_xgap_right, mv_ygap, bg_color_for_mpl, frame_size):

        self.frame_size = frame_size
        self.mv_xgap_left = mv_xgap_left
        self.mv_xgap_right = mv_xgap_right
        self.mv_ygap = mv_ygap
        self.bg_color_for_mpl = bg_color_for_mpl

        # make sure the frame sizes along x and y after padding is even
        possible_frame_Xsize = self.frame_size[0] + mv_xgap_left + mv_xgap_right
        frame_Xsize = possible_frame_Xsize + possible_frame_Xsize % 2
        possible_frame_Ysize = self.frame_size[1] + 2 * self.mv_ygap
        frame_Ysize = possible_frame_Ysize + possible_frame_Ysize % 2

        buffer_shape = list(self.frame_size) + [len(bg_color_for_mpl)]
        buffer_shape[0] = frame_Xsize
        buffer_shape[1] = frame_Ysize

        self.frame_with_blank_border = np.full(buffer_shape, self.bg_color_for_mpl)
        self.frame_with_annotations = None

    def get_static_frame(self, data_to_01_mapper):

        return self.frame_with_blank_border

    def composite(self, frame_data, static_frame):

        data_shape = frame_data.shape[:2]
        assert data_shape == self.frame_size, f"Frame data of shape {self.frame_size} expected, " \
                                              f"got {data_shape}"

        new_frame = static_frame.astype(dtype=frame_data.dtype, copy=True)

        new_frame[self.mv_xgap_left: self.mv_xgap_left + data_shape[0],
        self.mv_ygap: self.mv_ygap + data_shape[1]] = frame_data

        return new_frame


class StaticBorderWithColorbar(StaticBorder):

    def __init__(self, mv_xgap_left, mv_xgap_right, mv_ygap, bg_color_for_mpl, frame_size, colormap,
                 fg_color_for_mpl, font_file, font_size, legend_scale_factor):

        super().__init__(mv_xgap_left, mv_xgap_right, mv_ygap, bg_color_for_mpl, frame_size)
        self.fg_color_for_pil = mpl_color_to_PIL(fg_color_for_mpl)

        self.font_file = font_file

        self.colormap = colormap

        self.font_size = resolve_font_size(text="-0.000", maximum_width=mv_xgap_right,
                                           font_name=font_file, suggested_font_size=font_size)

        self.legend_scale_factor = legend_scale_factor

        current_frame_size = self.frame_with_blank_border.shape
        self.colorbar_x_end = current_frame_size[0] - int(0.35 * mv_xgap_right)
        self.colorbar_x_start = current_frame_size[0] - int(0.65 * mv_xgap_right)

        # these are for when origin in bottom left and positive Y axis is upwards
        self.colorbar_y_start = int(max(mv_ygap, 1 * self.font_size))
        self.colorbar_y_end = int(min(frame_size[1] + mv_ygap, current_frame_size[1] - 1 * self.font_size))

    def get_static_frame(self, data_to_01_mapper):

        vmin, vmax = data_to_01_mapper.get_data_limits()

        # draw scalebar
        data_for_colorbar = np.linspace(vmin, vmax, self.colorbar_y_end - self.colorbar_y_start + 1)
        data_for_colorbar_scaled = data_to_01_mapper.normalize(data_for_colorbar)
        self.frame_with_blank_border[self.colorbar_x_start: self.colorbar_x_end + 1,
        self.colorbar_y_start: self.colorbar_y_end + 1] \
            = self.colormap(data_for_colorbar_scaled)

        pil_image = numpy_to_pil_image(self.frame_with_blank_border)

        upper_lower_text_x = 0.8 * self.colorbar_x_start + 0.2 * self.colorbar_x_end

        # add string for upper limit
        upper_limit_to_print = vmax * self.legend_scale_factor
        upper_limit_to_print_str = f"{upper_limit_to_print: 1.2f}"
        pil_image = add_string(pil_image,
                               # in PIL, origin in at top left and positive Y is downwards
                               # needs to convert coordinates, plus half a font size margin
                               position=(upper_lower_text_x,
                                         pil_image.height - (self.colorbar_y_end + 0.25 * self.font_size)),
                               font_size=self.font_size, text=upper_limit_to_print_str,
                               horizontal_alignment="center", vertical_alignment="bottom",
                               fill_color_for_pil=self.fg_color_for_pil, font_file=self.font_file)

        # add string for lower limit
        lower_limit_to_print = vmin * self.legend_scale_factor
        lower_limit_to_print_str = f"{lower_limit_to_print: 1.2f}"
        pil_image = add_string(pil_image,
                               position=(upper_lower_text_x,
                                         pil_image.height - (self.colorbar_y_start - 0.25 * self.font_size)),
                               font_size=self.font_size,
                               text=lower_limit_to_print_str, horizontal_alignment="center", vertical_alignment="top",
                               fill_color_for_pil=self.fg_color_for_pil, font_file=self.font_file)

        # if required, add a line on colormap and '0' string
        if vmin <= 0 <= vmax:

            # calculate the position of 0 according to the normalization in <data_to_01_mapper>
            colorbar_y_range = self.colorbar_y_end - self.colorbar_y_start
            # normalize function only works with arrays, hence passing one element array and indexing the result
            # also, normalized vmin=0, normalized vmax=1
            normalized_0 = data_to_01_mapper.normalize(np.array([0]))[0]
            zero_y = self.colorbar_y_start + (normalized_0 - 0) / 1 * colorbar_y_range

            pil_image = add_string(pil_image, position=(1.025 * self.colorbar_x_end, pil_image.height - zero_y),
                                   font_size=self.font_size,
                                   text="0", horizontal_alignment="left", vertical_alignment="center",
                                   fill_color_for_pil=self.fg_color_for_pil, font_file=self.font_file)

            img_draw_obj = Draw(pil_image)

            img_draw_obj.line(xy=((self.colorbar_x_start, pil_image.height - zero_y),
                                  (self.colorbar_x_end, pil_image.height - zero_y)),
                              fill="rgb(0, 0, 0)", width=int(np.ceil(colorbar_y_range / 128)))

        return pil_image_to_numpy(pil_image)


def check_frame_height(frame_height, SO_cutborder):
    """
    raises a Value error if <frame_height> is not large enough to draw a colorbar
    """

    original_frame_height = frame_height + 2 * SO_cutborder

    if frame_height < 30:

        if SO_cutborder == 0:
            raise ValueError(
                f"Current frame height ({original_frame_height}) is too small to draw a scalebar."
                f"Please set the flag 'CTV_scalebar' to False and try again!"
            )
        else:
            raise ValueError(
                f"The current value of cutborder ({SO_cutborder}) removes too much of "
                f"the frame height ({2 * SO_cutborder} out of {original_frame_height}) to be able to "
                f"add a colorbar to it. Please consider reducing the value of "
                f"cutborder to {SO_cutborder - (30 - frame_height)} pixels, below which adding a "
                f"colorbar becomes possible")


def get_static_border_adder_3D(flags, fg_color_for_mpl, bg_color_for_mpl, colormap,
                               frame_size, font_file, font_size):
    mv_xgap = flags["mv_xgap"]
    mv_ygap = flags["mv_ygap"]

    if flags["CTV_scalebar"]:

        check_frame_height(frame_height=frame_size[1], SO_cutborder=flags["mv_cutborder"])

        mv_xgap_right = 2 * mv_xgap
        static_border_adder = StaticBorderWithColorbar(
            mv_xgap_left=mv_xgap, mv_xgap_right=mv_xgap_right,
            mv_ygap=mv_ygap, bg_color_for_mpl=bg_color_for_mpl,
            fg_color_for_mpl=fg_color_for_mpl, colormap=colormap,
            frame_size=frame_size, font_file=font_file,
            font_size=font_size, legend_scale_factor=flags["SO_scaleLegendFactor"])
        return static_border_adder, mv_xgap_right
    else:
        mv_xgap_right = mv_xgap
        static_border_adder = StaticBorder(
            mv_xgap_left=mv_xgap, mv_xgap_right=mv_xgap_right, mv_ygap=mv_ygap,
            bg_color_for_mpl=bg_color_for_mpl, frame_size=frame_size)
        return static_border_adder, mv_xgap_right


def get_static_border_adder_2D(flags, fg_color_for_mpl, bg_color_for_mpl, colormap,
                               frame_size):

    if flags["CTV_scalebar"] and (flags["SO_xgap"] > 0) and (np.floor(flags["SO_showROIs"] / 10) != 2):

        check_frame_height(frame_height=frame_size[1], SO_cutborder=flags["SO_cutborder"])

        font_file = resolve_font_file(flags["SO_fontName"])

        mv_xgap_right = 2 * flags["SO_xgap"]

        # <font_size> passed here is the maximum allowed font size, passing infinity to disable ceiling
        static_border_adder = StaticBorderWithColorbar(
            mv_xgap_left=0, mv_xgap_right=mv_xgap_right,
            mv_ygap=0, bg_color_for_mpl=bg_color_for_mpl,
            fg_color_for_mpl=fg_color_for_mpl, colormap=colormap,
            frame_size=frame_size, font_file=font_file,
            font_size=np.inf,
            legend_scale_factor=flags["SO_scaleLegendFactor"])
        return static_border_adder
    else:
        static_border_adder = StaticBorder(
            mv_xgap_left=0, mv_xgap_right=0, mv_ygap=0,
            bg_color_for_mpl=bg_color_for_mpl, frame_size=frame_size)
        return static_border_adder










