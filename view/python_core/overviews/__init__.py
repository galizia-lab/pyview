import math
import pathlib as pl
from view.python_core.utils.colors import interpret_flag_SO_MV_colortable
from view.python_core.utils.deduplicator import dedupilicate
from ..areas import get_area_for_p1
from ..flags import FlagsManager
from ..p1_class import Default_P1_Getter
from .ctv_handlers import get_ctv_handler
from .roi_marker import get_roi_marker_2D
from ..movies.excluder import Excluder2D
from ..movies.spatial import get_spatial_processor
from ..movies.data_limit import get_data_limit_decider_2D
from ..movies.colorizer import get_colorizer_2D
from ..movies.rotate import get_frame_rotator
from ..movies.static_border import get_static_border_adder_2D
from ..movies.data_to_01 import get_normalizer
from ..movies.colorizer.aux_funcs import stack_duplicate_frames
import numpy as np
from matplotlib import pyplot as plt
import logging


class OverviewColorizerAnnotator(object):

    def __init__(self, flags, p1):

        frame_size = (p1.metadata.format_x, p1.metadata.format_y)

        self.colormap, self.bg_color_mpl_compliant, self.fg_color_mpl_compliant = \
            interpret_flag_SO_MV_colortable(SO_MV_colortable=flags["SO_MV_colortable"],
                                      fg_color=flags["SO_fgColor"],
                                      bg_color=flags["SO_bgColor"])

        # initialize excluder
        self.excluder = Excluder2D(cutborder_x=flags["SO_cutborder"], cutborder_y=flags["SO_cutborder"])

        # initialize area mask
        area_mask_2D = self.excluder.exclude_from_frame(p1.area_mask)

        # initialize object for handling preprocessing
        self.spatial_processor = get_spatial_processor(filter_space_flag=flags["Signal_FilterSpaceFlag"],
                                                       filter_space_size=flags["Signal_FilterSpaceSize"])

        # initialize object for deciding data limit
        self.data_limit_decider = get_data_limit_decider_2D(flags=flags, frame_mask=area_mask_2D)
        
        # initialize scaler class
        self.individual_scale = flags["SO_individualScale"]

        # initialize colorizer
        self.colorizer = get_colorizer_2D(flags=flags, p1=p1, colormap=self.colormap,
                                          bg_color=self.bg_color_mpl_compliant, excluder=self.excluder,
                                          area_mask_2D_excluded=area_mask_2D)

        revised_frame_size = self.excluder.revise_frame_size(frame_size)

        # intialize ROI marker
        self.roi_marker = get_roi_marker_2D(
            flags=flags, measurement_label=p1.metadata.ex_name,
            fg_color=self.fg_color_mpl_compliant, bg_color=self.bg_color_mpl_compliant,
            unexcluded_frame_size=frame_size, excluder=self.excluder)

        # initialize object for rotations
        self.frame_rotater = get_frame_rotator(rotate=flags["SO_rotateImage"],
                                               reverse=flags["SO_reverseIt"])

        modified_frame_size = self.frame_rotater.transform_frame_size(revised_frame_size)

        # initialize object for adding colorbar
        self.colorbar_adder = get_static_border_adder_2D(flags=flags,
                                                         bg_color_for_mpl=self.bg_color_mpl_compliant,
                                                         fg_color_for_mpl=self.fg_color_mpl_compliant,
                                                         frame_size=modified_frame_size,
                                                         colormap=self.colormap,
                                                         )

    def preprocess(self, data: np.ndarray):

        space_filtered_data = self.spatial_processor.filter_2D(data)

        data_cropped = self.excluder.exclude_from_frame(space_filtered_data)

        return data_cropped

    def get_normalizer(self, data: np.ndarray):
        vmin, vmax = self.data_limit_decider.get_data_limit(data)
        return get_normalizer(vmin=vmin, vmax=vmax, mv_individualScale=self.individual_scale)

    def colorize(self, data: np.ndarray, data_to_01_mapper):
        return self.colorizer.colorize(data=data, data_to_01_mapper=data_to_01_mapper)

    def rotate_frame(self, frame_data):
        return self.frame_rotater.transform(frame_data)

    def add_colorbar(self, frame_data, static_frame):
        return self.colorbar_adder.composite(frame_data=frame_data, static_frame=static_frame)

    def add_rois(self, frame_data):
        return self.roi_marker.draw(frame_data)


