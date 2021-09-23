import re
import pandas as pd
from view.python_core.get_internal_files import get_metadata_definition
from view.python_core.stimuli import PulsedStimuliiHandler


def parse_p1_metadata_from_measurement_list_row(row):
    """
    Parse metadata from the row of a measurement list into a pandas Series object
    :param pandas.Series row: row of a measurement list
    :rtype: pandas.Series
    """

    # get metadata names and default values
    meta_def = MetadataDefinition()
    p1_metadata = meta_def.get_default_row()
    extra_metadata = {}
    list_column_p1_metadata_mapping = meta_def.get_list_column_p1_metadata_mapping()
    for k, v in row.items():
        if k in list_column_p1_metadata_mapping:
            p1_metadata_name = list_column_p1_metadata_mapping[k]
            if not pd.isnull(p1_metadata_name):
                p1_metadata[p1_metadata_name] = v
        else:
            extra_metadata[k] = v

    # stimulus information is stored in this object
    p1_metadata["pulsed_stimuli_handler"] = PulsedStimuliiHandler.create_from_row(row)

    if "agetxt" in p1_metadata:
        age = re.split('-|;', str(p1_metadata["agetxt"]))
        # age can be one number, or a range separated by ; or -
        # now age is ['5'] or ['3','7']
        p1_metadata["age"] = age[0]  # the youngest age in the range, or the only age
        p1_metadata["agemax"] = age[-1]  # the second number or the only number

    # calculate stimulus times in seconds
    p1_metadata["frequency"] = 1000.0 / p1_metadata["trial_ticks"]

    try:
        temp = p1_metadata["pixelsizex"] + 1
    except TypeError:
        print(f"Pixelsize has been converted to a date: {p1_metadata['pixelsizex']} "
              f"by excel - please correct. I assume 2.4 for now")
        p1_metadata["pixelsizex"], p1_metadata["pixelsizey"] = 2.4, 2.4
    except KeyError:  # pixelsizex is not specified
        pass

    return p1_metadata, extra_metadata


class MetadataDefinition(object):

    def __init__(self):

        self._def_df = get_metadata_definition()

    @property
    def def_df(self):

        return self._def_df.copy()

    def get_list_column_p1_metadata_mapping(self):

        temp = self._def_df.loc[:, "p1"]
        return temp.to_dict()

    def get_default_row(self):
        """
        returns a pandas Series representing a row of a measurement, with all default values
        :return: pandas Series
        """

        default_row = self._def_df["Default values"]
        return default_row.apply(lambda x: pd.to_numeric(x, errors="ignore"))

    def is_value_default(self, metadata_name, value):

        def_df2use = self._def_df

        assert metadata_name in def_df2use.index.values, f"Unknown metadata name {metadata_name}"

        default_value = def_df2use.loc[metadata_name, "Default values"]

        return value == pd.to_numeric(default_value, errors="ignore")
