"""
References:
    1. Kato, S. et al., 2014.
        “Temporal Responses of C.elegans Chemosensory Neurons Are Preserved in Behavioral Dynamics.” Neuron, 81(3),
        pp.616–628. Available at: http://dx.doi.org/10.1016/j.neuron.2013.11.020.
"""
import shutil
import tempfile
from typing import Sequence
import numpy as np
import math
import pandas as pd
from scipy.interpolate import interp1d
import pathlib as pl

from view.python_core.ctvs.cascade_model.gekko_related import fit_compare_models, GekkoSolver, ModelOneComp, \
    ModelTwoComp, ModelTwoCompNoDelay


def estimate_delay_rising_phase_only(stimulus_trace: Sequence[float], output_trace: Sequence[float]):
    """
    Estimate delay between the signals <input> and <output> using a cross correlation and only those points with
    positive derivative
    :param Sequence stimulus_trace: sequence of floats
    :param Sequence output_trace: sequence of floats
    :return: delay (number of samples)
    :rtype: int
    """

    stimulus_trace_non_rising_mask = (np.diff(stimulus_trace) <= 0).tolist() + [False]
    stim_min, stim_max = min(stimulus_trace), max(stimulus_trace)
    stimulus_trace_copy = np.array(stimulus_trace, copy=True)
    stimulus_trace_copy[stimulus_trace_non_rising_mask] = np.median(stimulus_trace)
    stimulus_trace_copy[stimulus_trace_copy >= stim_min + 0.85 * (stim_max - stim_min)] = np.median(stimulus_trace)

    output_trace_non_rising_mask = (np.diff(output_trace) <= 0).tolist() + [False]
    output_min, output_max = min(output_trace), max(output_trace)
    output_trace_copy = np.array(output_trace, copy=True)
    output_trace_copy[output_trace_non_rising_mask] = np.median(output_trace)
    output_trace_copy[output_trace_copy >= output_min + 0.85 * (output_max - output_min)] = np.median(output_trace)

    corr = np.correlate(stimulus_trace_copy, output_trace_copy, "full")

    delay_estimated = np.argmax(corr) - stimulus_trace_copy.shape[0] + 1

    # # code for debugging starts here
    # from matplotlib import pyplot as plt
    # plt.ion()
    # fig, axs = plt.subplots(nrows=3, figsize=(10, 8), squeeze=True)
    # axs[0].plot(stimulus_trace, 'b-')
    # axs[0].plot(stimulus_trace_copy, "r-o")
    # axs[0].set_ylabel("Stimulus")
    #
    # axs[1].plot(output_trace, 'b-')
    # axs[1].plot(output_trace_copy, "r-o")
    # axs[1].set_ylabel("Response")
    #
    # axs[2].plot(corr, "b-")
    # axs[2].axvline(np.argmax(corr), color='r')
    # axs[2].set_ylabel("Correlation")
    # axs[2].set_title(f"Estimated delay in samples: {delay_estimated}")
    #
    # plt.draw()
    # input("Press any key to continue..")
    # plt.close()
    # # code for debugging ends here

    return delay_estimated


def predict_into_future(fit_params, factor):

    output = factor * fit_params["output"]
    trace = np.array(output)
    n_pts = trace.shape[0]
    time_trace = fit_params["time_trace_fitted"]
    sampling_period = time_trace[1] - time_trace[0]

    stimulus_trace = np.array(fit_params["stimulus_trace_fitted"])
    stimulus_peak_pos = np.argmax(stimulus_trace)

    central_part_start = max(0, int(stimulus_peak_pos - 0.25 * n_pts))
    central_part_end = min(n_pts, int(stimulus_peak_pos + 0.25 * n_pts))
    central_part = trace[central_part_start: central_part_end + 1]

    max_pos = central_part.argmax() + central_part_start

    prediction_start = time_trace[-2]
    longest_time_constant = fit_params["kF"] + fit_params['kA']
    if "kS" in fit_params:
        longest_time_constant = max(fit_params["kS"], longest_time_constant)
    prediction_end = time_trace[max_pos] + 6 * longest_time_constant  # units is seconds

    predicted_trace = None
    if prediction_end > prediction_start:
        prediction_time_trace = np.arange(prediction_start, prediction_end + sampling_period, sampling_period)

        gs = GekkoSolver.init_from_model(fit_params["model"])
        predicted_traces_dict = gs.solve(
            time_vec=prediction_time_trace,
            input_vec=np.zeros_like(prediction_time_trace),
            parameter_values={k: fit_params[k] for k in gs.parameters},
            state_variable_init_dict={k: fit_params[k][-2:] for k in gs.state_variables},
            output_init=output[-2:]
        )
        predicted_trace = predicted_traces_dict["output"]

    predicted_trace_no_overlap = None
    predicted_time_trace_no_overlap = None
    if predicted_trace is not None:
        if predicted_trace[-1] <= predicted_trace[-2]:
            predicted_trace_no_overlap = np.array(predicted_trace)[1:] * factor
            predicted_time_trace_no_overlap = np.array(prediction_time_trace)[1:]

    return predicted_trace_no_overlap, predicted_time_trace_no_overlap


