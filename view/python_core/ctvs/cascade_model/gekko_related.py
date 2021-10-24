from gekko import GEKKO
import pandas as pd
import numpy as np

# to counteract a bug in gekko: https://github.com/BYU-PRISM/GEKKO/issues/108
from subprocess import TimeoutExpired


class GekkoSolver(object):

    def __init__(self, state_variables, parameters, equations):

        self.m = GEKKO(remote=False)

        # Input, fixed and to be provided
        self.m.input = self.m.Param()

        # State Variables
        self.state_variables = {}
        for var_name in state_variables:
            exec(f"self.m.{var_name} = self.m.SV()")
            self.state_variables[var_name] = eval(f"self.m.{var_name}")

        # Parameters, fixed by default
        self.parameters = {}
        for param in parameters:
            exec(f"self.m.{param} = self.m.{self.get_param_var_type()}(0)")
            self.parameters[param] = eval(f"self.m.{param}")

        # Output
        self.m.output = self.get_output_variable()

        # Equations
        self.equations = equations
        eval(f"self.m.Equations({equations.replace('m.', 'self.m.')})")

    @classmethod
    def init_from_model(cls, model):

        state_variable_inits = model.get_state_variable_inits()
        # sampling period irrelevant as we only need the parameter names
        parameter_inits = model.get_parameter_inits(sampling_period=1)

        gm = cls(
            state_variables=state_variable_inits.keys(),
            parameters=parameter_inits.keys(),
            equations=model.get_equations()
        )

        model.extra_init_steps(gm.m)

        return gm

    def get_param_var_type(self):

        return "Const"

    def get_output_variable(self):

        return self.m.Var(fixed_initial=True)

    def solve(self, time_vec, input_vec, parameter_values, state_variable_init_dict, output_init):

        self.m.output.value = output_init[-1]

        # initialize input
        self.m.input.value = input_vec

        # initialize time
        self.m.time = time_vec

        # initialize parameters
        for param_name, param_value in parameter_values.items():
            if param_name in self.parameters:
                temp = self.parameters[param_name]
                temp.value = param_value

        # initialize state variables
        for sv_name, sv_value in state_variable_init_dict.items():
            if sv_name in self.state_variables:
                self.state_variables[sv_name].value = sv_value[-1]

        self.m.options.imode = 6  # sequential dynamic simulation

        # set timeout to 5 minutes
        self.m.options.max_time = 60

        # solve
        try:
            self.m.solve(disp=False)
        except FileNotFoundError as fnfe:
            print(fnfe)
            return None
        except Exception as e:
            poss1 = str(e).find("@error: Solution Not Found") >= 0
            poss2 = str(e).find("Time Limit Exceeded:") >= 0
            poss3 = str(e).find("NameError: name \'TimeoutExpired\' is not defined")
            if poss1 or poss2 or poss3:
                print(f"Encountered an error during function solving/fitting with GEKKO: {e}")
                return None
            else:
                raise e
        return self.m.output


class GekkoFitter(GekkoSolver):

    def __init__(self, state_variables, parameters, equations):

        super().__init__(state_variables, parameters, equations)

    def get_output_variable(self):

        return self.m.CV()

    def get_param_var_type(self):

        return "FV"

    def fit(
            self, time_vec, input_vec, output_vec, state_variable_init_dict=None, parameter_lb_init_ub=None,
            ev_type=1, dead_band=None
    ):

        # output fixed, given, to be used for estimation
        self.m.output.status = 0
        self.m.output.fstatus = 1
        self.m.output.value = output_vec

        # initialize input
        self.m.input.value = input_vec

        # initialize time
        self.m.time = time_vec

        # initialize parameters initial value, lower and upper bounds
        for param_name, param_value in parameter_lb_init_ub.items():
            if param_name in self.parameters:
                temp = self.parameters[param_name]
                temp.status = 1
                temp.fstatus = 0
                temp.lower, temp.value, temp.upper = parameter_lb_init_ub[param_name]

        # initialize state variables
        for sv_name, sv_value in state_variable_init_dict.items():
            if sv_name in self.state_variables:
                self.state_variables[sv_name].value = sv_value

        self.m.options.imode = 5  # moving horizon estimate method
        self.m.options.ev_type = ev_type
        if dead_band is not None:
            self.m.options.meas_gap = dead_band

        # set timeout to 5 minutes
        self.m.options.max_time = 60

        try:
            self.m.solve(disp=False)
        except FileNotFoundError as fnfe:
            print(fnfe)
            return None
        except Exception as e:
            poss1 = str(e).find("@error: Solution Not Found") >= 0
            poss2 = str(e).find("Time Limit Exceeded:") >= 0
            poss3 = str(e).find("name 'TimeoutExpired' is not defined") >= 0
            if poss1 or poss2 or poss3:
                print(e)
                return None
            else:
                raise e

        sv_fit_dict = pd.Series()
        sv_fit_dict["output"] = np.array(self.m.output)
        for sv_name, sv in self.state_variables.items():
            sv_fit_dict[sv_name] = np.array(sv.value)

        for param_name, param in self.parameters.items():
            sv_fit_dict[param_name] = param.value[0]

        return sv_fit_dict


