'''
(explanation as of Sept. 4th, 2019. Code by Ajay)

p1 structure contains all parameters of an experiment that are
part of this particular measurement
e.g. image size, frame rate, stimulus times, etc.

this information comes from the imaging equipment (e.g. frame rate in Till .log file)
or from other equipment (e.g. odorant name in PAL bar-code reader)
or from the user (e.g. stimulus time or the like).
All this information has been collected prior to analysis in a file,
where each line/row is one measurement.
These are the .lst OR .settings files (.xls, or .csv, or tab-delimited...)
There is one .lst file for every animal.

For historical reasons, the same variable may have a different name in .settings,
.lst or p1.

the full list of allowed variables and their names is in metadata_definition.csv
e.g. ... Code/git_repos/VIEW/view/flags_and_metadata_definitions/metadata_definition.csv

The current format of p1 is implemented as a class in python_core/measurement_list/__init__.py:
    MeasurementList.
    In particular, this is used to extract p1 values for a particular measurement.
stimuli.py contains the tools to adjust p1 values related to stimulus timing.

'''
import re

from view.python_core.get_internal_files import get_metadata_definition
from view.python_core.paths import get_existing_raw_data_filename, convert_to_path_for_current_os
from view.python_core.p1_class.metadata_related import parse_p1_metadata_from_measurement_list_row
from ..p1_class import get_p1
import pandas as pd
import numpy as np
import pathlib as pl
from .io import get_ext_based_values
from .importers import get_importer_class
from view.python_core.old_file_handler import get_old_file_handler
import typing
import logging
import copy
import pprint


