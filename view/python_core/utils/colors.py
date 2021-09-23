import numpy as np
from matplotlib import pyplot as plt
from matplotlib.colors import to_rgba, is_color_like, ListedColormap

from view.idl_translation_core import IDL


def mpl_color_to_PIL(mpl_compliant_color):

    rgba = to_rgba(mpl_compliant_color)

    rgba_8_bit = [int(np.floor(255 * x)) for x in rgba]

    return f"rgb({rgba_8_bit[0]},{rgba_8_bit[1]},{rgba_8_bit[2]})"


def mpl_color_to_css(mpl_compliant_color):

    rgba = to_rgba(mpl_compliant_color)

    rgba_8_bit = [int(np.floor(255 * x)) for x in rgba]

    return f"rgba({rgba_8_bit[0]},{rgba_8_bit[1]},{rgba_8_bit[2]}, {rgba[3]})"


class ColorDecider(object):

    def __init__(self, mv_bgColor, mv_fgColor):

        super().__init__()
        if is_color_like(mv_bgColor):
            self.background_color = to_rgba(mv_bgColor)
        else:
            self.background_color = (0, 0, 0, 1)

        if is_color_like(mv_fgColor):
            self.foreground_color = to_rgba(mv_fgColor)
        else:
            self.foreground_color = (1, 1, 1, 1)

    def get_SO_MV_colortable_bg_fg(self):

        return self.get_colormap(), self.background_color, self.foreground_color

    def get_colormap(self):

        pass


class ColorDeciderMPLCMap(ColorDecider):

    def __init__(self, mpl_cmap_name, mv_bgColor, mv_fgColor):

        super().__init__(mv_bgColor, mv_fgColor)
        self.mpl_cmap_name = mpl_cmap_name

    def get_colormap(self):

        return plt.get_cmap(self.mpl_cmap_name)


class ColorDeciderIDL(ColorDecider):

    def __init__(self, IDL_Colortable, mv_bgColor, mv_fgColor):

        super().__init__(mv_bgColor, mv_fgColor)
        self.IDL_Colortable = IDL_Colortable

    def get_colormap(self):
        extended_mpl_cmap = IDL.createPalette(self.IDL_Colortable)
        extended_mpl_cmap_values = extended_mpl_cmap(np.linspace(0, 1, extended_mpl_cmap.N))

        mpl_cmap = ListedColormap(extended_mpl_cmap_values[1:-1, :])

        return mpl_cmap


def interpret_flag_SO_MV_colortable(SO_MV_colortable, bg_color=None, fg_color=None):
    """
    Interprets the colors specfied in the flags SO_MV_colortable, mv_bgColor and mv_fgColor
    :param SO_MV_colortable: int or str
    :param bg_color: a valid mpl color
    :param fg_color: a valid mpl color
    :return: colormap, bg_color, fg_color
    colormap: matplotlib.colors.ListedColorMap
    bg_color: tuple, rgba color for matplotlib
    fg_color: tuple, rgba color for matplotlib
    """

    if type(SO_MV_colortable) == str:
        color_decider = ColorDeciderMPLCMap(SO_MV_colortable, bg_color, fg_color)
    else:
        try:
            idl_SO_MV_colortable_number = int(SO_MV_colortable)
        except ValueError as ve:
            raise ValueError(f"Colortable was expected to be a string or an int or int-like. Got {SO_MV_colortable} of "
                             f"type {type(SO_MV_colortable)}")

        color_decider = ColorDeciderIDL(idl_SO_MV_colortable_number, bg_color, fg_color)
    return color_decider.get_SO_MV_colortable_bg_fg()


def get_qualitative_colors(n_colors):

    if n_colors <= 10:
        temp = np.linspace(0, 1, 10)
        return plt.cm.tab10(temp[:n_colors])
    elif n_colors <= 20:
        temp = np.linspace(0, 1, 20)
        return plt.cm.tab20(temp[:n_colors])
    else:
        return plt.cm.tab20(np.linspace(0, 1, n_colors))
