from view.python_core.utils.colors import mpl_color_to_PIL
from .mark_stimulus import get_stimulus_marker
from .frame_time import get_time_string_adder
from .static_border import get_static_border_adder_3D
from view.python_core.utils.pil_helpers import numpy_to_pil_image, pil_image_to_numpy
from view.python_core.utils.fonts import resolve_font_file, get_maximum_font_size_by_width


class BordersAndAnnotations(object):

    def __init__(self, flags, frame_size, data_sampling_period, pulsed_stimuli_handler,
                 colormap, fg_color_for_mpl, bg_color_for_mpl):

        fg_color_for_pil = mpl_color_to_PIL(fg_color_for_mpl)
        bg_color_for_pil = mpl_color_to_PIL(bg_color_for_mpl)
        self.data_sampling_period = data_sampling_period

        font_name = flags["mv_fontName"]
        font_file = resolve_font_file(font_name)
        
        # font size suggestion based on possible time strings and the flag mv_displayTime
        time_font_size_suggestion_full = get_maximum_font_size_by_width(
            maximum_width=frame_size[0], font_name=font_file, text="00 m 00.000 s")
        if flags["mv_displayTime"] > 0:
            time_font_size_suggestion = max(int(flags["mv_displayTime"] * time_font_size_suggestion_full), 8)
        else:
            time_font_size_suggestion = time_font_size_suggestion_full

        # initialization of stimulus_marker will provide a suggestion for font size in stimulus_marker.font_size
        # if stimulus marker does not use a font, stimulus_marker.font_size will be None
        self.stimulus_marker = get_stimulus_marker(
            mv_markStimulus=flags["mv_markStimulus"],
            left_xgap=flags["mv_xgap"],
            mv_ygap=flags["mv_ygap"],
            color_for_pil=fg_color_for_pil,
            pulsed_stimuli_handler=pulsed_stimuli_handler,
            font_file=font_file,
            frame_size=frame_size,
        )

        # make a decision on font size based on time string, considering stimulus string if required
        if self.stimulus_marker.font_size is not None:
            font_size_suggestion = max(min(time_font_size_suggestion, self.stimulus_marker.font_size), 8)
        else:
            font_size_suggestion = time_font_size_suggestion

        self.stimulus_marker.font_size = font_size_suggestion

        self.static_border_adder, revised_right_xgap = get_static_border_adder_3D(
            flags=flags,
            fg_color_for_mpl=fg_color_for_mpl,
            bg_color_for_mpl=bg_color_for_mpl,
            colormap=colormap,
            frame_size=frame_size,
            font_file=font_file,
            font_size=font_size_suggestion)
        
        self.time_string_adder = get_time_string_adder(
            mv_display_time=flags["mv_displayTime"],
            mv_suppress_ms=flags["mv_suppressMilliseconds"],
            color_for_pil=fg_color_for_pil,
            right_xgap=revised_right_xgap,
            mv_ygap=flags["mv_ygap"],
            pulsed_stimuli_handler=pulsed_stimuli_handler,
            font_file=font_file,
            font_size=font_size_suggestion
        )

    def add(self, frame_data, frame_number, static_frame):

        frame_data_with_border = self.static_border_adder.composite(frame_data, static_frame)

        frame_time = self.data_sampling_period * (frame_number - 1)

        pil_image = numpy_to_pil_image(frame_data_with_border)

        pil_image_with_time = self.time_string_adder.add(pil_image, frame_time)

        pil_image_with_time_stimulus = self.stimulus_marker.mark(pil_image_with_time, frame_time)

        annotated_frame_data = pil_image_to_numpy(pil_image_with_time_stimulus)

        return annotated_frame_data