class MeasurementList(object):

    def __init__(self, LE_loadExp):

        self._metadata_def_df = get_metadata_definition()
        self.LE_loadExp = LE_loadExp
        self.measurement_list_df = None
        self.last_measurement_list_fle = None
        self.animal_name = None

    def get_column_mapping(self, from_col=None, to_col=None):
        """
        Return a dictionary with column names of <from_col> as keys and corresponding column names of <to_col> as values.
        If one of them is set to None, the internal column names are used. Both cannot be None.
        :param from_col: str or None
        :param to_col: str or None
        :return: dict
        """

        assert not (from_col is None and to_col is None), "One of 'from_col' and 'to_col' needs to be specified!"

        if from_col is None:

            from_col = "LST Name"

        if to_col is None:

            to_col = "LST Name"

        metadata_reset = self._metadata_def_df.reset_index()

        if from_col == to_col == "LST Name":
            return {k: k for k in metadata_reset["LST Name"]}
        else:
            temp_df = metadata_reset.set_index(from_col)
            return dict(temp_df[to_col])

    @classmethod
    def create_from_lst_file(cls, lst_fle: str, LE_loadExp: int):
        """
        Creates an empty MeasurementList object, reads values from a list file and and initializes the MeasurementList
        object with values read
        :param lst_fle: str, containing the path of a measurement list file
        :param LE_loadExp: int, the LE_loadExp flag of VIEW
        :return: MeasurementList object
        """

        measurement_list = cls(LE_loadExp)

        io_class, relevant_column, ext = get_ext_based_values(lst_fle)

        measurement_list.last_measurement_list_fle = lst_fle
        measurement_list.animal_name = pl.Path(lst_fle).name[:-len(ext)]

        in_df = io_class.read(lst_fle)

        column_name_mapping = measurement_list.get_column_mapping(from_col=relevant_column, to_col=None)

        in_df_lst_names = in_df.rename(columns=column_name_mapping)

        # define a new column order where columns known to VIEW are moved to the beginning
        new_column_order = \
            [column_name_mapping[x] for x in in_df.columns if x in column_name_mapping] + \
            [x for x in in_df.columns if x not in column_name_mapping]

        # reorder columns to resemble the row order in the internal metadata definition file
        # columns not internal definition will be at the end
        in_df_reordered = in_df_lst_names[new_column_order]

        measurement_list.measurement_list_df = in_df_reordered

        measurement_list.revise_dbbs_for_current_OS()
        measurement_list.add_missing_defaults()
        measurement_list.convert_to_numeric()
        measurement_list.check_minimum_requirements()

        return measurement_list

    @classmethod
    def create_from_df(cls, LE_loadExp, df):

        measurement_list = cls(LE_loadExp)

        measurement_list.measurement_list_df = df
        measurement_list.convert_to_numeric()
        measurement_list.check_minimum_requirements()

        return measurement_list

    def write_to_list_file(self, lst_fle: str, columns2write: typing.Union[None, list] = None,
                           overwrite_old_values=()):
        """
        Write to file with column names based on file extension
        :param lst_fle: str, path of the file to be written
        :param columns2write: list or None, the columns 2 write. The written file will have the same column order as
        <columns2write>. If None, all columns are used and written in no particular order.
        :param overwrite_old_values: iterable of strings or None, names of columns of the list file to be written whose
        values are to be overwritten from a file of the same name, if it exists. If None, file is not backed up
        :return: None
        """

        io_class, relevant_column, _ = get_ext_based_values(lst_fle)

        old_file_handler = get_old_file_handler(lst_fle)

        old_file_handler.backup()

        column_name_mapping = self.get_column_mapping(to_col=relevant_column)
        df_to_write = self.measurement_list_df.rename(columns=column_name_mapping)

        # rewrite values from old df
        df_with_old_values = old_file_handler.write_old_values(df_to_write, overwrite_old_values,
                                                               measu_col_name=column_name_mapping["Measu"],
                                                               label_col_name=column_name_mapping["Label"])

        # use all columns if <columns2write> is None
        if columns2write is None:
            columns2write = df_to_write.columns.values

        # add those columns to <columns2write> that exist additionally in <df_with_old_values>
        columns2write = list(columns2write)
        for column2overwrite in df_with_old_values.columns.values:
            if column2overwrite not in columns2write:
                columns2write.append(column2overwrite)

        # reorder / limits columns of <df_with_old_values> based on <columns2write>
        df_with_old_values = df_with_old_values.reindex(columns=columns2write)

        io_class.write(df=df_with_old_values, fle=lst_fle)

    def write_to_lst_file_cross_format(self, output_lst_file: str, backup_current_file: bool=True):
        """
        Writes the current measurement list to another format, based on the extension of <output_lst_file>.
        :param str output_lst_file: path where output will be written
        :param bool backup_current_file: if True, and this MeasurementList object was loaded from a file, that file
        will be backed up
        """

        io_class_output, = get_ext_based_values(output_lst_file)

        if backup_current_file:

            old_file_handler = get_old_file_handler(self.last_measurement_list_fle)
            old_file_handler.backup()

        io_class_output.write(df=self.measurement_list_df, fle=output_lst_file)

    def get_minimum_columns_required(self):

        return [k for k, v in self._metadata_def_df["Requirement for List load"].items()
                if v in ["all", str(self.LE_loadExp)]]

    def check_minimum_requirements(self):

        minimum_columns_required = self.get_minimum_columns_required()
        missing_columns = set(minimum_columns_required) - set(self.measurement_list_df.columns)
        assert missing_columns == set(), f"These columns are required but were not found in the list file: " \
            f"{missing_columns}"

    def add_missing_defaults(self):

        for col_name, default_value in self._metadata_def_df["Default values"].items():

            if col_name not in self.measurement_list_df.columns:

                self.measurement_list_df = self.measurement_list_df.reindex(self.measurement_list_df.columns.tolist() + [col_name], axis=1)
