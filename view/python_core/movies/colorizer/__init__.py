from view.python_core.flags import FlagsManager
from view.python_core.movies.colorizer.aux_funcs import (
    apply_colormaps_based_on_mask,
)
from view.python_core.movies.colorizer.background import (
    get_background_2D,
    get_background_3D,
)
from view.python_core.movies.colorizer.data_limits import (
    get_data_limit_decider,
)
from view.python_core.movies.colorizer.threshold import (
    get_thresholder_2D,
    get_thresholder_3D,
)
from view.python_core.movies.excluder import Excluder2D, Excluder3D


class ColorizerWithoutThresholding:
    def __init__(self, colormap):
        super().__init__()
        self.colormap = colormap

    def colorize(self, data, data_to_01_mapper):
        scaled_data = data_to_01_mapper.normalize(data=data)
        return self.colormap(scaled_data)


class ColorizerWithThresholding(ColorizerWithoutThresholding):
    def __init__(self, background, thresholder, colormap_inside):
        super().__init__(colormap_inside)
        self.thresholder = thresholder
        self.background_data = background.get_data_scaled()
        self.colormap_outside = background.get_colormap()

    def colorize(self, data, data_to_01_mapper):
        scaled_data = data_to_01_mapper.normalize(data=data)
        return apply_colormaps_based_on_mask(
            mask=self.thresholder.get_mask(data),
            data_for_inside_mask=scaled_data,
            data_for_outside_mask=self.background_data,
            colormap_inside_mask=self.colormap,
            colormap_outside_mask=self.colormap_outside,
        )


def get_colorizer_3D(
    flags: FlagsManager,
    p1,
    colormap,
    excluder: Excluder3D,
    area_mask_2D_excluded,
):

    thresholder = get_thresholder_3D(
        flags=flags,
        p1=p1,
        area_mask_excluded=area_mask_2D_excluded,
        excluder=excluder,
    )

    data_limit_decider = get_data_limit_decider(
        mv_thresholdScale=flags["mv_thresholdScale"], thresholder=thresholder
    )
    background_obj = get_background_3D(
        flags=flags,
        p1=p1,
        excluder=excluder,
        data_limit_decider=data_limit_decider,
    )

    return ColorizerWithThresholding(
        background=background_obj,
        thresholder=thresholder,
        colormap_inside=colormap,
    )


def get_colorizer_2D(
    flags: FlagsManager,
    p1,
    colormap,
    bg_color,
    excluder: Excluder2D,
    area_mask_2D_excluded,
):

    thresholder = get_thresholder_2D(
        flags=flags,
        p1=p1,
        area_mask_excluded=area_mask_2D_excluded,
        excluder=excluder,
    )

    data_limit_decider = get_data_limit_decider(
        mv_thresholdScale=flags["SO_thresholdScale"], thresholder=thresholder
    )

    background_obj = get_background_2D(
        flags=flags,
        p1=p1,
        excluder=excluder,
        data_limit_decider=data_limit_decider,
        bg_color=bg_color,
    )

    return ColorizerWithThresholding(
        background=background_obj,
        thresholder=thresholder,
        colormap_inside=colormap,
    )
