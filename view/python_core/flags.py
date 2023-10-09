'''
(explanation as of Sept. 4th, 2019. Code by Ajay)
flags control all parameters of an experiment that are not part of the imaging data itself,
and the preferences for how to analyze the data,
e.g. what kind of data, what kind of calc methods, which filters, etc. 

flags are given in a .yml file, that is located in the mother folder, i.e.
within motherofallfolders.
There is one .yml file for each experiment (= list of many animals with same settings)

the full list of allowed flags is in view_flags_definition.csv
e.g. ... Code/git_repos/VIEW/view/flags_and_metadata_definitions/view_flags_definition.csv

The current format of flags is implemented as a class in python_core/flags.py: 
    FlagsManager. It has the following features:

Flags can be accessed by indexing, i.e., flags["LE_loadExp"]. 
However, attribute access is not available, i.e., flags.LE_loadExp will give an error.

When initialized, the object takes default values from view_flags_definition.csv.

Flags can be updated using the method "update_flags". 
Usage with a dictionary: .update_flags({'mv_bitrate':'512K'})
This method makes sure that flags are only updated to valid values.

There is a method "init_from_ymlfile" which can be used to initialize flags from a yml file.

There are several other methods in the class which are associated with flags, 
like writing flags to yml file,
or reading flags from yml file.

For view-offline usage, I would suggest the following:
Initialize a FlagsManager: flags = FlagsManager()
Update it with value from a yml file: flags.read_flags_from_yml(yml_file)
Use flags by indexing it. 
If you need attribute access, convert it to a pandas series using 
flags_series = flags.to_series()
'''

import pkg_resources
import pandas as pd
import yaml
import pathlib as pl
from ast import literal_eval
from matplotlib.colors import is_color_like, to_rgba
from view.python_core.io import read_check_yml_file, write_yml
from view.python_core.misc import interpret_string_as_boolean
from view.python_core.paths import convert_to_path_for_current_os, check_get_file_existence_in_folder
from view.python_core.measurement_list.io import get_format_specific_defs
import logging
import os


def get_internal_flags_def():
    """
    Read and return internal flags definitions
    :return: pandas.DataFrame
    """

    # get the internal flag checks file depending on flags_type
    flags_def_XL = pkg_resources.resource_filename('view',
                                                   "flags_and_metadata_definitions/view_flags_definition.csv")

    # read and return flag definitions
    flags_def_df = pd.read_csv(flags_def_XL, comment="#")

    # initialize descriptions with empty string if it has no entry
    flags_def_df["Flag Description"] = flags_def_df["Flag Description"].apply(lambda x: "" if pd.isna(x) else x)

    return flags_def_df


