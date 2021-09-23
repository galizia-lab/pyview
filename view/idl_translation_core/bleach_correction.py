import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import logging


# for the linear fit on the logarithm, to estimate initial parameters
def fit_exp_linear_autoOffset(t, y):

    # I assume the decay has reached 90% , i.e. I subtract part of the trace
    percent_left = 0.01

    # to what level do we expect the decay to have gone?
    # e.g. percent_left = 0.1 assumes that 10% of bleachable signal is still there at the end of the measurement
    # 0.001 assumes that at the end there is almost no bleachabel signal any more, i.e. all resting fluorescence is stable

    miny, maxy = np.min(y), np.max(y)
    offset = (1 + percent_left) * miny - percent_left * maxy  # equals: np.min(y) - 0.1*(np.max(y)-np.min(y))
    # the line above fails if the signal is entirely flat - as is the case in some artificial datasets
    if offset == miny:  # i.e., miny == maxy
        return 0, 1, miny
    else:
        # y is guaranteed to be positive after offset removal (all zero case handled above)
        y = y - offset

        y_log = np.log(y)
        K, A_log = np.polyfit(t, y_log, 1)
        A = np.exp(A_log)

        return A, K, offset


# the function to be fitted in the end
def model_func(t, A, K, C):
    return A * np.exp(K * t) + C


# # debug fitlogdecay
# #create fictive time course
# A = 10
# K = -0.01
# C = 3
# length = 100
# t = np.arange(length)
# lineIn = model_func(t,A,K,C)
# lineIn = np.full((length),1000)
# #lineIn[50] = 100
# plt.plot(lineIn)
# weights = np.full((length),1)
# #test fitlogdecay
# (fittedout, opt_parms) = fitlogdecay(lineIn, weights, True, 'test')
# print(opt_parms)

def fitlogdecay(lineIn, weights, showresults=False, measurement_label=""):

    ##python help, look at:
    # https://scipython.com/book/chapter-8-scipy/examples/weighted-and-non-weighted-least-squares-fitting/


    #copy of IDL FitLogDecay
    #but in the essence, not the letter
    #lineIn is an array to fit
    #return: the fitted modelled
    #weights: same length as lineIn. 0: do not consider this value.
    # high value: point is important
    # low value:  point is not important.




#pro FitLogDecay, lineIn, fittedOut, weights, verbose ;, noConverge
#;a fitted output is given
#;Compute the fit to the function we have just defined. First, define the independent and dependent variables:
#
#common data ; necessary in order to write parameters into p structure
    ### in the python translation, parameters are not stored (yet)
#;common CFD
#;common CFDconst
#;set verbose to 1 if not explicitly stated
#IF N_PARAMS() GE 4 THEN begin
#endIF else begin
#	verbose = 1
#endElse
# replaced by keyword argument verbose=1
#Y = reform(lineIn) M reform in IDL removes empty dimensions
    y = lineIn #copy, for now, to keep close to IDL text
#X = FLOAT(INDGEN(N_elements(y)))
    t = np.arange(len(y)) #this assumes that time points are equidistant

##;nov 07, new initial estimates, follow this for python
#    A, K = fit_exp_linear(t, y, offset) #
#    print('ViewCalcData:fitlogdecay: linear fit parameters A,K are: ',A,' ', K, '. Offest is: ',offset)
#    # initial guess done without weights, without excluded values.
## A and K are the estimates

#;A = [1.0D,-0.1D,offset]	;old presets
#A = [logOffset,logdecay,offset]	;Provide an initial guess of the function's parameters.
#
#;;may 07, new approach for initial estimate - removed but kept for record
#;;a0 is offset
#;A(0) = estimate(0)
#;;a1 = (ln(Fx) - ln(a0)) / x
#;;we need the response at timepoint x.
#;fx = yfit(n_elements(y)-1)
#;vx = x(n_elements(x)-1)
#;;A(1) = (alog(fx) - alog(a(0)) ) / vx
#IF verbose THEN print, 'FitLogDecay.pro: Function estimates: ', A

#now look at the weights
#remove where weights are 0
    keep = weights != 0
    t_keep = t[keep]
    y_keep = y[keep]
    weights_keep = weights[keep]
#high weights mean important points, i.e. low variability = sigma
    sigma = 1/weights_keep

#;nov 07, new initial estimates, follow this for python
    A, K, offset = fit_exp_linear_autoOffset(t_keep, y_keep) #
    fittedout_lin = A * np.exp(K*t) + offset
    logging.getLogger("VIEW").debug(
        f'ViewCalcData:fitlogdecay: linear fit parameters A = {A}, K = {K} . Offest={offset}')
    # initial guess done without weights, but excluding excluded values.
# A and K are the estimates

# give feedback on linear fit
#    opt_parms = (A, K, offset)
#    fittedout = A * np.exp(K*t) + offset
#    if showresults: show_fitlogdecay(y, fittedout, t, weights, opt_parms)