def generate_overview_frame(flags, p1, feature_number=None):
    """
    Generate overview frames
    :param flags: view.python_core.FlagsManager object
    :param p1: pandas.Series
    :param str|None|list feature_number: one of the following:
    'all': all features of the CTV specified by the flags, generating as many subplots
    None: use the feature number in the flag "CTV_FeatureNumber"
    list: containing a list of feature numbers to use (features are numbered 0, 1, 2...)
    :return: overview_frames, list of 2D numpy.ndarray, the overview image for features in XY format with origin at bottom left
    """

    ctv_handler = get_ctv_handler(flags=flags, p1=p1)

    overview_frames = ctv_handler.apply(p1.sig1)
    n_features = overview_frames.shape[0]

    if feature_number is None:
        feature_number = [flags["CTV_FeatureNumber"]]
    elif feature_number == "all":
        feature_number = slice(None)
    else:
        assert type(feature_number) is list and all(type(x) is int for x in feature_number), \
            f"feature_number can be either None, 'all' or a list of ints. Got {feature_number}"

    try:
        return overview_frames[feature_number, :, :]
    except IndexError as ie:
        raise IndexError(
            f"The specified CTV has {n_features} features, so feature_number can be in [0, {n_features - 1}]. "
            f"Some values of feature_number fall out of this range: {feature_number}")


def generate_overview_image(flags, p1):
    """
    Generate overview image
    :param flags: view.python_core.FlagsManager object
    :param p1: pandas.Series
    :returns: image, data_limits
    image: numpy.ndarray, of dimension 3, format X x Y x Color
    data_limits: 2-member tuple, indicating frame values mapping to lower and upper end of colormap
    """

    overview_frames = generate_overview_frame(flags, p1)
    overview_frame = overview_frames[0, :, :]

    return colorize_overview_add_border_etc(overview_frame=overview_frame, flags=flags, p1=p1)


def colorize_overview_add_border_etc(overview_frame, flags, p1=None):
    """
    Colorizes <overview_frame>, applies borders and border annotations according to <flags>. If <overview_frame> was
    generated from a p1 object, pass it to <p1>, else let it default to None. A p1 object is only required when <flags>
    specify that foto1 or stimuli information is to be used when colorizing or applying border annotations
    to <overview_frame>.
    :param overview_frame: numpy.ndarray, of dimension 2, format X x Y. input overview frame
    :param flags: FlagsManager object, containing flags, most importantly "SO..." flags
    :param p1: None or a p1 object with stimulus data.
    :rtype: tuple
    :returns: image, data_limits, overview_generator used
    image: numpy.ndarray, of dimension 3, format X x Y x Color
    data_limits: 2-member tuple, indicating frame values mapping to lower and upper end of colormap
    """

    if p1 is None:
        fake_raw1 = stack_duplicate_frames(overview_frame, 1)
        p1 = Default_P1_Getter().get_fake_p1_from_raw(raw1=fake_raw1)
        p1.metadata.format_x, p1.metadata.format_y = overview_frame.shape
        logging.getLogger("VIEW").warning(
            "Since original p1 object has not been specified, data in overview_frame will be used as foto1")
        p1.foto1 = overview_frame
        p1.area_mask = get_area_for_p1(frame_size=overview_frame.shape, flags=flags)

    overview_generator = OverviewColorizerAnnotator(flags=flags, p1=p1)

    # apply spatial filter and cut
    overview_frame_preprocessed = overview_generator.preprocess(overview_frame)

    # get data_to_01_mapper
    data_to_01_mapper = overview_generator.get_normalizer(overview_frame_preprocessed)

    # get static frame
    try:
        static_frame = overview_generator.colorbar_adder.get_static_frame(data_to_01_mapper)
    except ValueError as ve:
        if str(ve).startswith('Number of samples,'):
            raise ValueError("")
        else:
            raise ve

    # colorize the data
    overview_frame_colorized = overview_generator.colorize(data=overview_frame_preprocessed,
                                                           data_to_01_mapper=data_to_01_mapper)

    # draw ROIs
    overview_frame_with_rois = overview_generator.add_rois(frame_data=overview_frame_colorized)

    # apply rotations
    overview_frame_rotated = overview_generator.rotate_frame(overview_frame_with_rois)

    # add colorbar
    overview_frame_final = overview_generator.add_colorbar(overview_frame_rotated, static_frame)

    logging.getLogger("VIEW").info(
        f"SO_individualScale set to:{flags['SO_individualScale']}. "
        f"Minimum and maximum are: {data_to_01_mapper.get_data_limits()}")

    return overview_frame_final, data_to_01_mapper.get_data_limits(), overview_generator


