from view.python_core.rois.roi_io import get_roi_io_class
from view.python_core.utils.colors import get_qualitative_colors
import numpy as np
from view.python_core.movies.excluder import Excluder2D


class BlankROIMarker(object):

    def __init__(self):

        super().__init__()

    def draw(self, frame):
        return frame


class BaseROIMarker(BlankROIMarker):

    def __init__(self, roi_data_dict):

        super().__init__()
        self.roi_data_dict = roi_data_dict
        self.roi_mask_color_label_tuples = []

    def draw(self, frame):

        frame_copy = frame.copy()
        for roi_mask, col, label in self.roi_mask_color_label_tuples:
            frame_copy[roi_mask, :] = col

        return frame_copy


class ROIMarkerSingleColor(BaseROIMarker):

    def __init__(self, perimeter_color, roi_data_dict: dict, unexcluded_frame_size, excluder: Excluder2D):
        super().__init__(roi_data_dict)
        for roi_label, roi in roi_data_dict.items():
            perimeter_mask, boolean_mask = roi.get_perimeter_mask(unexcluded_frame_size)
            perimeter_mask_excluded = excluder.exclude_from_frame(perimeter_mask)
            self.roi_mask_color_label_tuples.append(
                (perimeter_mask_excluded, perimeter_color, roi.label))


class ROIMarkerQualitativeColors(BaseROIMarker):

    def __init__(self, roi_data_dict: dict, unexcluded_frame_size, excluder: Excluder2D):

        super().__init__(roi_data_dict)
        roi_labels_sorted = sorted(roi_data_dict.keys())
        colors = get_qualitative_colors(len(roi_labels_sorted))
        for roi_label, color in zip(roi_labels_sorted, colors):
            roi = roi_data_dict[roi_label]
            perimeter_mask, boolean_mask = roi.get_perimeter_mask(unexcluded_frame_size)
            perimeter_mask_excluded = excluder.exclude_from_frame(perimeter_mask)
            self.roi_mask_color_label_tuples.append(
                (perimeter_mask_excluded, color, roi_label))


class ROIMarkerQualitativeColorsBlankBackground(ROIMarkerQualitativeColors):

    def __init__(self, roi_data_dict: dict, unexcluded_frame_size, excluder: Excluder2D, bg_color):

        super().__init__(
            roi_data_dict=roi_data_dict, unexcluded_frame_size=unexcluded_frame_size,
            excluder=excluder
        )
        self.bg_color = bg_color

    def draw(self, frame):

        blank_frame = np.empty_like(frame)
        blank_frame[:, :, :] = self.bg_color
        return super().draw(blank_frame)


def get_roi_marker_2D(flags, fg_color, bg_color, unexcluded_frame_size, excluder, measurement_label):

    how_to_draw = np.floor(flags["SO_showROIs"] / 10)
    source = flags["SO_showROIs"] % 10

    roi_io_class = get_roi_io_class(RM_ROITrace=source)

    if how_to_draw == 0:

        return BlankROIMarker()

    elif how_to_draw == 1:

        roi_data_dict, roi_file = roi_io_class.read(flags, measurement_label)
        return ROIMarkerSingleColor(
            perimeter_color=fg_color, roi_data_dict=roi_data_dict,
            unexcluded_frame_size=unexcluded_frame_size, excluder=excluder)

    elif how_to_draw == 2:

        roi_data_dict, roi_file = roi_io_class.read(flags, measurement_label)
        return ROIMarkerQualitativeColorsBlankBackground(
            roi_data_dict=roi_data_dict, unexcluded_frame_size=unexcluded_frame_size,
            bg_color=bg_color, excluder=excluder)

    elif how_to_draw == 3:

        roi_data_dict, roi_file = roi_io_class.read(flags, measurement_label)
        return ROIMarkerQualitativeColors(
            roi_data_dict=roi_data_dict, unexcluded_frame_size=unexcluded_frame_size,
            excluder=excluder)

    else:
        raise NotImplementedError


def get_roi_marker_3D(flags, fg_color, unexcluded_frame_size, excluder, measurement_label):
 
    how_to_draw = np.floor(flags["mv_showROIs"] / 10)
    source = flags["mv_showROIs"] % 10

    roi_io_class = get_roi_io_class(RM_ROITrace=source)

    if how_to_draw == 0:

        return BlankROIMarker()

    elif how_to_draw == 1:

        roi_data_dict, roi_file = roi_io_class.read(flags, measurement_label)
        return ROIMarkerSingleColor(
            perimeter_color=fg_color, roi_data_dict=roi_data_dict,
            unexcluded_frame_size=unexcluded_frame_size, excluder=excluder)

    else:
        raise NotImplementedError




