from scipy.ndimage.filters import median_filter, uniform_filter
import numpy as np
from scipy.signal import kaiserord, firwin, freqz, lfilter


def apply_filter(matrix_in: np.ndarray, view_flags, filter_type: str):

    if filter_type == "median":
        func = median_filter
        interpretation_func = view_flags.interpret_median_filter_params
    elif filter_type == "mean":
        func = uniform_filter
        interpretation_func = view_flags.interpret_mean_filter_params
    else:
        raise NotImplementedError(f"Filter type can be either 'median' or 'mean', got {filter_type}")

    size_in_space, size_in_time = interpretation_func()

    if size_in_time is None and size_in_space is None:
        return matrix_in

    if len(matrix_in.shape) == 3:  # assume data format is XYT
        sizes_along_dimension_of_input = (size_in_space, size_in_space, size_in_time)
    elif len(matrix_in.shape) == 2:  # assume data format is XY
        sizes_along_dimension_of_input = (size_in_space, size_in_space)
    elif len(matrix_in.shape) == 1:  # assume data is a time trace
        sizes_along_dimension_of_input = (size_in_time,)
    else:
        raise NotImplementedError

    return func(matrix_in, size=sizes_along_dimension_of_input, mode="nearest")


def filter_kaisord_highpass(signal, sampling_rate, cutoff=100, transitionWidth=40, rippleDB=20):
    """
    Applies a digital high pass filter to <signal>.
    :param Sequence signal: sequence of floats representing the signal to be filtered
    :param float sampling_rate: sampling rate of <signal> in Hz
    :param float cutoff: in Hz, frequencies above this will pass
    :param float transitionWidth: in Hz, over which filter gain transits from pass to stop
    :param float rippleDB: in DB, amplitude of ripple of frequency band stopped
    :return: Sequence of float, representing the filtered signal
    """
    nyqFreq = sampling_rate / 2

    transitionWidth = min(transitionWidth, cutoff)

    N, beta = kaiserord(rippleDB, transitionWidth / nyqFreq)

    tapsLP = firwin(N, cutoff / nyqFreq, window=('kaiser', beta))

    delay_samples = int((N - 1) * 0.5)

    temp = np.zeros((N,))
    temp[delay_samples] = 1
    tapsHP = temp - tapsLP

    temp = np.empty((len(signal) + 2 * delay_samples))
    temp[:delay_samples] = signal[0]
    temp[delay_samples: delay_samples + len(signal)] = signal
    temp[-delay_samples:] = signal[-1]
    temp1 = lfilter(tapsHP, 1.0, temp)
    signal_filtered = temp1[2 * delay_samples: 2 * delay_samples + len(signal)]

    # ----- code for debugging ----
    # from matplotlib import pyplot as plt
    # plt.ion()
    # fig, ax = plt.subplots(figsize=(7, 5.6))
    # ax.plot(signal, "-b", label="unfiltered")
    # ax.plot(signal_filtered, "-r", label='filtered')
    # ax.legend(loc="best")
    # plt.draw()
    # input("Press any key to continue")
    # plt.close()
    # ------------------------------
    return signal_filtered