#itMax = 1000
#yfit = CURVEFIT(X, Y, weights, A, SIGMA, FUNCTION_NAME='gfunct', ITmax=itMax, ITER=iter, status=status)
    import scipy.optimize as spo
    # Linear fit is better than exponential fit here, as y_keep is flat
    if A == 0:
        opt_parms = (A, K, offset)
    else:
        try:
            # default value of maxfev is 800, not always sufficient
            opt_parms, parm_cov = spo.curve_fit(
                model_func, t_keep, y_keep,  p0=(A,K,offset), sigma = sigma, maxfev=3200,
                # setting bounds on A, to make sure that the fitted curve does not rise/fall faster than y_keep does.
                # it helps to reduce the exponential divergence between fittedout and y for points with 0 weight.
                bounds=[
                    (min(y_keep.min() - offset, A), -np.inf, -np.inf),  # lower bounds
                    (max(y_keep.max() - offset, A), np.inf, np.inf)  # upper bounds
                ]
            )
            logging.getLogger("VIEW").debug("Fitting log function converged! Using Log fit")
        except RuntimeError as rte:
            opt_parms = (A, K, offset)
            logging.getLogger("VIEW").debug("Fitting log function did NOT converge. Using linear parameters.")




#;Compute the parameters.
#;IF ((iter gt itmax) OR (iter eq 1)) THEN noConverge=1 ELSE noConverge=0
#IF (status ge 1) THEN noConverge=1 ELSE noConverge=0
#IF verbose THEN PRINT, 'FitLogDecay.pro: Function parameters (check FitLogDecay.pro for function): ', A	;Print the parameters returned in A.
#IF noConverge THEN print, 'FitLogDecay.pro: Failed to converge, setting parameters to 0; check FitLogDecay.pro'
#
#;copy the parameters into the p structure, so it is available for later retrieval
#p1.BleachPar = A


#;IDL prints:
#;Function parameters:       9.91120    -0.100883      2.07773
#;Thus, the function that best fits the data is:
#;F(x) = 9.91120 * exp(-0.100883x) +  2.07773

    A, K, C = opt_parms
    fittedout = A * np.exp(K*t) + C
### show result
    if showresults: show_fitlogdecay(y, fittedout, fittedout_lin, t, weights, opt_parms, measurement_label)
# end function fitlogdecay
    return (fittedout, opt_parms) #, A, K, C


def show_fitlogdecay(lineIn, fittedout_blue, fittedout_green, t, weights, opt_parms, measurement_label):

    A, K, C = opt_parms #extract function parameters
    fig = plt.figure()
    fig.canvas.set_window_title(measurement_label)
    ax1 = fig.add_subplot(2,1,1) # (2,1,1)
    ax2 = fig.add_subplot(2,1,2)
    ax1.set_title('Fitlogdecay')
    ax2.set_title('weights')
    ax2.plot(t, weights, 'k--',
          label='weights')
    ax1.plot(t, lineIn, 'ro')
    ax1.plot(t, fittedout_blue, 'b-',
          label='$y = %0.2f e^{%0.2f t} + %0.2f$' % (A, K, C))
    ax1.plot(t, fittedout_green, 'g-',
          label='Alternate lin log-fit')
#    ax1.legend(bbox_to_anchor=(1, 1), fancybox=True, shadow=True)
    ax1.legend(fancybox=True, shadow=True)
    plt.show(block=False)
    # move window to the front - no idea if this works


def get_bleach_weights(
        flags, p1_metadata: pd.Series, movie_size: tuple, exclude_stimulus: bool):
    """
    Calculates weights to be used for bleach correction. Weights for the frames 0 to `end_background` are set
    flags["LELog_InitialFactor"]. If `flags["LE_BleachStartFrame"]` is > 0, frames 0 to this value is set to 0. If
    `exclude_stimulus` is True, then the weights for "stimulus frames" are set to 0, where "stimulus frames" are defined
    to be from `end_background` to `flags["LELog_ExcludeSeconds"]` seconds after the onset of first stimulus
    :param FlagsManager flags:
    :param pandas.Series p1_metadata: experimental metadata
    :param tuple movie_size: size of raw data, format XYT
    :param bool exclude_stimulus: when true, "stimulus frames" as defined above are set to have 0 weight
    :return: an array of weights
    :rtype: numpy.ndarray
    """

    n_frames = movie_size[2]
    end_background = p1_metadata.background_frames[1]
    sampling_frequency = p1_metadata.frequency

    # can't exclude stimulus if stimulus info is not provided
    exclude_stimulus = exclude_stimulus and p1_metadata.pulsed_stimuli_handler is not None

    weights = np.ones(n_frames)

    #  change weight to initial portion (with safety net)
    weights[0: end_background] = flags["LELog_InitialFactor"]

    #  exclude first frames
    bleach_start_frame = flags["LE_BleachStartFrame"]
    if bleach_start_frame > 0:
        weights[0:bleach_start_frame] = 0

    #  exclude response interval
    if exclude_stimulus:
        startweight = end_background
        endweight = min([round(end_background + flags["LELog_ExcludeSeconds"] * sampling_frequency), n_frames - 1])
        weights[startweight:endweight] = 0

    return weights