#creating column first avoids giving a warning in the next line: A value is trying to be set on a copy of a slice from a DataFrame
                self.measurement_list_df.loc[:, col_name] = default_value 
                
    def convert_to_numeric(self):
        self.measurement_list_df = \
            self.measurement_list_df.applymap(lambda x: pd.to_numeric(x, errors="ignore"))

    def revise_dbbs_for_current_OS(self):

        for row_ind, row in self.measurement_list_df.iterrows():

            for k, v in self.get_metadata_by_type(measurement_row=row, tpye="paths").items():

                self.measurement_list_df.loc[row_ind, k] = convert_to_path_for_current_os(v)

    def get_df_from_file(self, fle):
        pass


    def get_row_by_measu(self, measu):

        return self.get_row_by_column_value(column_name="Measu", column_value=measu)

    def get_row_by_label(self, label):

        return self.get_row_by_column_value(column_name="Label", column_value=label)

    def get_row_index_by_column_value(self, column_name, column_value):

        rows_mask = self.measurement_list_df[column_name].apply(lambda x: x == column_value)

        assert not sum(rows_mask) > 1, f"More than one rows found in {self.last_measurement_list_fle} with " \
                                       f"{column_name}={column_value}"
        assert not sum(rows_mask) == 0, f"No rows with {column_name}={column_value} " \
                                        f"found in {self.last_measurement_list_fle}"

        row_index = np.where(rows_mask.values)[0][0]
        return row_index

    def get_row_by_column_value(self, column_name, column_value):

        row_index = self.get_row_index_by_column_value(column_name, column_value)

        return self.get_row_by_index(row_index)

    def get_row_by_index(self, index):

        assert index in range(self.measurement_list_df.shape[0]), \
            f"Index={index} out of range for {self.last_measurement_list_fle} " \
            f"containing {self.measurement_list_df.shape[0]} rows"

        return self.measurement_list_df.iloc[index, :]

    def get_metadata_by_type(self, measurement_row, tpye):

        metadata_subset = self._metadata_def_df["Type"].apply(lambda x: x == tpye)

        return {ind: measurement_row[ind] for ind, val in metadata_subset.items() if val and ind in measurement_row}

    def get_p1_metadata_by_index(self, index):

        selected_row = self.get_row_by_index(index)

        return parse_p1_metadata_from_measurement_list_row(selected_row)

    def get_p1_metadata_by_measu(self, measu):

        selected_row = self.get_row_by_measu(measu)

        return parse_p1_metadata_from_measurement_list_row(selected_row)

    def get_p1_metadata_by_label(self, label):

        selected_row = self.get_row_by_label(label)

        return parse_p1_metadata_from_measurement_list_row(selected_row)

    def get_measus(self, analyze_values_accepted=None):
        """
        Returns those measus that have a value in the column 'Analyze' from among those in <analyze_values_accepted>.
        If <analyze_values_accepted> is None, then all measus for the animal are returned
        :param analyze_values_accepted: iterable
        :return: list of int
        """

        if analyze_values_accepted is None:
            return self.measurement_list_df["Measu"].values.tolist()
        else:
            analyse_col = self.measurement_list_df["Analyze"].values

            row_filter = [x in analyze_values_accepted for x in analyse_col]

            return self.measurement_list_df.loc[row_filter, "Measu"].values.tolist()

    def sub_select_based_on_analyze(self, analyze_values_accepted=None):
        """
        Returns a measurement list object with only those rows that have 'Analyze' values from among those in
        <analyze_values_accepted>. If <analyze_values_accepted> is None, returns a copy of self
        :param analyze_values_accepted: iterable
        :return: MeasurementList object
        """

        if analyze_values_accepted is None:
            return copy.deepcopy(self)
        else:
            analyse_col = self.measurement_list_df["Analyze"].values

            row_filter = [x in analyze_values_accepted for x in analyse_col]

            list2return = MeasurementList(self.LE_loadExp)
            list2return.measurement_list_df = self.measurement_list_df.loc[row_filter, :].copy()
            list2return.last_measurement_list_fle = self.last_measurement_list_fle

            return list2return

    def get_last_measurement_list_path(self):

        return pl.Path(self.last_measurement_list_fle)

    def get_STG_ReportTag(self):

        current_fle_path = self.get_last_measurement_list_path()

        if "." in current_fle_path.name:
            return current_fle_path.name.split(".")[0]
        else:
            return current_fle_path.name

    def get_STG_OdorInfoPath(self):

        current_fle_path = self.get_last_measurement_list_path()

        return current_fle_path.parent

    def update_metadata_of_measurement(self, measu: int, metadata2update: dict):
        """
        In the row for the measurement <measu>, replaces values of those cells whose names are keys
        in <meatadata2update> with corresponding dictionary values
        :param measu: int
        :param metadata2update: dict, whose keys are strings
        """

        measu_row_ind = self.get_row_index_by_column_value(column_name="Measu", column_value=measu)
        measu_index_value = self.measurement_list_df.index.values[measu_row_ind]

        for column_name, column_value in metadata2update.items():
            if column_name in self.measurement_list_df.columns:
                self.measurement_list_df.loc[measu_index_value, column_name] = column_value

    def get_value(self, measu, column):
        """
        Returns the value in the column <column> for the row with measu <measu>
        :param measu: int
        :param column: str
        """

        measu_row_ind = self.get_row_index_by_column_value(column_name="Measu", column_value=measu)
        measu_index_value = self.measurement_list_df.index.values[measu_row_ind]

        return self.measurement_list_df.loc[measu_index_value, column]

    def update_from_custom_func(self, custom_func, **kwargs):
        """
        update measurement list using custom function. This function is expected to take on argument: one row of the
        measurement list as a pandas.Series object and return a pandas.Series object. Ideally the index of the returned
        pandas.Series object must be a superset of the index of the input pandas.Series. In that case, the net effect
        would be to modify some columns and add other to the measurement list, as defined in <custom_func>.
        :param custom_func: a function, taking one pandas.Series object and returning a pandas.Series object
        :param kwargs: dictionary, whose key-value pairs will be passed onto 'custom_func' as arguments
        :return: None
        """

        self.measurement_list_df = self.measurement_list_df.apply(custom_func, axis=1,
                                                                  **kwargs)

    def check_set_analyze(self, loading_criterion_pass, index):
        """
        If <loading_criterion_pass> is false, sets unconditionally "Analyze" for the row at <index> to 0.
        If <loading_criterion_pass> is true, sets "Analyze" for the the row at <index> to 1 only if the column
        "Analyze" does not exist or has been set to a negative value
        :param bool loading_criterion_pass: a criterion
        :param int index: row index
        """

        analyze_column_exists = "Analyze" in self.measurement_list_df.columns.values

        if loading_criterion_pass and not analyze_column_exists:
            self.measurement_list_df.loc[index, "Analyze"] = 1
        elif loading_criterion_pass and analyze_column_exists:
            current_analyze = self.measurement_list_df.loc[index, "Analyze"]
            if current_analyze < 0 or pd.isnull(current_analyze):
                self.measurement_list_df.loc[index, "Analyze"] = 1
            else:
                pass  # do nothing
        elif not loading_criterion_pass:
            self.measurement_list_df.loc[index, "Analyze"] = 0
        else:
            pass  # should not come here as all possible cases are covered above

    def sanitize(self, data_file_extensions, STG_Datapath=None, flags=None, make_paths_absolute=False):
        """
        For each, set analyze to zero if indicated data files or their possible alternatives don't exist
        :param flags: instance of view.python_core.flags.FlagsManager
        :param STG_Datapath: str, either flags are specified or this argument, retained for backward compatibility
        :param data_file_extensions: list of str, extensions of the data file expected.
        :param make_paths_absolute: bool, if True, all data file paths found on file system wil be expanded to their
        absolute paths
        """

        which_data_cols = ["DBB1"]
        minimum_requirements = self.get_minimum_columns_required()
        extra_cols = [x for x in ("dbb2", "dbb3") if x in minimum_requirements]

        for index, row in self.measurement_list_df.iterrows():

            this_which_data_cols = which_data_cols.copy()
            for col in extra_cols:
                if col in self.measurement_list_df.columns:
                    if self.measurement_list_df.loc[index, col] != self._metadata_def_df.loc[col, "Default values"]:
                        this_which_data_cols.append(col)

            existences = []
            warnings = {}
            for data_col in this_which_data_cols:
                if STG_Datapath is None and flags is not None:
                    try:
                        dbb = row[data_col]
                        absolute_data_path = get_existing_raw_data_filename(flags=flags, dbb=dbb,
                                                                            extensions=data_file_extensions,
                                                                            )
                        if make_paths_absolute:
                            self.measurement_list_df.loc[index, data_col] = absolute_data_path

                        existences.append(True)
                    except FileNotFoundError as fnfe:
                        logging.getLogger("VIEW").warning(str(fnfe))
                        existences.append(False)
                elif flags is None and STG_Datapath is not None:
                    expected_data_file = pl.Path(STG_Datapath) / f"{row[data_col]}{data_file_extensions}"
                    existence = expected_data_file.is_file()
                    if existence:
                        if make_paths_absolute:
                            self.measurement_list_df.loc[index, data_col] = expected_data_file
                    else:
                        warnings[data_col] = f"Expected file not found: {expected_data_file}"

                    existences.append(existence)
                else:
                    raise ValueError("This function has invalid arguments. Exactly one among STG_Datapath and"
                                     "flags need to be set and the other not set or set to None")

            self.check_set_analyze(loading_criterion_pass=all(existences), index=index)
            if not all(existences):
                logging.getLogger("VIEW").warning(
                    f"Some expected data files were not found for the measurement with "
                    f"measu={self.measurement_list_df.loc[index, 'Measu']} and "
                    f"label={self.measurement_list_df.loc[index, 'Label']}. 'Analyze' for this row "
                    f"has been set to 0. I looked for:\n"
                    f"{pprint.pformat(warnings)}")

    def sanitize_based_on_loading(self, flags):
        """
        Try to load measurement of each row, if unsuccessful, set Analyze=0
        :param FlagsManager flags:
        """

        for index, row in self.measurement_list_df.iterrows():

            measu = row["Measu"]
            try:
                self.load_data(flags=flags, measu=measu)
                self.check_set_analyze(loading_criterion_pass=True, index=index)
            except (IOError, FileNotFoundError, AssertionError, ValueError):
                self.measurement_list_df.loc[index, "Analyze"] = 0

    def append(self, measurement_list, label_suffix: str = None):
        """
        Creates a new measurement label by appending <measurement_list> to self. Measus are updated to avoid
        duplication. If <label_suffix> is not None, it is appended to each entry in the column "Label"
        of <measurement_list> before appending it to self.
        :param measurement_list: MeasurementList object, to be appended
        :param label_suffix: str, see function description
        :return: MeasurementList Object
        """

        if self.LE_loadExp == measurement_list.LE_loadExp:

            new_ml = MeasurementList(self.LE_loadExp)

        else:

            new_ml = MeasurementList(None)

        max_measu_current_ml = self.measurement_list_df["Measu"].max()
        incoming_ml = measurement_list.measurement_list_df

        incoming_ml.loc[:, "Measu"] = np.arange(incoming_ml.shape[0]) + max_measu_current_ml + 1

        incoming_ml.loc[:, "Label"] = [f"{x}{label_suffix}" for x in incoming_ml["Label"].values]

        #new_ml.measurement_list_df = self.measurement_list_df.append(incoming_ml, ignore_index=True)
        new_ml.measurement_list_df = pd.concat([self.measurement_list_df,incoming_ml], ignore_index=True)

        return new_ml

    def load_data(self, flags, measu):

        p1_metadata, extra_metadata = self.get_p1_metadata_by_measu(measu)
        p1 = get_p1(p1_metadata=p1_metadata, flags=flags, extra_metadata=extra_metadata)

        return flags.get_measurement_label(measurement_row=self.get_row_by_measu(measu)), p1


def get_animal_name_from_list_file(list_file):
    io_class, relevant_column, ext = get_ext_based_values(list_file)
    return pl.Path(list_file).stem.rstrip(ext)