def fit_cascade_model(
        stimulus_trace, output_trace, time_trace, delays_to_test=np.arange(-15, 9, 1).astype(int)
):

    stimulus_trace = np.array(stimulus_trace)
    output_trace = np.array(output_trace)
    time_trace = np.array(time_trace)

    assert stimulus_trace.shape == output_trace.shape, "Stimulus and output traces have different shapes"
    assert time_trace.shape == output_trace.shape, "time trace and output trace have different shapes"

    sampling_period = time_trace[1] - time_trace[0]

    pcc = PrelimChunkClassifier(output_trace)
    factor = 1 if pcc.is_chunk_response_positive() else -1

    bics = []
    fit_params_all = []
    model_one_comp = ModelOneComp()

    for delay in delays_to_test:

        if delay > 0:
            output_trace_to_fit = output_trace[:-delay]
            stimulus_trace_to_fit = stimulus_trace[delay:]
            time_trace_to_fit = time_trace[delay:]
        else:
            output_trace_to_fit = output_trace[-delay:]
            stimulus_trace_to_fit = stimulus_trace[:stimulus_trace.shape[0] + delay]
            time_trace_to_fit = time_trace[:time_trace.shape[0] + delay]

        fit_params = fit_compare_models(
            time_vec=time_trace_to_fit,
            input_vec=stimulus_trace_to_fit, output_vec=factor * output_trace_to_fit,
            model2consider=model_one_comp
        )

        if fit_params is not None:
            fit_params["output"] = factor * fit_params["output"]
            fit_params["output_trace_expected"] = factor * fit_params["output_trace_expected"]

            fit_params_all.append(fit_params)
            bics.append(fit_params["bic"])

    if len(fit_params_all) == 0:
        return None
    else:
        best_ind = np.argmin(bics)
        fit_params_best_one_comp = fit_params_all[best_ind]
        delay_best = delays_to_test[best_ind]
        fit_params_best_one_comp["delay_input"] = delay_best * sampling_period
        cascade_model_output = dict(
            fit_params_one_comp=fit_params_best_one_comp
        )

        fit_params_all_second = []
        bics_second = []

        params_fixed = ["kA"]

        models_to_fit = []

        param_fixed_arg = {k: [fit_params_best_one_comp[k]] * 3 for k in params_fixed}
        param_fixed_arg["kF"] = [
            fit_params_best_one_comp["kF"] * 0.5,
            fit_params_best_one_comp["kF"],
            1.5 * fit_params_best_one_comp["kF"]]
        param_inits = {
            k: fit_params_best_one_comp[k]
            for k in fit_params_best_one_comp["model_params"] if k not in param_fixed_arg}

        model_two_comp_no_delay = ModelTwoCompNoDelay(
            param_inits=param_inits,
            params_fixed=param_fixed_arg)

        models_to_fit.append(model_two_comp_no_delay)

        second_comp_delays = list(range(0, 20))
        for second_comp_delay in second_comp_delays[1:]:

            model_two_comp = ModelTwoComp(
                delay=second_comp_delay,
                param_inits=param_inits,
                params_fixed=param_fixed_arg
            )

            models_to_fit.append(model_two_comp)

        for model2fit, second_comp_delay in zip(models_to_fit, second_comp_delays):

            fit_params = fit_compare_models(
                time_vec=fit_params_best_one_comp["time_trace_fitted"],
                input_vec=fit_params_best_one_comp["stimulus_trace_fitted"],
                output_vec=factor * fit_params_best_one_comp["output_trace_expected"],
                model2consider=model2fit
            )

            if fit_params is not None:
                fit_params["output"] = factor * fit_params["output"]
                fit_params["output_trace_expected"] = factor * fit_params["output_trace_expected"]
                fit_params_all_second.append(fit_params)
                bics_second.append(fit_params["bic"])

        best_ind = None
        if len(fit_params_all):

            best_ind = np.argmin(bics_second)

            fit_params_best_two_comp = fit_params_all_second[best_ind]
            fit_params_best_two_comp["delay_second_comp"] = second_comp_delays[best_ind]
            cascade_model_output["fit_params_two_comp"] = fit_params_best_two_comp

            # https://imaging.mrc-cbu.cam.ac.uk/statswiki/FAQ/AICreg
            # difference of 50 chosen based fitting on a test set
            if fit_params_all_second[best_ind]["bic"] >= fit_params_best_one_comp["bic"] - 50:
                best_ind = None

        if best_ind is None:
            fit_params_best = fit_params_best_one_comp
        else:
            fit_params_best = fit_params_all_second[best_ind]

        predicted_trace, predicted_time_trace = predict_into_future(fit_params_best, factor)

        cascade_model_output.update(dict(
            sign_factor=factor, fit_params=fit_params_best,
            predicted_time_trace=predicted_time_trace, predicted_trace=predicted_trace
        ))

        tempdir = pl.Path(tempfile.gettempdir())
        for child in tempdir.iterdir():
            if child.is_dir() and child.name.startswith("tmp"):
                shutil.rmtree(child)

        return cascade_model_output


class PrelimChunkClassifier(object):

    def __init__(self, chunk: Sequence[float]):

        self.chunk = np.asarray(chunk)
        self.chunk_abs = np.abs(chunk)
        self.chunk_abs_argmax = np.argmax(self.chunk_abs)

    def is_chunk_contaminated(self):

        # is the maximum of absolute values of chunk in its middle half?
        lower_limit = 0.25 * self.chunk.shape[0]
        upper_limit = 0.75 * self.chunk.shape[0]
        return not (lower_limit <= self.chunk_abs_argmax <= upper_limit)

    def is_chunk_response_positive(self):

        # is the maximum value of the chunk positive?
        return self.chunk[self.chunk_abs_argmax] > 0
