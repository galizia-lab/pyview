import numpy as np


def ctv_for_FIDOR_chunks(curve):
    """
    input: a time trace (curve)
    output: one value, based on a number
    """
    base_ind, peak_ind = ctv_for_FIDOR_chunks_frames(curve)
    output = curve[peak_ind] - curve[base_ind]
    return output


def ctv_for_FIDOR_chunks_with_minmax_indices(curve, stim_frame=None):
    """
    input: a time trace (curve)
    output: ctv, ind1, ind2
    ctv: one value, based on a number; ind1 and ind2, so that CTV = curve[ind2] - curve[ind1]
    """
    curve = np.convolve(curve, np.ones(3)/3, mode='same')
    
    base_ind, peak_ind = ctv_for_FIDOR_chunks_frames(curve, stim_frame=stim_frame)
    output = curve[peak_ind] - curve[base_ind]
    return output, base_ind, peak_ind


def ctv_for_FIDOR_chunks_frames(curve, stim_frame=None):
    """
    input: a time trace (curve)
    output: two indices ind1 and ind2, so that CTV = curve[ind2] - curve[ind1]
    """
    if stim_frame is not None:
        middle = stim_frame
    else:
        middle = len(curve)//2
    # Ajay's calculation here
    # leftminpos = np.argmin(curve[:middle])
    # leftmaxpos = np.argmax(curve[:middle])
    # argminval  = np.argmin(curve[leftminpos:])
    # argmaxval  = np.argmax(curve[leftminpos:])

    # # assuming responses ride only on a flat or falling baseline;
    # if argminval == 0:  # positive response, or an early negative response, which is really rare
    #     pos_resp = True

    # elif argmaxval == 0:  # positive response in first half, maybe weak negative response, hard to quantify reliably
    #     base_ind = leftminpos + argminval
    #     peak_ind = leftmaxpos

    #     return base_ind, peak_ind

    # elif argminval < argmaxval:  # negative response
    #     pos_resp = False

    # else:  # argminval > argmaxval; positive response
    #     pos_resp = True

    # if pos_resp:
    #     base_ind = leftminpos + argminval
    #     peak_ind = leftminpos + argmaxval
    # else:
    #     base_ind = leftminpos + argmaxval
    #     peak_ind = leftminpos + argminval
    
    #new CTV Giovanni July 2023
    # get minimum to the left as base_ind. Define "left" as half the way to stimulus
    # get min and max around the stimulus
    # decide 'positive' or 'negative' based on size
    middle = int(middle)
    stim_range = int(middle//2)
    base_ind = np.argmin(curve[:stim_range]) # minimum in first quarter (or first half before stim-time)
    base_val = curve[base_ind]
    peak_ind_max = np.argmax(curve[stim_range:(middle+stim_range)]) + stim_range
    peak_ind_min = np.argmin(curve[stim_range:(middle+stim_range)]) + stim_range
    peak_val_max = curve[peak_ind_max] - base_val
    peak_val_min = curve[peak_ind_min] - base_val
    if abs(peak_val_max) > abs(peak_val_min):
        #pos_resp = True
        peak_ind = peak_ind_max
    else:
        #pos_resp = False
        peak_ind = peak_ind_min

    return base_ind, peak_ind