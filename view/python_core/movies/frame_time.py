import pandas as pd
import numpy as np
from view.python_core.utils.pil_helpers import add_string
import logging


class DisplayTimeFormatterFull(object):

    def __init__(self, frame_time):

        super().__init__()

        if frame_time < pd.Timedelta(0):
            self.prefix = "-"
            frame_time = -frame_time
        else:
            self.prefix = ""

        total_seconds = frame_time.total_seconds()

        minutes = int(np.floor(total_seconds / 60))
        self.seconds = total_seconds - (minutes * 60)

        if minutes > 0:
            self.minutes_string = f"{minutes} m "
        else:
            self.minutes_string = ""

    def format(self):

        return f"{self.prefix}{self.minutes_string}{self.seconds:6.3f} s"


class DisplayTimeWithoutMS(DisplayTimeFormatterFull):

    def __init__(self, frame_time):

        super().__init__(frame_time)

    def format(self):
        return f"{self.prefix}{self.minutes_string}{self.seconds:2.0f} s"


class TimeStringAdderBlank(object):

    def __init__(self):

        super().__init__()
        self.font_size = None

    def add(self, pil_image, frame_time):
        return pil_image


class TimeStringAdder(TimeStringAdderBlank):

    def __init__(self, time_formatter, mv_ygap, right_xgap,
                 color_for_pil, pulsed_stimuli_handler, font_file, font_size):

        super().__init__()
        self.time_formatter = time_formatter
        self.mv_ygap = mv_ygap
        self.right_xgap = right_xgap
        self.color_for_pil = color_for_pil
        stim_pulse_start_times = pulsed_stimuli_handler.get_pulse_start_times()
        if len(stim_pulse_start_times):
            self.offset = -stim_pulse_start_times.min()
        else:
            self.offset = pd.Timedelta(0)
            logging.getLogger("VIEW").info("Since no stimulii were specified, first frame of the movie will have a display time of 0")
        self.font_file = font_file
        self.font_size = font_size

    def add(self, pil_image, frame_time):

        time_y_pos = pil_image.height - self.mv_ygap + int(0.1 * self.font_size)

        frame_time_to_show = frame_time + self.offset

        frame_time_string = self.time_formatter(frame_time_to_show).format()

        pil_image = add_string(pil_image, text=frame_time_string,
                               position=(pil_image.width - self.right_xgap, time_y_pos + int(0.25 * self.font_size)),
                               font_size=self.font_size, fill_color_for_pil=self.color_for_pil,
                               horizontal_alignment="right", vertical_alignment="top", font_file=self.font_file)
        return pil_image


def get_time_string_adder(mv_display_time, mv_suppress_ms, right_xgap, mv_ygap, color_for_pil,
                          pulsed_stimuli_handler, font_file, font_size):

    if mv_suppress_ms:
        time_formatter = DisplayTimeWithoutMS
    else:
        time_formatter = DisplayTimeFormatterFull

    if mv_display_time > 0:
        return TimeStringAdder(
            mv_ygap=mv_ygap, time_formatter=time_formatter,
            right_xgap=right_xgap,
            color_for_pil=color_for_pil,
            pulsed_stimuli_handler=pulsed_stimuli_handler, font_file=font_file,
            font_size=font_size)

    else:

        return TimeStringAdderBlank()






