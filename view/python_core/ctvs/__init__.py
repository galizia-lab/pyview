import inspect
import math
from typing import Callable

import numpy as np

from view.python_core.ctvs.chunk_ctv_funcs_from_fidor import ctv_for_FIDOR_chunks_with_minmax_indices


def ctv_dummy(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1):
    """
    dummy CTV to specify function call signature
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, use 1 for first stimulus
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    return [0]


def ctv_0(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1):
    """
    alias for ctv_303, retained for backward compatibility
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, use 1 for first stimulus
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """

    return ctv_303(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1
    )


def ctv_22(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1):
    """
    (mean of 3 frames around <last_frame>) – (mean of 3 frames around <first_frame>)
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """

    first_frame_index = first_frame
    last_frame_index = last_frame

    assert 1 <= last_frame_index <= len(time_trace) - 2, f"Error calculating CTV 22: lastframe={last_frame} " \
                                                         f"is invalid for data with {len(time_trace)} frames. " \
                                                         f"Need three frames around lastframe."
    assert 1 <= first_frame_index <= len(time_trace) - 2, f"Error calculating CTV 22: firstframe={first_frame} " \
                                                          f"is invalid for data with {len(time_trace)} frames. " \
                                                          f"Need three frames around firstframe."
    ctv_value = np.mean(time_trace[last_frame_index - 1: last_frame_index + 2]) \
                - np.mean(time_trace[first_frame_index - 1: first_frame_index + 2])

    return [ctv_value]


def ctv_222(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    (mean of 4 frames starting at <last_frame>) – (mean of 4 frames starting at <first_frame>)
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """

    first_frame_index = first_frame
    last_frame_index = last_frame

    assert 0 <= last_frame_index <= len(time_trace) - 4, f"Error calculating CTV 222: lastframe={last_frame} " \
                                                         f"is invalid for data with {len(time_trace)} frames. " \
                                                         f"Need three frames around lastframe."
    assert 0 <= first_frame_index <= len(time_trace) - 4, f"Error calculating CTV 22: firstframe={first_frame} " \
                                                          f"is invalid for data with {len(time_trace)} frames. " \
                                                          f"Need three frames around firstframe."
    ctv_value = np.mean(time_trace[last_frame_index: last_frame_index + 4]) - \
                    np.mean(time_trace[first_frame_index: first_frame_index + 4])

    return [ctv_value]


