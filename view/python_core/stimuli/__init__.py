import logging
import pandas as pd
from .stimuli_parser import StimuliParamsParser


class BaseStimuliiHandler(object):

    def __init__(self):
        self.stimulus_frame = pd.DataFrame(columns=("Odor", "Concentration",
                                                    "Pulse Start Time", "Pulse End Time",
                                                    "Sampling Period"))
        self.stimulus_offset_td = pd.Timedelta(0)

    def initialize_stimulus_offset(self, mv_correctStimulusOnset, data_sampling_period):
        """
        Corrects all stimuli periods stored internally by adding a time interval specified by the flag
        "mv_correctStimulusOnset" to them.
        :param mv_correctStimulusOnset: float, flag mv_correct stimulus. Interpreted as frame number if it is less than
        1000, else as a time interval in milliseconds
        :param data_sampling_period: pd.Timedelta, the inter-frame-interval
        :return: None
        """

        # interprets mv_correctStimulusOnset in ms and converts to a pd.Timedelta object representing an interval
        # changed Sept. 19: stimulus correction is always in ms!
        if mv_correctStimulusOnset == 0:
            self.stimulus_offset_td = pd.Timedelta(0)
        else:
            self.stimulus_offset_td = pd.Timedelta(f"{mv_correctStimulusOnset}ms")

        if self.stimulus_frame.shape[0]:
            self.stimulus_frame["Pulse Start Time"] += self.stimulus_offset_td
            self.stimulus_frame["Pulse End Time"] += self.stimulus_offset_td
        else:
            logging.getLogger("VIEW").warning("No stimulus found in object. Stimulus offset not initialized!")

    def add_odor_pulse(self, odor, concentration,
                       on_frame: int = None, data_sampling_period: float = None,
                       on_ms: float = None,
                       off_frame: int = None, duration_ms: float = None):
        """
        Add an odor pulse stimlus, applying correction based on mv_correctOnsetStimulus.
        One of the following needs to specified to define stimulus pulse onset
        1. on_frame and data_sampling_period
        2. on_ms
        One of the following need to be specified to define stimulus pulse offset
        1. off_frame and data_sampling_period
        2. duration
        :param odor: string, odor applied
        :param concentration: float, logarithm to base 10 of the concentration of the odor applied
        :param on_frame: int, frame number of stimulus pulse onset
        :param float data_sampling_period: data sampling period in ms, i.e., 600 for 100 frames per minute
        :param on_ms: float, time of stimlus onset in milliseconds
        :param off_frame: int, frame number of stimulus pulse offset
        :param duration_ms: float, stimulus duration in milliseconds
        :return:
        """
        data_sampling_period_td = pd.Timedelta(f"{data_sampling_period}ms")

        if not pd.isnull(on_frame) and not pd.isnull(data_sampling_period) and pd.isnull(on_ms):
            # stimulus start, based on on_frame
            assert on_frame >= 0, f"on_frame must be >= 0. {on_frame} specified"
            on_time_from_frame = on_frame * data_sampling_period_td
        elif pd.isnull(on_frame) and not pd.isnull(on_ms):
            # stimulus start, based on on_ms
            assert on_ms >= 0, f"on_ms must be >= 0. {on_ms} specified"
            on_time_from_frame = pd.Timedelta(f"{on_ms}ms")
        elif not pd.isnull(on_frame) and not pd.isnull(on_ms) and not pd.isnull(data_sampling_period):
            # stimulus start, both on_ms and on_frame are given
            on_time_from_frame = on_frame * data_sampling_period_td
            on_time_from_time = pd.Timedelta(f"{on_ms}ms")
            assert on_time_from_time == on_time_from_frame, f"stimulus on_frame and on_time are contradictory: " \
                                                            f"check stimulus time in .lst file"
        else:
            return 1

        if not pd.isnull(off_frame):
            off_time_from_frame = (off_frame + 1) * data_sampling_period_td
            if not pd.isnull(duration_ms):
                logging.getLogger("VIEW").warning(
                    'During stimulus parsing: stimulus length taken from Stim_off in frames, '
                    'stim_duration has been ignored! Check info in .lst file')
        elif not pd.isnull(duration_ms):
            off_time_from_frame = on_time_from_frame + pd.Timedelta(f"{duration_ms}ms")
        else:
            return 1

        temp_df = pd.DataFrame([[odor,
                                 concentration,
                                 on_time_from_frame,
                                 off_time_from_frame,
                                 data_sampling_period_td]],
                               columns=self.stimulus_frame.columns)

        self.stimulus_frame = self.stimulus_frame.append(temp_df, ignore_index=True)

        return 0

    def get_number_of_stimuli(self):
        """
        returns the number of stimuli
        :return: int
        """

        return self.stimulus_frame.shape[0]

    def get_all_odors(self):
        """
        Returns an iterable of strings, containing all Odor stimuli applied
        :return: iterable
        """

        return self.stimulus_frame["Odour"].unique()

    def get_odor_info_at_times(self, times):

        """
        :param times: iterable of pandas.TimeDelta
        :returns odors, concs
        odors: list of str, containing odor information
        concs: list of str, containing concentration information
        """

        assert all(type(x) == pd.Timedelta for x in times), "times must be of type pandas.TimeDelta"

        odors = []
        concs = []

        for time in times:
            current_odors = []
            current_concs = []
            for row_index, row in self.stimulus_frame.iterrows():

                if (row["Pulse Start Time"] <= time) & (row["Pulse End Time"] >= time):
                    current_odors.append(row["Odor"])
                    current_concs.append(row["Concentration"])

            odors.append(current_odors)
            concs.append(current_concs)

        return odors, concs

    def get_pulse_start_times(self):
        """
        Returns the start times of all stimulus pulses
        :return: an Sequence, of pandas.Timedelta objects
        """
        return self.stimulus_frame["Pulse Start Time"].values

    def get_pulse_end_times(self):
        """
        Returns the end times of all stimulus pulses
        :return: an Sequence, of pandas.Timedelta objects
        """
        return self.stimulus_frame["Pulse End Time"].values

    def get_pulse_durations(self):
        """
        Returns the duration of all stimulus pulses
        :return: a Sequence of pandas.TimeDelta objects
        """
        return self.get_pulse_end_times() - self.get_pulse_start_times()

    def get_pulse_start_frames(self, allow_fractional_frames=False):
        """
        Return the array of pulse start times in frames.
        :param allow_fractional_frames: bool. If False, fractional frame numbers are replaced by None
        :return: an iterable, of floats or None
        """
        frame_numbers = [(x / y) for x, y in zip(self.stimulus_frame["Pulse Start Time"],
                                                 self.stimulus_frame["Sampling Period"])]

        if not allow_fractional_frames:
            frame_numbers = [int(x) if int(x) == x else None for x in frame_numbers]

        return frame_numbers

    def get_pulse_end_frames(self, allow_fractional_frames=False):
        """
        Return the array of pulse end times in frames. Non-integral frame numbers are replaced by None
        :param allow_fractional_frames: bool. If False, fractional frame numbers are replaced by None
        :return: an iterable, of floats or None
        """
        frame_numbers = [(x / y) for x, y in zip(self.stimulus_frame["Pulse End Time"],
                                                 self.stimulus_frame["Sampling Period"])]

        if not allow_fractional_frames:
            frame_numbers = [int(x) if int(x) == x else None for x in frame_numbers]

        return frame_numbers

    def get_pulse_start_end_frames(self, allow_fractional_frames=False):
        """
        Returns a list of tuples of start and end frames of stimulus pulses
        :param allow_fractional_frames: If False, fractional frame numbers are replaced by None
        :rtype: list
        """

        starts = self.get_pulse_start_frames(allow_fractional_frames)
        ends = self.get_pulse_end_frames(allow_fractional_frames)

        return list(zip(starts, ends))

    def get_first_stimulus_onset_frame(self):

        onset_frames = self.get_pulse_start_frames(allow_fractional_frames=True)
        if len(onset_frames):
            return int(onset_frames[0])  # round it if fractional
        else:
            return None

    def get_stimon_background_range(self, LE_StartBackground, LE_PrestimEndBackground, default_background):
        """
        Decides the start and end frames of background to use based on the onset of first stimulus,
        <LE_PrestimEndBackground>, <LE_StartBackground>
        :param int LE_StartBackground: see documentation of corresponding flag
        :param int LE_PrestimEndBackground: see documentation of corresponding flag
        :param tuple default_background: tuple of two ints, specifying the default background range, if
        the interpreted range is invalid
        :return: background_range, onset_frame_first_stimulus
        background_range: tuple of two ints, specifying background range to use in frame numbers
        onset_frame_first_stimulus: int, frame number of the onset of first stimulus.
        If the interpreted range is invalid, -1 will be returned
        """
        
        onset_frame_first_stimulus = self.get_first_stimulus_onset_frame()
        if onset_frame_first_stimulus is not None:
            end_background = onset_frame_first_stimulus - LE_PrestimEndBackground
            if end_background <= LE_StartBackground:
                logging.getLogger("VIEW").warning(
                    f"Encountered end_background <= start_background, which is invalid. "
                    f"Defaulting to the background range {default_background}")
                return default_background, -1
        else:
            logging.getLogger("VIEW").warning(
                f"No stimuli information specified in measurement list file. "
                f"Defaulting to the background range {default_background}")
            return default_background, -1

        return (LE_StartBackground, end_background), onset_frame_first_stimulus


class PulsedStimuliiHandler(BaseStimuliiHandler):

    def __init__(self):

        super().__init__()

    @classmethod
    def create_from_row(cls, row):

        stimulus_params = StimuliParamsParser().parse_row(row)

        handler = cls()

        for stim_ind, stimulus in stimulus_params.iter_stimuli():

            handler.add_odor_pulse(data_sampling_period=row["Cycle"],
                                   on_frame=stimulus["StimON"],
                                   off_frame=stimulus["StimOFF"],
                                   on_ms=stimulus["StimONms"],
                                   duration_ms=stimulus["StimLen"],
                                   odor=stimulus["Odour"],
                                   concentration=stimulus["OConc"])

        return handler