def generate_overview_image_for_output(flags, p1):
    """
    Generates overview frame and transforms it so that it can be readily used either for plt.imshow or for
    saving with tifffile.imsave
    :param flags: FlagsManager object
    :param p1: p1 object
    :return: overview_frame, data_limits
    overview_frame: image as a 3D uint8 numpy.ndarray of format Y, X, Color with origin at top right
    data_limits: tuple, the lower and upper limits of data in overview image
    """

    # data is in X, Y, color format
    overview_frame, data_limits, overview_generator_used = generate_overview_image(flags, p1)

    # conversion to YX format, uint8 and flip Y
    return prep_overview_for_output(overview=overview_frame), data_limits


def prep_overview_for_output(overview):
    """
    Prepare overview image for output as TIFs or as a frame of a movie
    :param numpy.ndarray overview: float64 X,Y,Color format with origin at bottom left
    :rtype: numpy.ndarray
    :returns: uint8; Y,X, Color format with origin at top left
    """

    # need to swap axes as tiff expects YX
    frame_data_numpy_swapped = overview.swapaxes(0, 1)

    # need to convert it to 8 bit from float
    frame_data_numpy_swapped_uint8 = np.array(frame_data_numpy_swapped * 255, dtype=np.uint8)

    # flip Y since origin in tiff is top left
    return np.flip(frame_data_numpy_swapped_uint8, axis=0)


def get_current_pyplot_window_titles():
    """
    Returns the titles of all open pyplot windows as a list
    :return: list
    """

    titles = []

    for figure_number in plt.get_fignums():
        fig = plt.figure(figure_number)
        titles.append(fig.canvas.get_window_title())

    return titles


