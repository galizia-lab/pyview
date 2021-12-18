
import numpy as np




# #expected signature is like this:
# def ctv_dummy(
#         time_trace, sampling_period,
#         first_frame, last_frame,
#         stimulus_number, stim_on_times, stim_off_times,
#         flags, p1):
#     """
#     dummy CTV to specify function call signature
#     :param time_trace: iterable of numbers
#     :param sampling_period: float, sampling period of <time_trace>, in ms
#     :param first_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
#     :param last_frame: int, interpreted as a frame number, where frames are numbered 0, 1, 2...
#     :param stimulus_number: int, indicates the which stimulus to use, use 1 for first stimulus
#     :param stim_on_times: list of floats, stimulus onset times, in ms
#     :param stim_off_times: list of floats, stimulus offset times, in ms
#     :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
#     :param p1: pandas.Series object, internal representation of data
#     :rtype: list
#     :return: one member, float
#     """
#     return [0]

def ctvBente(time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1):
    """
    ana's method -222
    mean(13-16) - mean(6-9) 4 frames each
    <insert a brief description of the method here>
    :param time_trace: iterable of numbers
    :param first_frame: int, interpreted as a frame number, where frames are numbered 1, 2, 3...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 1, 2, 3...
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :return: float
    """
    # print('**************************** running ctvBente now: ')
    # print('len time trace is: ', str(len(time_trace)))
    
    
    output = np.mean(time_trace[30:40]) - np.mean(time_trace[10:20])
    return [output]


def myownctv22(time_trace, sampling_period,
        first_frame, last_frame,
        stimulus_number, stim_on_times, stim_off_times,
        flags, p1):
    """
    ana's method -222
    mean(13-16) - mean(6-9) 4 frames each
    <insert a brief description of the method here>
    :param time_trace: iterable of numbers
    :param first_frame: int, interpreted as a frame number, where frames are numbered 1, 2, 3...
    :param last_frame: int, interpreted as a frame number, where frames are numbered 1, 2, 3...
    :param sampling_period: float, sampling period of <time_trace>, in ms
    :param stim_on_times: list of floats, stimulus onset times, in ms
    :param stim_off_times: list of floats, stimulus offset times, in ms
    :param flags: FlagsManager object, is a mapping of flag names to flags values with additional functions
    :param p1: pandas.Series object, internal representation of data
    :return: float
    """
    output = np.mean(time_trace[30:40]) - np.mean(time_trace[5:95])
    return [output]