def check_correct_flag(flag_value, flag_name: str, expected_value_type_str: str, flag_checks: str = "True",
                       error_msg: str = "Not specified"):

    comma_index = expected_value_type_str.find(",")
    if comma_index == 0:
        expected_value_types = [eval(expected_value_type_str[1:])]
    elif comma_index == len(expected_value_type_str):
        expected_value_types = [eval(expected_value_type_str[:-1])]
    elif comma_index == -1:
        expected_value_types = [eval(expected_value_type_str)]
    else:
        expected_value_types = [eval(x) for x in expected_value_type_str.split(",")]
        if expected_value_types == [float, int] or expected_value_types == [int, float]:
            assert False, f"{expected_value_type_str} is an invalid type specification for flag={flag_name} as the" \
                          f"types are interconvertible"

    if None in expected_value_types:
        expected_value_types.remove(None)
        expected_value_types = [None] + expected_value_types

    flag_problems = [None for _ in expected_value_types]
    for evt_index, expected_value_type in enumerate(expected_value_types):

        # convert value to float if type float was expected but type int was specified
        if expected_value_type is float and type(flag_value) is int:
            flag_value = float(flag_value)

        # if expected type is bool, accept "True", "TRUE", "False", "FALSE"
        elif expected_value_type is bool and type(flag_value) is str:
            try:
                flag_value = interpret_string_as_boolean(flag_value)
            except ValueError as ve:
                flag_problems[evt_index] = str(ve)

        # if expected type is bool, accept float/int values of 0 as False and 1 as True
        elif expected_value_type is bool and type(flag_value) in (int, float):

            if flag_value == 1:
                flag_value = True
            elif flag_value == 0:
                flag_value = False
            else:
                flag_problems[evt_index] = f"Could not interpret numerical value {flag_value} as bool"

        elif expected_value_type is None:
            if flag_value is None:
                pass  # all good
            elif type(flag_value) is str:
                if flag_value.lower() == "none":
                    flag_value = None
                else:
                    flag_problems[evt_index] = f"Could not interpret string {flag_value} as None"
            else:
                flag_problems[evt_index] = f"Could not interpret value {flag_value} of type {type(flag_value)} as None"

        # if expected type is a tuple and the flag value is a string
        elif expected_value_type is tuple and type(flag_value) is str:
            try:
                flag_value = tuple(literal_eval(flag_value))
            except Exception as e:
                flag_problems[evt_index] = f"Could not interpret string value {flag_value} as a tuple!"

        # convert value int or float if required and possible
        elif expected_value_type in (float, int):
            try:
                flag_value = expected_value_type(pd.to_numeric(flag_value, downcast="integer"))
            except (ValueError, TypeError) as ve:
                flag_problems[evt_index] = f"Could not interpret value={flag_value} as a {expected_value_type}!"

        # if the flag value is none of the above, but matches requirement
        elif type(flag_value) is expected_value_type:
            pass  # all good

        # failure to interpret <flag value> as <expected_value_type>
        else:
            flag_problem = f"flag {flag_name} was expected to be of type " \
                           f"{expected_value_type_str}, got {type(flag_value)}"
            flag_problems.append(flag_problem)

        # further checks on the flag value, if type could be interpreted
        if not pd.isnull(flag_checks) and flag_problems[evt_index] is None:
            flag_checks = flag_checks.replace("‘", "\'").replace("’", "\'").replace("“", "\"").replace("”", "\"")
            if not eval(flag_checks.format(flag="flag_value")):
                flag_problems[evt_index] = error_msg.format(flag=flag_value, flag_name=flag_name)

        if flag_problems[evt_index] is None:
            break  # if flag value was parsed without problem, there is no need to try to parse further

    # if <flag_value> could not be interpreted as any of the expected types and
    # there were problems interpreting flag_value as any expected type
    if all(x is not None for x in flag_problems):
        flag_problems_str = '\n- '.join(flag_problems)
        raise AssertionError(f"Could not set the value of the flag '{flag_name}' to '{flag_value}'. "
                             f"One or more of the following problems ocurred.\n\n"
                             f"1. Could not interpret '{flag_value}' as any of these: {expected_value_type_str}\n"
                             f"2. '{flag_value}' did not meet the condition: {flag_checks}\n\n"
                             f"More Info on the errors encountered:\n\n{flag_problems_str}")

    return flag_value


def to_PIL_RGBA(color):

    if is_color_like(color):

        return tuple(to_rgba(color).astype())


