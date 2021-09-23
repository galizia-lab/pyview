from .aux_funcs import stack_duplicate_frames
from view.python_core.movies.data_to_01 import LinearNormalizer
from ..excluder import Excluder3D, Excluder2D
from view.python_core.foto import get_foto1_data
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.pylab import cm


class AbstractBackground(object):

    def __init__(self, data_limit_decider):

        super().__init__()
        self.data_limit_decider = data_limit_decider

    def get_data(self):
        pass

    def get_data_scaled(self):

        # background could get 2D or 3D data depending on the implementation of get_data
        background = self.get_data()
        vmin, vmax = self.data_limit_decider.get_limits(background)

        # if the pixel values in the background are all equal, then clip it to 0, 1
        if vmin == vmax:
            return np.clip(background, 0, 1)
        else:
            return LinearNormalizer(vmin, vmax).normalize(background)

    def get_colormap(self):

        return cm.gray


class BlankBackground(object):

    def __init__(self, background_size, bg_color):
        super().__init__()
        self.background_size = background_size
        self.bg_color = bg_color

    def get_data_scaled(self):

        return np.ones(self.background_size)

    def get_colormap(self):
        return LinearSegmentedColormap.from_list(name="singleton_bg",
                                                 colors=[self.bg_color, self.bg_color],
                                                 N=2)


class StaticBackground3D(AbstractBackground):

    def __init__(self, background_frame, depth, data_limit_decider):

        super().__init__(data_limit_decider)
        self.background_frame = background_frame
        self.depth = depth

    def get_data(self):

        return stack_duplicate_frames(frame=self.background_frame, depth=self.depth)


class StaticBackground2D(AbstractBackground):

    def __init__(self, background_frame, data_limit_decider):

        super().__init__(data_limit_decider)
        self.background_frame = background_frame

    def get_data(self):

        return self.background_frame


class DynamicBackground3D(AbstractBackground):

    def __init__(self, data_3D, data_limit_decider):

        super().__init__(data_limit_decider)
        self.data_3D = data_3D

    def get_data(self):

        return self.data_3D


def get_background_3D(flags, p1, excluder: Excluder3D, data_limit_decider):

    revised_movie_size = excluder.revise_movie_size((p1.metadata.format_x, p1.metadata.format_y, p1.metadata.frames))

    if flags["mv_thresholdShowImage"] == "foto1":

        foto1_data = get_foto1_data(flags, p1)
        foto1_cropped = excluder.exclude_from_frame(foto1_data)

        return StaticBackground3D(background_frame=foto1_cropped, data_limit_decider=data_limit_decider,
                                  depth=revised_movie_size[2])

    elif flags["mv_thresholdShowImage"] == "bgColor":

        return BlankBackground(background_size=revised_movie_size, bg_color=flags["mv_bgColor"])

    elif flags["mv_thresholdShowImage"] == "raw1":

        raw1_data_cropped = excluder.exclude_from_movie(p1.raw1)

        return DynamicBackground3D(data_3D=raw1_data_cropped, data_limit_decider=data_limit_decider)

    else:
        raise NotImplementedError


def get_background_2D(flags, p1, excluder: Excluder2D, data_limit_decider, bg_color):

    if flags["SO_thresholdShowImage"] == "foto1":

        foto1_data = get_foto1_data(flags, p1)
        foto1_cropped = excluder.exclude_from_frame(foto1_data)

        return StaticBackground2D(background_frame=foto1_cropped, data_limit_decider=data_limit_decider)

    elif flags["SO_thresholdShowImage"] == "bgColor":

        revised_frame_size = excluder.revise_frame_size((p1.metadata.format_x, p1.metadata.format_y))

        return BlankBackground(background_size=revised_frame_size, bg_color=bg_color)

    else:
        raise NotImplementedError




