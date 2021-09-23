import numpy as np


def ctv_for_FIDOR_chunks(curve):
    """
    input: a time trace (curve)
    output: one value, based on a number
    """
    base_ind, peak_ind = ctv_for_FIDOR_chunks_frames(curve)
    output = curve[peak_ind] - curve[base_ind]
    return output


def ctv_for_FIDOR_chunks_with_minmax_indices(curve):
    """
    input: a time trace (curve)
    output: ctv, ind1, ind2
    ctv: one value, based on a number; ind1 and ind2, so that CTV = curve[ind2] - curve[ind1]
    """
    base_ind, peak_ind = ctv_for_FIDOR_chunks_frames(curve)
    output = curve[peak_ind] - curve[base_ind]
    return output, base_ind, peak_ind


def ctv_for_FIDOR_chunks_frames(curve):
    """
    input: a time trace (curve)
    output: two indices ind1 and ind2, so that CTV = curve[ind2] - curve[ind1]
    """
    middle = len(curve)//2
    leftminpos = np.argmin(curve[:middle])
    leftmaxpos = np.argmax(curve[:middle])
    argminval = np.argmin(curve[leftminpos:])
    argmaxval = np.argmax(curve[leftminpos:])

    # assuming responses ride only on a flat or falling baseline;
    if argminval == 0:  # positive response, or an early negative response, which is really rare
        pos_resp = True

    elif argmaxval == 0:  # positive response in first half, maybe weak negative response, hard to quantify reliably
        base_ind = leftminpos + argminval
        peak_ind = leftmaxpos

        return base_ind, peak_ind

    elif argminval < argmaxval:  # negative response
        pos_resp = False

    else:  # argminval > argmaxval; positive response
        pos_resp = True

    if pos_resp:
        base_ind = leftminpos + argminval
        peak_ind = leftminpos + argmaxval
    else:
        base_ind = leftminpos + argmaxval
        peak_ind = leftminpos + argminval

    return base_ind, peak_ind