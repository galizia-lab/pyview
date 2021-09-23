import pandas as pd
import view.python_core.p1_class.metadata_related as metadata_related


class StimuliParams(pd.DataFrame):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def iter_stimuli(self):

        return self.iterrows()


class StimuliParamsParser(object):

    def __init__(self):

        self.param_def_df = pd.DataFrame()
        self.param_def_df["column_name"] = ["StimON", "StimOFF", "StimONms", "StimLen", "Odour", "OConc"]
        self.param_def_df["expected_type"] = [int,     int,       float,      int,       str,     float]
        self.param_def_df["second_stim"] = ["Stim2ON", "Stim2OFF", "Stim2ONms", "Stim2Len", "Odour", "OConc"]

        self.param_def_df.set_index("column_name", inplace=True)

        self.metadata_def = metadata_related.MetadataDefinition()

    def get_specified_unspecified_params(self, row: pd.Series):

        specified_params = []
        unspecified_params = []

        for column_name in self.param_def_df.index.values:
            if column_name in row:
                if self.metadata_def.is_value_default(column_name, row[column_name]):
                    unspecified_params.append(column_name)
                else:
                    specified_params.append(column_name)

        return specified_params, unspecified_params

    def parse_row(self, row: pd.Series):

        specified_params, unspecified_params = self.get_specified_unspecified_params(row)

        if len(specified_params) == 0:

            return StimuliParams()

        else:

            # count the number of commas in each entry
            commas_per_specified_param = {x: row[x].count(",") if type(row[x]) is str else 0
                                          for x in specified_params}

            # infer the number of stimuli
            n_stim = max(commas_per_specified_param.values()) + 1

            # ensure that each specified parameter either has one entry or <n_stim> number of entries
            assert all(x in (n_stim - 1, 0) for x in commas_per_specified_param.values()), \
                "Some stimulus parameters have more than one entry and these parameters are not equal in number"

            # initialize a data frame with param names as columns and stimuli number as indices
            param_values = StimuliParams(columns=self.param_def_df.index,
                                         index=pd.RangeIndex(0, n_stim, 1), dtype=object)

            # fill all unspecified parameters with None
            param_values.loc[:, unspecified_params] = None

            # fill specified parameters, duplicating where necessary
            for specified_param, n_commas in commas_per_specified_param.items():

                # for all entries with atleast one comma
                if (n_commas == n_stim - 1) and (n_stim > 1):
                    param_values.loc[:, specified_param] \
                        = [self._parse_comma_separated_entry(specified_param, x.replace(" ", ""))
                            for x in row[specified_param].split(',')]
                else:
                    param_values.loc[:, specified_param] \
                        = self._parse_comma_separated_entry(specified_param, row[specified_param])

            # when stimuli parameter entries have no commas, add parameters for second stimulus from
            # entries of STIM2ON etc, if they have been specified
            if n_stim == 1:

                second_param_values = {}
                for param_name, second_param_name in self.param_def_df["second_stim"].items():
                    if not self.metadata_def.is_value_default(second_param_name, row[second_param_name]):
                        second_param_values[param_name] \
                            = self._parse_comma_separated_entry(param_name, row[second_param_name])
                    else:
                        second_param_values[param_name] = None

                # only when at least one of the four parameters starting with "Stim" are specified
                if any(v is not None for k, v in second_param_values.items() if k.startswith("Stim")):

                    param_values_new = StimuliParams(columns=self.param_def_df.index,
                                                     index=pd.RangeIndex(0, 2, 1), dtype=object)
                    param_values_new.loc[0, :] = param_values.loc[0, :]
                    for param_name, second_param_value in second_param_values.items():
                        param_values_new.loc[1, param_name] = second_param_value

                    param_values = param_values_new

            return param_values

    def _parse_comma_separated_entry(self, param_name, param_value):

        expected_type = self.param_def_df.loc[param_name, "expected_type"]

        if param_value == '' or pd.isnull(param_value):
            return None
        else:
            try:
                return expected_type(param_value)
            except ValueError as ve:
                raise ValueError(
                    f"Could not interpret '{param_value}' in the column '{param_name}' as an {expected_type}."
                )