class ModelOneComp(object):

    def __init__(self):

        super().__init__()

        def extra_init_steps(m):
            pass

        self.extra_init_steps = extra_init_steps

    def get_equations(self):

        return """
                [ 
                    m.A.dt() == - m.A / m.kA + m.input,
                    m.F.dt() == - m.F / m.kF + m.kAF * m.A,
                    m.output == m.F
                    ]
                """

    def get_state_variable_inits(self):
        return {"F": 0, "A": 0}

    def get_parameter_inits(self, sampling_period):

        return {
                "kF": np.array([0.01, 20, 200]) * sampling_period,
                "kAF": np.array([1e-3, 1, 200]) * sampling_period,
                "kA": np.array([0.01, 1, 200]) * sampling_period,
                }


class ModelTwoCompNoDelay(ModelOneComp):

    def __init__(self, param_inits=None, params_fixed=None):

        super().__init__()

        self.param_inits = param_inits
        self.params_fixed = params_fixed

        def f(m):
            pass
        self.extra_init_steps = f

    def get_equations(self):
        return """
                [ 
                    m.A.dt() == - m.A / m.kA + m.input,
                    m.F.dt() == - m.F / m.kF + m.kAF * m.A,
                    m.S.dt() == - m.S / m.kS - m.kAS * m.A,
                    m.output == m.F + m.S,
                    m.kS > m.kF
                    ]
                """

    def get_state_variable_inits(self):
        temp = super().get_state_variable_inits()
        temp.update({"S": 0})
        return temp

    def get_parameter_inits(self, sampling_period):
        temp = super().get_parameter_inits(sampling_period)
        temp.update(
            {
                "kS": np.array([1, 100, 200]) * sampling_period,
                "kAS": np.array([-200, 1, 200]) * sampling_period
            })
        if self.param_inits is not None:
            for k, v in self.param_inits.items():
                if k in temp:
                    temp[k][1] = v    # use specified value as starting point

        if self.params_fixed is not None:
            for k, v in self.params_fixed.items():
                if k in temp:
                    temp[k] = v  # use specified starting points and limits

        return temp


class ModelTwoComp(ModelTwoCompNoDelay):

    def __init__(self, delay, param_inits=None, params_fixed=None):

        super().__init__(param_inits=param_inits, params_fixed=params_fixed)
        self.delay = delay

        def extra_init_steps(m):
            if delay > 0:
                m.delay(m.A, m.A_delayed, delay)

        self.extra_init_steps = extra_init_steps

    def get_equations(self):
        return """
                [ 
                    m.A.dt() == - m.A / m.kA + m.input,
                    m.F.dt() == - m.F / m.kF + m.kAF * m.A,
                    m.S.dt() == - m.S / m.kS - m.kAS * m.A_delayed,
                    m.output == m.F + m.S,
                    m.kS > m.kF
                    ]
                """

    def get_state_variable_inits(self):
        temp = super().get_state_variable_inits()
        temp.update({"A_delayed": 0})
        return temp


def fit_compare_models(time_vec, output_vec, model2consider, input_vec=None, dead_band=None):
    """
    Fits output_vec and time_vec to the multiple models and returns the paramters of the best model fit
    based on AIC. Loosely based on
    "Temporal Responses of C. elegans Chemosensory Neurons Are Preserved in Behavioral Dynamics"
    # https://doi.org/10.1016/j.neuron.2013.11.020, Figure 3
    :param Sequence time_vec: time values
    :param Sequence output_vec: ca response values
    :param model2consider: object of either ModelOneComp or ModelTwoComp
    :param Sequence input_vec: input values, with maximum scaled to 1
    See https://gekko.readthedocs.io/en/latest/global.html#ev-type
    :param dead_band: noise half band-width of output signal. Fitting cost in this band will be 0.
    See https://gekko.readthedocs.io/en/latest/tuning_params.html#meas-gap
    :return:
    """

    sampling_period = time_vec[1] - time_vec[0]

    output_vec = np.asarray(output_vec)

    gm = GekkoFitter.init_from_model(model=model2consider)

    state_variable_inits = model2consider.get_state_variable_inits()
    parameter_inits = model2consider.get_parameter_inits(sampling_period=sampling_period)

    fit_params = gm.fit(
        time_vec=time_vec.copy(), input_vec=input_vec.copy(), output_vec=output_vec.copy(),
        state_variable_init_dict=state_variable_inits,
        parameter_lb_init_ub=parameter_inits,
        ev_type=2, dead_band=dead_band
    )

    if fit_params is not None:

        # residual sum of squares
        rss = np.power(output_vec - fit_params["output"], 2).sum()

        # definition from https://en.wikipedia.org/wiki/Bayesian_information_criterion
        n = output_vec.shape[0]
        k = len(parameter_inits)
        bic = n * np.log(rss / n) + k * np.log(n)

        fit_params["model_params"] = list(parameter_inits.keys())
        fit_params["model_name"] = model2consider.__class__.__name__
        fit_params["model"] = model2consider
        fit_params["bic"] = bic

        fit_params["stimulus_trace_fitted"] = input_vec
        fit_params["output_trace_expected"] = output_vec
        fit_params["time_trace_fitted"] = time_vec

    return fit_params

    # if len(bics):
    #     best_model_ind = np.argmin(bics)
    #
    #     return \
    #         fit_params_all[best_model_ind], gms_all[best_model_ind], \
    #         {f"{model.__class__.__name__};bic={bic:2.3g}": fit_params["output"]
    #          for model, fit_params, bic in zip(models_to_consider, fit_params_all, bics)}
    # else:
    #     return None, None, None
