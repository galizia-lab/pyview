import pkg_resources
import pandas as pd
from collections import OrderedDict
from .io import read_check_yml_file


def get_metadata_definition():
    """
    Read and return internal metadata definition as a DataFrame with internal metadata names as indices
    :return: pandas.DataFrame
    """
    metadta_def_csv = pkg_resources.resource_filename('view',
                                                      "flags_and_metadata_definitions/metadata_definition.csv")
    metadta_def_df = pd.read_csv(metadta_def_csv, index_col=0)

    return metadta_def_df


def get_internal_flags_def():
    """
    Read and return internal flags definitions
    :return: pandas.DataFrame
    """

    # get the internal flag checks file depending on flags_type
    flags_def_XL = pkg_resources.resource_filename('view',
                                                   "flags_and_metadata_definitions/view_flags_definition.csv")

    # read and return flag definitions
    return pd.read_csv(flags_def_XL, comment="#")


def get_internal_fonts_dir():
    """
    Returns the path of the internal fonts directory
    :return: string
    """

    fonts_dir = pkg_resources.resource_filename("view", "fonts")

    return fonts_dir


def get_internal_icons(icon_name):
    """
    Returns the internal path of an icon file if exists
    :param icon_name: string, name of the icon file to look for
    :return: string
    """

    return pkg_resources.resource_filename("view", f"graphics/icons/{icon_name}")


def get_internal_jinja_template(template_name):
    """
    Returns a internal jinja template with name <template_name>
    :param template_name: str, name of the jinja template with extension
    :return: str
    """

    return pkg_resources.resource_filename("view", f"jinja_templates/{template_name}")


def get_setup_info_df():
    """
    Reads the internal csv file containing information about recording setups and returns contents as a pandas DataFrame
    :return: pandas.DataFrame
    """

    internal_setup_info_csv = pkg_resources.resource_filename(
        'view', "flags_and_metadata_definitions/setup_definitions.csv")

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

        setup_info_dict[f"{description} (LE_loadExp={LE_loadExp})"] = LE_loadExp

    return setup_info_dict


def get_gdm_doc_df():
    """
    Reads and returns pandas.Dataframe containing the descriptions of GDM columns
    """

    gdm_doc_csv = pkg_resources.resource_filename(
        "view", "flags_and_metadata_definitions/glodatamix_columns_doc.csv")

    return pd.read_csv(gdm_doc_csv)