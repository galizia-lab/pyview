import importlib
import pathlib as pl
from collections import OrderedDict

import pandas as pd

from view import flags_and_metadata_definitions, fonts, jinja_templates
from view.graphics import icons
from view.python_core.tests import test_files


def get_metadata_definition():
    """
    Read and return internal metadata definition as a DataFrame with internal metadata names as indices
    :return: pandas.DataFrame
    """
    with importlib.resources.path(
        flags_and_metadata_definitions, "metadata_definition.csv"
    ) as metadata_def_csv:
        metadata_def_df = pd.read_csv(metadata_def_csv, index_col=0)

    return metadata_def_df


def get_internal_flags_def():
    """
    Read and return internal flags definitions
    :return: pandas.DataFrame
    """

    # get the internal flag checks file depending on flags_type
    with importlib.resources.path(
        flags_and_metadata_definitions, "view_flags_definition.csv"
    ) as flags_def_XL:
        # read and return flag definitions
        return pd.read_csv(flags_def_XL, comment="#")


def get_internal_fonts_dir():
    """
    Returns the path of the internal fonts directory
    :return: string
    """

    return fonts.__path__[0]


def get_internal_icons(icon_name):
    """
    Returns the internal path of an icon file if exists
    :param icon_name: string, name of the icon file to look for
    :return: string
    """

    with importlib.resources.path(icons, icon_name) as fle:
        return str(fle)


def get_internal_jinja_template(template_name):
    """
    Returns a internal jinja template with name <template_name>
    :param template_name: str, name of the jinja template with extension
    :return: str
    """

    with importlib.resources.path(
        jinja_templates, template_name
    ) as jinja2_template_filename:
        return jinja2_template_filename


def get_setup_info_df():
    """
    Reads the internal csv file containing information about recording setups and returns contents as a pandas DataFrame
    :return: pandas.DataFrame
    """

    with importlib.resources.path(
        flags_and_metadata_definitions, "setup_definitions.csv"
    ) as internal_setup_info_csv:
        return pd.read_csv(internal_setup_info_csv, comment="#")


def get_setup_description_dict():
    """
    Returns an OrderedDict, with recording setup description strings as keys and corresponding LE_loadExp values as
    values
    :return: OrderedDict
    """

    setup_info_df = get_setup_info_df()

    setup_info_dict = OrderedDict()

    for ind, (LE_loadExp, description) in setup_info_df.iterrows():
        setup_info_dict[f"{description} (LE_loadExp={LE_loadExp})"] = (
            LE_loadExp
        )

    return setup_info_dict


def get_gdm_doc_df():
    """
    Reads and returns pandas.Dataframe containing the descriptions of GDM columns
    """
    with importlib.resources.path(
        flags_and_metadata_definitions, "glodatamix_columns_doc.csv"
    ) as gdm_doc_csv:
        return pd.read_csv(gdm_doc_csv)


def get_internal_test_files_path():
    """
    Returns the path of the internal test files directory as string
    :return: str
    """

    return test_files.__path__[0]
