import numpy as np
from view.python_core.utils.colors import interpret_flag_SO_MV_colortable
import view.python_core.overviews.roi_marker as roi_markers
import pandas as pd

from .temporal import get_temporal_processor
from .spatial import get_spatial_processor
from .data_limit import get_data_limit_decider_3D
from .write import get_writer
from .borders_and_annotations import BordersAndAnnotations
from .rotate import get_frame_rotator
from .colorizer import get_colorizer_3D
from .data_to_01 import get_normalizer
from .excluder import Excluder3D
import logging


class MovieExporter(object):

    def __init__(self, flags, p1):

        self.data_sampling_period = pd.Timedelta(f"{p1.metadata.trial_ticks}ms")

        frame_size = (p1.metadata.format_x, p1.metadata.format_y)

        self.colormap, self.bg_color_mpl_compliant, self.fg_color_mpl_compliant = \
            interpret_flag_SO_MV_colortable(SO_MV_colortable=flags["SO_MV_colortable"],
                                      fg_color=flags["mv_fgColor"],
                                      bg_color=flags["mv_bgColor"])

        self.temporal_processor = get_temporal_processor(filter_time_flag=flags["Signal_FilterTimeFlag"],
                                                         filter_time_size=flags["Signal_FilterTimeSize"])

        self.spatial_processor = get_spatial_processor(filter_space_flag=flags["Signal_FilterSpaceFlag"],
                                                       filter_space_size=flags["Signal_FilterSpaceSize"])

        self.excluder = Excluder3D(mv_FirstFrame=flags["mv_FirstFrame"],
                                   mv_LastFrame=flags["mv_LastFrame"],
                                   cutborder_x=flags["mv_cutborder"],
                                   cutborder_y=flags["mv_cutborder"])

        area_mask_2D_excluded = self.excluder.exclude_from_frame(p1.area_mask)

        self.data_limit_decider = get_data_limit_decider_3D(flags, area_mask_2D_excluded)

        self.individual_scale = flags["mv_individualScale"]

        self.colorizer = get_colorizer_3D(flags=flags, p1=p1, colormap=self.colormap,
                                          area_mask_2D_excluded=area_mask_2D_excluded,
                                          excluder=self.excluder)
        revised_frame_size = self.excluder.revise_frame_size(frame_size)
        self.roi_marker = roi_markers.get_roi_marker_3D(
            flags=flags, measurement_label=p1.metadata.ex_name,
            fg_color=self.fg_color_mpl_compliant, unexcluded_frame_size=frame_size, excluder=self.excluder)

        self.frame_rotater = get_frame_rotator(rotate=flags["mv_rotateImage"],
                                               reverse=flags["mv_reverseIt"])

        modified_frame_size = self.frame_rotater.transform_frame_size(revised_frame_size)

        self.border_annotations_adder = BordersAndAnnotations(flags=flags,
                                                              colormap=self.colormap,
                                                              fg_color_for_mpl=self.fg_color_mpl_compliant,
                                                              bg_color_for_mpl=self.bg_color_mpl_compliant,
                                                              frame_size=modified_frame_size,
                                                              data_sampling_period=self.data_sampling_period,
                                                              pulsed_stimuli_handler=p1.pulsed_stimuli_handler,
                                                              )

        self.writer = get_writer(flags)

    def preprocess(self, data: np.ndarray):

        time_filtered_data = self.temporal_processor.filter(data)

        time_space_filtered_data = self.spatial_processor.filter_3D(time_filtered_data)

        data_cropped = self.excluder.exclude_from_movie(time_space_filtered_data)

        first_frame_retained, last_frame_retained = self.excluder.revised_frame_start_end(data.shape)

        return data_cropped, first_frame_retained, last_frame_retained

    def get_normalizer(self, data: np.ndarray):

        vmin, vmax = self.data_limit_decider.get_data_limit(data)
        return get_normalizer(vmin=vmin, vmax=vmax, mv_individualScale=self.individual_scale)

    def colorize(self, data: np.ndarray, data_to_01_mapper):

        return self.colorizer.colorize(data=data, data_to_01_mapper=data_to_01_mapper)

    def rotate_frame(self, frame_data):

        return self.frame_rotater.transform(frame_data)

    def add_borders_annotations_to_frame(self, frame_data, frame_number, static_frame):

        return self.border_annotations_adder.add(frame_data, frame_number, static_frame)

    def write_to_file(self, data_numpy_list, full_filename_without_extension):

        return self.writer.write(data_numpy_list, self.data_sampling_period, full_filename_without_extension)

    def add_rois(self, frame_data):
        return self.roi_marker.draw(frame_data)


def export_movie(flags, p1, full_filename_without_extension):

    movie_exporter = MovieExporter(flags=flags, p1=p1)

    preprocessed_data, first_frame_retained, last_frame_retained = movie_exporter.preprocess(p1.sig1)

    data_to_01_mapper = movie_exporter.get_normalizer(preprocessed_data)

    static_frame = movie_exporter.border_annotations_adder.static_border_adder.get_static_frame(data_to_01_mapper)

    colorized_data = movie_exporter.colorize(preprocessed_data, data_to_01_mapper)

    finalized_frame_data_list = []
    for frame_number in range(first_frame_retained, last_frame_retained + 1):

        frame_data = colorized_data[:, :, frame_number - first_frame_retained, :]

        frame_data_with_rois = movie_exporter.add_rois(frame_data)

        rotated_frame_data = movie_exporter.rotate_frame(frame_data_with_rois)

        finalized_frame_data = movie_exporter.add_borders_annotations_to_frame(rotated_frame_data,
                                                                               frame_number,
                                                                               static_frame)

        finalized_frame_data_list.append(finalized_frame_data)

    logging.getLogger("VIEW").info(f"mv_individualScale set to:{flags['mv_individualScale']}. Minimum and maximum are: "
                 f"{data_to_01_mapper.get_data_limits()}")
    op_filename = movie_exporter.write_to_file(finalized_frame_data_list, full_filename_without_extension)
    return op_filename