def ctv_35(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    A - B where A=(three-frame-average around the maximum responses in an interval of 3 seconds after stimulus onset),
    B=(mean of 3 frames that preceed the onset of stimulus by LE_PrestimEndBackground frames)
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """

    stim_on_frame_ind = int(stim_on_times[stimulus_number] / sampling_period) + 1
    frame_ind_after_3s_stim_onset = int((stim_on_times[stimulus_number] + 3000) / sampling_period) + 1

    # reset to end of trace if stimulus onset is less than 3 seconds before the end of trace
    frame_ind_after_3s_stim_onset = min(frame_ind_after_3s_stim_onset, len(time_trace) - 1)

    argmax_in_3s_after_stim_onset \
        = np.argmax(time_trace[stim_on_frame_ind: frame_ind_after_3s_stim_onset + 1]) + stim_on_frame_ind

    # make sure there are three frames around <argmax_in_3s_after_stim1_onset>. This will only happen if the
    # <argmax_in_3s_after_stim1_onset> happens to be the first or last frame
    argmax_in_3s_after_stim_onset = max(1, argmax_in_3s_after_stim_onset)
    argmax_in_3s_after_stim_onset = min(len(time_trace) - 2, argmax_in_3s_after_stim_onset)

    A = np.mean(time_trace[argmax_in_3s_after_stim_onset - 1: argmax_in_3s_after_stim_onset + 2])

    # make sure there are three frames around <stim1_on_frame_ind2use>. This will only happen if the
    # <stim1_on_frame_ind> happens to be the first or last frame
    stim_on_frame_ind2use = \
        min(max(1, stim_on_frame_ind - flags["LE_PrestimEndBackground"]), len(time_trace) - 2)

    B = np.mean(time_trace[stim_on_frame_ind2use - 1: stim_on_frame_ind2use + 2])

    return [A - B]


def ctv_22and35(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1):
    """
    feature 1: ctv_22; feature 2: ctv_35
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: two members, float
    """

    return [
        ctv_22(
            time_trace, sampling_period,
            first_frame, last_frame,
            stimulus_number, stim_on_times, stim_off_times,
            flags, p1)[0],
        ctv_35(
            time_trace, sampling_period,
            first_frame, last_frame,
            stimulus_number, stim_on_times, stim_off_times,
            flags, p1)[0]
        ]


def ctv_300(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    (definition taken forward from VIEW-IDL) mean of all frames, useful for simulated photographs
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    return [np.nanmean(time_trace)]


def ctv_301(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    (definition taken forward from VIEW-IDL) mean of frames 5 to 10, which is generally before stimulus onset.
    Useful for morphological views.
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    return [np.nanmean(time_trace[4: 10])]


def ctv_302(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    mean of frames from <first_frame> to <last_frame> (both inclusive).
    One possible use: calculate morphological image by specifying manually the range of frames to average.
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    first_frame_index = first_frame
    last_frame_index = last_frame + 1

    assert 0 <= last_frame_index <= len(time_trace) - 1, f"Error calculating CTV 302: lastframe={last_frame} " \
                                                         f"is invalid for data with {len(time_trace)} frames. "

    assert 0 <= first_frame_index <= len(time_trace) - 1, f"Error calculating CTV 302: firstframe={first_frame} " \
                                                          f"is invalid for data with {len(time_trace)} frames. "

    return [np.nanmean(time_trace[first_frame_index: last_frame_index + 1])]


def ctv_303(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    Average of background frames, calculated using stimulus onset and the flags LE_StartBackground and
    LE_PrestimEndBackground. Can be useful to visualize and compare baseline values of signals.
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """

    return [np.nanmean(time_trace[
                       p1.metadata.background_frames[0]: p1.metadata.background_frames[1] + 1])]


def ctv_330(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    median of all frames
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    return [np.nanmedian(time_trace)]


def ctv_331(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    median of frames 5 to 10, which is generally before stimulus onset.
    Useful for morphological views.
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    return [np.nanmedian(time_trace[4: 10])]


def ctv_332(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    median of frames from <first_frame> to <last_frame> (both inclusive).
    One possible use: calculate morphological image by specifying manually the range of frames to average.
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """
    first_frame_index = first_frame
    last_frame_index = last_frame + 1

    assert 0 <= last_frame_index <= len(time_trace) - 1, f"Error calculating CTV 302: lastframe={last_frame} " \
                                                         f"is invalid for data with {len(time_trace)} frames. "

    assert 0 <= first_frame_index <= len(time_trace) - 1, f"Error calculating CTV 302: firstframe={first_frame} " \
                                                          f"is invalid for data with {len(time_trace)} frames. "
    return [np.nanmedian(time_trace[first_frame_index: last_frame_index + 1])]


def ctv_333(
        time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times, 
        flags, p1):
    """
    Median of background frames, calculated using stimulus onset and the flags LE_StartBackground and
    LE_PrestimEndBackground. Can be useful to visualize and compare baseline values of signals.
    :param time_trace: iterable of numbers
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
    :param stimulus_number: int, indicates the which stimulus to use, where stimuli are numbered 0, 1, 2...
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :rtype: list
    :return: one member, float
    """

    return [np.nanmedian(time_trace[
                       p1.metadata.background_frames[0]: p1.metadata.background_frames[1] + 1])]


def ctv_chunk_magnitude_basic(
        time_trace, sampling_period=None,
        first_frame=None, last_frame=None,
        stimulus_number=None, stim_on_times=None, stim_off_times=None,
        flags=None, p1=None):
    """

    :param time_trace: iterable of numbers
    :param sampling_period: not used
    :param first_frame: not used
    :param last_frame: not used
    :param stimulus_number: not used
    :param stim_on_times: not used
    :param stim_off_times: not used
    :param flags: not used
    :param p1: not used
    :rtype: list
    :return: estimated_magnitude, base_ind, peak_ind
    estimated_magnitude: float, estimate of signal magnitude, kind of peak - baseline
    base_ind: int, index corresponding to the value used as baseline
    peak_ind, int, index corresponding to the value used as peak
    """

    return ctv_for_FIDOR_chunks_with_minmax_indices(time_trace)


def get_custom_ctv_method(file, function_name):
    
    with open(file, 'r') as fh:
        import scipy
        exec(compile(fh.read(), "<string>", "exec"), {"np": np, "scipy": scipy}, locals())
        ctv_method = locals()[function_name]

    assert callable(ctv_method), f"The function '{function_name}' in {file} is not a function."
    assert inspect.signature(ctv_method) == inspect.signature(ctv_dummy), \
        f"The function '{function_name}' in {file} has an incorrect signature to be a CTV method"

    return ctv_method


def get_ctv_function(ctv_method, ctv_method_file):

    to_return = None
    possible_function_name = f"ctv_{ctv_method}"
    if possible_function_name in globals():
        possible_function = globals()[possible_function_name]
        if callable(possible_function):
            return possible_function

    if to_return is None and type(ctv_method) is str:

        return get_custom_ctv_method(ctv_method_file, ctv_method)

    raise NotImplementedError


def get_all_available_ctvs():

    available_ctvs = []

    for object_name, object in globals().items():

        if isinstance(object, Callable) and object_name.startswith("ctv_"):
            # to catch values like ctv_dummy
            try:
                available_ctvs += [int(object_name[4:])]
            except ValueError as ve:
                pass

    return available_ctvs


