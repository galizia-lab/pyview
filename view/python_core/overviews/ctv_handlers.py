from ..ctvs import get_ctv_function
import numpy as np
import pandas as pd
from ..flags import FlagsManager


class PixelWiseCTVHandler(object):

    def __init__(self, flags: FlagsManager, p1):

        super().__init__()

        try:
            ctv_method_file = flags.get_ctv_method_file()
        except FileNotFoundError as fnfe:
            ctv_method_file = None

        self.ctv_method = get_ctv_function(flags["CTV_Method"], ctv_method_file)
        self.ctv_firstframe = flags["CTV_firstframe"]
        self.ctv_lastframe = flags["CTV_lastframe"]
        self.sampling_period = p1.metadata.trial_ticks

        stim_on_times_td = p1.pulsed_stimuli_handler.get_pulse_start_times()
        if len(stim_on_times_td) > 0:
            self.stim_on_times = stim_on_times_td / pd.Timedelta("1ms")
        else:
            self.stim_on_times = None

        stim_off_times_td = p1.pulsed_stimuli_handler.get_pulse_end_times()
        if len(stim_off_times_td) > 0:
            self.stim_off_times = stim_off_times_td / pd.Timedelta("1ms")
        else:
            self.stim_off_times = None

        self.stimulus_number = flags["CTV_StimulusNumber"]

        self.flags = flags
        self.p1 = p1

    def apply(self, data):
        """
        Apply the CTV specified in self.flags during initialization pixel wise to generate overview frames
        :param numpy.ndarray data: 3D, XYT
        :rtype: numpy.ndarray
        :return: dimensions: features-X-Y
        """

        result_frame = None

        for x_ind, y_ind in np.ndindex(*data.shape[:2]):
            features = self.apply_pixel(data[x_ind, y_ind, :])
            if result_frame is None:
                result_frame = np.empty((len(features), *data.shape[:2]))

            result_frame[:, x_ind, y_ind] = features

        return result_frame  # dimensions: features-X-Y

    def apply_pixel(self, timetrace):

        return self.ctv_method(
            time_trace=timetrace,
            first_frame=self.ctv_firstframe,
            last_frame=self.ctv_lastframe,
            sampling_period=self.sampling_period,
            stim_on_times=self.stim_on_times,
            stim_off_times=self.stim_off_times,
            stimulus_number=self.stimulus_number,
            flags=self.flags,
            p1=self.p1)


def get_ctv_handler(flags, p1):

    if flags["SO_Method"] == 0:

        return PixelWiseCTVHandler(flags=flags, p1=p1)

    else:
        raise NotImplementedError(
            f"Features with 'SO_Method' set to {flags['SO_Method']} have not yet been implemented\n")