def pop_show_overview(flags, p1, label, stimulus_number=None, feature_number=None):
    """
    Creates a new figure and plots overview frames in it. Subplots in tabular arrangement, with
    as many rows as features selected acc. to <feature_number> and as many columns as stimuli selected
    acc. to <stimulus_number>
    :param flags: FlagsManager object
    :param p1: p1 object
    :param label: internal label for the data in <p1> loaded with <flags>
    :param str|None|list stimulus_number: one of the following:
    'all': all stimuli are used, generating as many subplots
    None: use the stimulus number in the flag "CTV_StimulusNumber"
    list: containing a list of stimulus numbers to use (stimuli are numbered 0, 1, 2...)
    :param str|None|list feature_number: one of the following:
    'all': all features of the CTV specified by the flags, generating as many subplots
    None: use the feature number in the flag "CTV_FeatureNumber"
    list: containing a list of feature numbers to use (features are numbered 0, 1, 2...)
    """

    if not plt.isinteractive():
        plt.ion()

    n_stim = p1.pulsed_stimuli_handler.get_number_of_stimuli()

    if stimulus_number is None:
        stimulus_number = [flags['CTV_StimulusNumber']]
    elif stimulus_number == "all":
        stimulus_number = range(n_stim)
    else:
        assert type(stimulus_number) is list and all(type(x) is int for x in stimulus_number), \
            f"stimulus_number can be either None, 'all' or a list of ints. Got {stimulus_number}"

    n_stim_used = len(stimulus_number)
    overview_frames_columns = []
    for stim_ind in stimulus_number:
        assert type(stim_ind) is int, f"For flag 'CTV_StimulusNumber' Expected int, got {type(stim_ind)}({stim_ind})"
        if n_stim > 0:
            assert 0 <= stim_ind < n_stim, \
                f"IndexError: Current measurement has {n_stim} stimuli, " \
                f"therefore stimulus_number can be in [0, {n_stim - 1}]. Got {stim_ind}"

        flags_copy = flags.copy()
        flags_copy.update_flags({"CTV_StimulusNumber": stim_ind})

        overview_frames = generate_overview_frame(flags_copy, p1, feature_number=feature_number)
        overview_frames_columns.append(overview_frames)

    n_features = len(overview_frames_columns[0])

    frame_size = p1.get_frame_size()
    aspect_ratio = frame_size[0] / frame_size[1]

    temp_width = min(10, 5 * n_stim_used)
    temp_height = min(10, 5 * n_features)

    fig, axs = plt.subplots(
        figsize=(temp_width, temp_height / aspect_ratio),
        constrained_layout=True, nrows=n_features, ncols=n_stim_used, squeeze=False)

    for col_ind, stim_ind in enumerate(stimulus_number):

        for feature_ind, overview_frame_this_feature in enumerate(overview_frames_columns[col_ind]):

            row_ind = feature_ind
            ax = axs[row_ind, col_ind]
            overview_frame_colorized_with_frame, data_limits, overview_generator_used = \
                colorize_overview_add_border_etc(overview_frame=overview_frame_this_feature, flags=flags, p1=p1)

            overview_for_output = prep_overview_for_output(overview_frame_colorized_with_frame)

            ax.imshow(np.flip(overview_for_output, axis=0), origin="lower")
            legendfactor = flags["SO_scaleLegendFactor"]
            ax.set_title(
                f'Feature Number: {feature_ind:d}; Stimulus Number: {stim_ind:d}\n'
                f'False color scale (CTV*{legendfactor:2.1f}) is '
                f'{data_limits[0] * legendfactor:2.3f} to {data_limits[1] * legendfactor:2.3f}'
            )

            def format_coord(x_img_data, y_img_data):
                y_overview = int(y_img_data + 0.5)
                x_overview = int(x_img_data + 0.5)
                if 0 <= y_overview < p1.metadata.format_y and 0 <= x_overview < p1.metadata.format_x:
                    z = overview_frame_this_feature[x_overview, y_overview]*legendfactor
                    reportline = 'Location: x=%.0i, y=%.0i, CTV Value (*%.0i)= %2.3f'
                    return reportline % (x_img_data, y_img_data, legendfactor, z)
                else:
                    return ''

            ax.format_coord = format_coord

            # add legend indicating the labels of ROIs marked if the flags "SO_showROIs" starts with a 2
            if np.floor(flags["SO_showROIs"] / 10) == 2:
                for roi_mask, color, label in overview_generator_used.roi_marker.roi_mask_color_label_tuples:
                    ax.plot([-1], [-1], "-", color=color, label=label)
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0.)

    plt.draw()


def create_bw_image_from_frame(frame, extra_flags=None):
    """
    Creates a BW image from a 2D frame using flags in <extra_flags> if specified
    :param numpy.ndarray frame: 2D frame in XY format with origin at bottom left
    :param dict|None extra_flags: flags as key value pairs
    :rtype: numpy.ndarray
    :returns: float64 X,Y,Color format with origin at bottom left
    """

    flags_2_update = {"SO_MV_colortable": "gray",
                      "SO_individualScale": 2,
                      }

    flags = FlagsManager()
    flags.update_flags(flags_2_update)

    if type(extra_flags) is dict:
        flags.update_flags(extra_flags)

    frame_bw, data_limits, overview_generator_used = \
        colorize_overview_add_border_etc(overview_frame=frame, flags=flags)

    return frame_bw