class FlagsManager(object):

    def __init__(self):

        super().__init__()
        self.flags = {}

        self.flags_def_df = get_internal_flags_def()
        self.flags_def_df.set_index("Flag Name", inplace=True)

        self.compound_path_flags = ["STG_OdorReportPath", "STG_OdorInfoPath", "STG_OdormaskPath",
                                    "STG_Datapath", "STG_ProcessedDataPath", "STG_OdorAreaPath"]

        self.compound_path_flags_with_defaults = ["STG_ProcessedDataPath", "STG_OdorAreaPath"]

        self.initialize_defaults()

        self.label_separator = "_"

    def initialize_defaults(self, which=None):
        """
        Initializes flags with internally defined defaults. If <which> is None, all flags are initialized, else only
        flags with names in the iterable <which>
        :param which: iterable or None
        """

        if which is None:
            df2use = self.flags_def_df
        else:
            mask = [x in which for x in self.flags_def_df.index.values]
            df2use = self.flags_def_df.loc[mask, :]

        flag_name_value_dict = {}
        for flag_name, (flag_subgroup, flag_description, selectable_options,
                        flag_value_type, flag_default_value, flag_checks, error_msg) in df2use.iterrows():

            is_not_a_compound_path_flag = flag_name not in self.compound_path_flags

            if flag_name != "STG_MotherOfAllFolders" and \
                    is_not_a_compound_path_flag and \
                    not self.is_flag_deprecated(flag_name):
                flag_name_value_dict[flag_name] = flag_default_value

        self.update_flags(flag_name_value_dict)

    def __getitem__(self, item):

        return self.flags[item]

    def items(self):

        return self.flags.items()

    def _expand_path_relative2moaf(self, flag_value):

        possible_path = (pl.Path(self["STG_MotherOfAllFolders"]) / flag_value).resolve()
        return possible_path

    def update_flags(self, flags):
        """
        Checks the updates specified in {flags} and update if the flags values are okay.
        :param flags: dict-like
        :return: None
        """

        for flag_name, flag_value in flags.items():

            # if flag is unknown
            if not self.is_flag_known(flag_name):
                logging.getLogger("VIEW").info(f"Ignoring update request for unknown flag {flag_name}")
                continue

            if self.is_flag_deprecated(flag_name):
                logging.getLogger("VIEW").warning(f"Ignoring update request for deprecated flag {flag_name}")
                continue

            expected_value_type = self.flags_def_df.loc[flag_name, "Flag Value Type"]
            flags_checks = self.flags_def_df.loc[flag_name, "Flag Checks"]
            error_msg = self.flags_def_df.loc[flag_name, "Error Message"]

            flag_value_corrected = check_correct_flag(flag_value=flag_value,
                                                      flag_name=flag_name,
                                                      expected_value_type_str=expected_value_type,
                                                      flag_checks=flags_checks,
                                                      error_msg=error_msg)

            # additional actions are required when updating compound-path flags (STG**Path flags)
            if flag_name in self.compound_path_flags:
                if flag_name in self.compound_path_flags_with_defaults:
                    self._check_update_compound_flag(flag_name, flag_value, must_exist=False)
                else:
                    self._check_update_compound_flag(flag_name, flag_value, must_exist=True)
            # additional actions are required when updating STG_MotherOfAllFolders
            elif flag_name == "STG_MotherOfAllFolders":
                self._check_update_mother_of_all_folders(flag_value)
            else:
                self.flags[flag_name] = flag_value_corrected

    def is_flag_known(self, flag_name):
        """
        returns True if flag_name is defined in internal flags definition
        :param flag_name: str
        :return: bool
        """

        return flag_name in self.flags_def_df.index

    def is_flag_deprecated(self, flag_name):
        """
        Returns true if flag <flag_name> is deprecated
        :param flag_name: str
        :return: bool
        """

        return self.flags_def_df.loc[flag_name, "Flag Description"].lower()[:10] == "deprecated"

    def get_flag_values_by_subgroup(self, subgroup):

        flags_to_return_df = self.get_subgroup_definition(subgroup)

        return {x: self[x] for x in flags_to_return_df["Flag Name"].values}

    def _check_update_mother_of_all_folders(self, moaf):
        """
        Update flag STG_MotherOfAllFolders, reset values of STG_**Path to default values (="not set yet)
        :return:
        """

        possible_moaf_path = convert_to_path_for_current_os(moaf)
        assert possible_moaf_path.is_dir(), \
            ValueError("Error updating the flag STG_MotherOfAllFolders! The value specified for it does not point to an "
                       "existing folder on the computer.")
        self.flags["STG_MotherOfAllFolders"] = str(possible_moaf_path)
        self.initialize_defaults(self.compound_path_flags)

    def _check_update_compound_flag(self, flag_name, flag_value, must_exist=True):

        assert flag_name in self.compound_path_flags, f"{flag_name} is not one of {self.compound_path_flags}"
        temp_path = convert_to_path_for_current_os(flag_value)
        if not temp_path.is_absolute():
            temp_path = self._expand_path_relative2moaf(str(temp_path))

        try:
            temp_path.mkdir(exist_ok=True)
            self.flags[flag_name] = str(temp_path)
        except FileNotFoundError as fnfe:  # this happens when the parent of temp_path does not exist
            if must_exist:
                raise FileNotFoundError(f"I am not able to figure out the path for \"{flag_name}\"."
                                        f"Specifed value ({flag_value}) does not point to an existing folder, "
                                        f"neither does {temp_path}. "
                                        f"VIEW can unfortunately not work without this folder. Please check "
                                        f" and if required create the folder.")

    def initialize_compound_flags_with_defaults(self):

        flags2update = {}
        for flag_name in self.compound_path_flags_with_defaults:

            if flag_name not in self.flags:
                flags2update[flag_name] = self.flags_def_df.loc[flag_name, "Flag Default Value"]

                # if self.is_flag_known(flag_name) and not self.is_flag_deprecated(flag_name):
                #
                #     flags_default_value = self.flags_def_df.loc[flag_name, "Flag Default Value"]
                #     self.flags[flag_name] = str(self._expand_path_relative2moaf(flags_default_value))

        self.update_flags(flags2update)

    def check_compound_flag_initialization_status(self):

        return {flag: self.is_flag_state_default(flag) if flag in self.flags else False
                for flag in self.compound_path_flags}

    def to_series(self):

        return pd.Series(self.flags)

    def get_subgroup_definition(self, subgroup):
        """
        Returns a pandas.Dataframe which is the internal flags definition Dataframe restricted to the columns
        ("Flag Name", "Flag Default Value", "Flag Description") and rows where the column "Flag Subgroup" == <subgroup>.
        Deprecated flags are excluded.
        :param subgroup: str, a flag subgroup
        :return: pandas.Dataframe
        """

        assert subgroup in self.flags_def_df["Flag Subgroup"].values, f"Invalid Subgroup {subgroup} specified"
        flags_def_df_reset = self.flags_def_df.reset_index()

        def selection_criteria(df):
            subgroup_mask = df["Flag Subgroup"] == subgroup
            non_deprecated_mask = df["Flag Description"].apply(lambda s: s[:10].lower() != "deprecated")
            return subgroup_mask & non_deprecated_mask

        temp = flags_def_df_reset.loc[
            selection_criteria,
            ("Flag Name", "Flag Default Value", "Flag Description", "Selectable Options", "Flag Value Type")
        ]
        return temp.reset_index(drop=True)

    def get_flags_filtered_by_subgroup(self, subgroups: list):

        df = pd.DataFrame()
        for index, row in self.flags_def_df.iterrows():

            if row["Flag Subgroup"] in subgroups:
                temp_s = pd.Series()
                temp_s["Flag Name"] = row["Flag Name"]
                temp_s["Flag Subgroup"] = row["Flag Subgroup"]
                temp_s["Flag Value"] = self.flags[row["Flag Name"]]

                #df = df.append(temp_s, ignore_index=True)
                df = pd.concat([df,temp_s], ignore_index=True)
                

        df.set_index("Flag name", inplace=True)
        return df

    def get_subgroups(self):

        return self.flags_def_df["Flag Subgroup"].unique()

    def get_flag_subgroup(self, flag_name):

        return self.flags_def_df.loc[flag_name, "Flag Subgroup"]

    def read_flags_from_yml(self, yml_filename):
        """
        Reads and initializes flags from YML file
        :param yml_filename: str, path to the YML file
        :return: None
        """

        #! Any changes here must also be reflected in view.gui.central_widget.CentralWidget.load_yml_flags !

        yml_flags = read_check_yml_file(yml_filename, dict)
        # STG_MotherOfAllFolders must be set before STG* flags so that they are properly interpreted
        self.update_flags({"STG_MotherOfAllFolders": str(pl.Path(yml_filename).parent)})
        # remove to avoid double, possible wrong initialization of this flag
        if "STG_MotherOfAllFolders" in yml_flags:
            del yml_flags["STG_MotherOfAllFolders"]

        self.update_flags(yml_flags)
        self.initialize_compound_flags_with_defaults()

    def write_flags_to_yml(self, yml_filename):
        """
        Writes flags to a YML file
        :param yml_filename: str, path of YML file
        """

        dict2write = {}
        dict2write.update(self.flags)

        for flag_name in self.compound_path_flags:
            if flag_name in self.flags:
                if not self.is_flag_state_default(flag_name):
                    path = pl.Path(self.flags[flag_name])
                    if path.is_absolute():
                        dict2write[flag_name] = os.path.relpath(path, self["STG_MotherOfAllFolders"])

        dict2write["STG_MotherOfAllFolders"] = "!!parent of this file will be used!!"
        for k, v in dict2write.items():
            if type(v) in (tuple,):
                dict2write[k] = str(v)

        write_yml(yml_filename=yml_filename, to_write=dict2write)

    def get_coor_dir_str(self):

        return self.flags.get("STG_OdormaskPath", "not set yet")

    def get_area_dir_str(self):

        return self.flags.get("STG_OdorAreaPath", "not set yet")

    def get_raw_data_dir_str(self):

        return self.flags.get("STG_Datapath", "not set yet")

    def get_list_dir_str(self):

        return self.flags.get("STG_OdorInfoPath", "not set yet")

    def get_op_dir_str(self):

        return self.flags.get("STG_OdorReportPath", "not set yet")

    def get_processed_data_dir_str(self):

        return self.flags["STG_ProcessedDataPath"]

    def get_processed_data_dir_path(self):

        return pl.Path(self.get_processed_data_dir_str())

    def get_processed_data_op_path(self, format_name):

        return pl.Path(self.get_op_dir_str()) / "ProcessedDataExported" / format_name

    def get_animal_op_dir_path(self):
        """
        Returns <STG_OdorReportPath>/<STG_ReportTag> as pathlib.Path object
        :return: pathlib.Path
        """
        return pl.Path(self.get_op_dir_str()) / f"{self.get_current_animal_id()}"

    def get_animal_op_dir(self):
        """
        Returns <STG_OdorReportPath>/<STG_ReportTag> as a string
        :return: str
        """
        return str(self.get_animal_op_dir_path())

    def get_archive_dir_str(self):

        return self["STG_TempArchivePath"]

    def get_move_corrected_data_path_for_animal(self, animal):

        return self.get_processed_data_dir_path() / "MovementCorrectedData" / animal

    def get_existing_filename_in_coor(self, extension, measurement_label=""):

        return check_get_file_existence_in_folder(folder=self.get_coor_dir_str(), possible_extensions=[extension],
                                                  stems=self.get_file_stem_hierarchy(measurement_label),
                                                  )

    def get_file_stem_hierarchy(self, measurement_label):

        animal_tag = self.get_roi_filename_stem_for_current_animal()
        return [animal_tag, f"{animal_tag}_{measurement_label}"]

    def get_existing_area_filepath(self, measurement_label=""):
        """
        Checks possible nomenclatures and formats for mask file for current flag values and returns one that exisits
        If None exist, raises FileNotFoundError
        :return: pathlib.Path
        """

        extension_hierarchy = [".area.tif", ".AREA.tif", ".Area", ".AREA"]
        filename = check_get_file_existence_in_folder(folder=self.get_area_dir_str(),
                                                      possible_extensions=extension_hierarchy,
                                                      stems=self.get_file_stem_hierarchy(measurement_label))
        if filename is None:
            filename = check_get_file_existence_in_folder(folder=self.get_coor_dir_str(),
                                                          possible_extensions=extension_hierarchy,
                                                          stems=self.get_file_stem_hierarchy(measurement_label))

        return filename

    def get_current_animal_id(self):

        return self["STG_ReportTag"]

    def get_existing_lst_file(self, animal_name=None):
        """
        Tests possible files names for current flag settings and returns existing one. Else None.
        :return: str or None
        """

        if animal_name is not None:
            self.update_flags({"STG_ReportTag": animal_name})

        possible_lst_extensions = get_format_specific_defs()["extension"].values
        return check_get_file_existence_in_folder(folder=self.get_list_dir_str(), stems=[self.get_current_animal_id()],
                                                  possible_extensions=possible_lst_extensions)

    def get_lst_file_stem(self):
        """
        Returns the stem of the measurement list file given the current flag values
        :return: str
        """

        return str(pl.Path(self.get_list_dir_str()) / self.get_current_animal_id())


    def get_component_traces_file(self, animal):

        return str(self.get_processed_data_dir_path() / "ComponentTimeTraces" / f"{animal}.csv")
    
    def get_op_tapestries_dir(self):
        """
        Returns the name of the folder used to output overviews as a string
        :return: string
        """

        return str(pl.Path(self.get_op_dir_str()) / "tapestries")

    def get_op_movie_dir(self):
        """
        Returns the name of the folder used to output movies as a string
        :return: string
        """

        return str(self.get_animal_op_dir_path() / "movies")

    def get_gloDatamix_file_for_current_animal(self):
        """
        Returns the name of the file used to output gloDatamix for current animal
        :return: string
        """

        return str(self.get_animal_op_dir_path() / f"{self.get_current_animal_id()}.gloDatamix.csv")

    def get_pipeline_report_dir_for_animal(self, animal):

        return str(pl.Path(self.get_op_dir_str()) / "Pipeline Reports" / animal)

    def get_roi_filename_stem_for_animal(self, animal):

        return animal

    def get_roi_filename_stem_for_current_animal(self):

        return self.get_roi_filename_stem_for_animal(animal=self.get_current_animal_id())

    def clear_flags(self):

        self.flags = {}

    def copy(self):

        flags = FlagsManager()
        flags.flags = self.flags.copy()
        return flags

    def is_flag_state_default(self, flag_name):

        assert flag_name in self.flags_def_df.index, f"Unknown flag name {flag_name}"

        flag_subgroup, flag_description, selectable_values, flag_value_type, flag_default_value, flag_checks, error_msg \
            = self.flags_def_df.loc[flag_name, :]

        flag_value_is_inited = flag_name in self.flags

        flag_value_is_default = False  # the value here does not matter
        if flag_value_is_inited:
            flag_value_is_default \
                = self.flags[flag_name] == check_correct_flag(
                    flag_name=flag_name,
                    flag_value=flag_default_value,
                    error_msg=error_msg,
                    expected_value_type_str=flag_value_type,
                    flag_checks=flag_checks)

        return flag_value_is_default or not flag_value_is_inited

    def get_default_measurement_label(self):

        return f"{self.flags['STG_ReportTag']}{self.label_separator}{self['STG_Measu']}"

    def get_measurement_label(self, measurement_row):

        label = self.get_default_measurement_label()

        label_columns = self.flags["LE_labelColumns"]
        labels_to_exclude = ["Measu"]
        labels2use = [x for x in label_columns if x not in labels_to_exclude and x in measurement_row]
        for col in labels2use:
            label = f"{label}{self.label_separator}{measurement_row[col]}"

        return label

    def get_ctv_method_file(self):

        ctv_method_file = self["CTV_MethodFile"]

        if pl.Path(ctv_method_file).is_absolute() and pl.Path(ctv_method_file).is_file():
            return ctv_method_file
        elif not self.is_flag_state_default("STG_MotherOfAllFolders"):
            possible_file = self._expand_path_relative2moaf(self["CTV_MethodFile"])

            if possible_file.is_file():
                return str(possible_file)

        raise FileNotFoundError(f"Could not interpret the specified CTV Method File ({ctv_method_file}) "
                                f"as a file")

    def get_bleach_corr_patch_size(self):
        """
        Interprets value of flag "LE_BleachPatchSize".
        :returns: tuple indicating patch size for bleach correction along x and y
        """
        flag_value = self["LE_BleachPatchSize"]

        if type(flag_value) is int:
            return flag_value, flag_value
        elif type(flag_value) is tuple:
            if len(flag_value) == 2:
                return flag_value
            else:
                raise ValueError(f"Flag `LE_BleachPatchSize` expects an integer or a tuple of two integers. "
                                 f"Got {flag_value}")

        raise ValueError(
            f"Could not interpret value set for flag `LE_BleachPatchSize`. Expected int or tuple, got {flag_value}")

    def reset_all_flags_in_subgroup_to_default(self, subgroup):

        def_df = self.get_subgroup_definition(subgroup).set_index("Flag Name")

        self.update_flags(def_df["Flag Default Value"].to_dict())

    def interpret_median_filter_params(self):

        return interpret_filter_params(
            filter_behaviour_switch=self["Data_Median_Filter"],
            size_in_space=self["Data_Median_Filter_space"],
            size_in_time=self["Data_Median_Filter_time"]
        )

    def interpret_mean_filter_params(self):

        return interpret_filter_params(
            filter_behaviour_switch=self["Data_Mean_Filter"],
            size_in_space=self["Data_Mean_Filter_space"],
            size_in_time=self["Data_Mean_Filter_time"]
        )


def interpret_filter_params(filter_behaviour_switch, size_in_space, size_in_time):

    if filter_behaviour_switch == 1:
        size_in_space = 3  # old fixed values, for backwards compatibility
        size_in_time = 1
    elif filter_behaviour_switch == 2:
        size_in_space = 1  # old fixed values, for backwards compatibility
        size_in_time = 3
    elif filter_behaviour_switch == 3:
        size_in_space = max(1, size_in_space)  # values from flags
        size_in_time = max(1, size_in_time)  # values at least 1
        # (i.e., if I selected a size of 0 to switch off filtering, 1 is taken all the same, since 1 means no filter)
    else:  # will result in no filtering
        size_in_time = None
        size_in_space = None

    return size_in_space, size_in_time
