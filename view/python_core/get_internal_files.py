from importlib.resources import as_file
from importlib.resources import files as il_files

import pandas as pd

from view import flags_and_metadata_definitions, fonts, jinja_templates
from view.graphics import icons
from view.python_core.tests import test_files


def get_metadata_definition() -> pd.DataFrame:
    """
    Read and return internal metadata definition as a DataFrame with internal metadata names as indices
    :return: pandas.DataFrame
    """
    metadata_def_csv = il_files(flags_and_metadata_definitions).joinpath(
        "metadata_definition.csv"
    )
    with as_file(metadata_def_csv) as f:
        metadata_def_df = pd.read_csv(f, index_col=0)

    return metadata_def_df


def get_internal_flags_def() -> pd.DataFrame:
    """
    Read and return internal flags definitions
    :return: pandas.DataFrame
    """

    # get the internal flag checks file depending on flags_type
    flags_def_XL = il_files(flags_and_metadata_definitions).joinpath(
        "view_flags_definition.csv"
    )
    with as_file(flags_def_XL) as f:
        return pd.read_csv(f, comment="#")


def get_internal_fonts_dir() -> str:
    """
    Returns the path of the internal fonts directory
    :return: string
    """

    return fonts.__path__[0]


def get_internal_icons(icon_name) -> str:
    """
    Returns the internal path of an icon file if exists
    :param icon_name: string, name of the icon file to look for
    :return: string
    """

    icon_path = il_files(icons).joinpath(icon_name)
    return str(icon_path)


def get_internal_jinja_template(template_name) -> str:
    """
    Returns a internal jinja template with name <template_name>
    :param template_name: str, name of the jinja template with extension
    :return: str
    """

    jinja2_template_filename = il_files(jinja_templates).joinpath(
        template_name
    )
    return str(jinja2_template_filename)


def get_setup_info_df() -> pd.DataFrame:
    """
    Reads the internal csv file containing information about recording setups and returns contents as a pandas DataFrame
    :return: pandas.DataFrame
    """

    internal_setup_info_csv = il_files(
        flags_and_metadata_definitions
    ).joinpath("setup_definitions.csv")
    with as_file(internal_setup_info_csv) as f:
        return pd.read_csv(f, comment="#")


def get_setup_description_dict() -> dict:
    """
    Returns a dict, with recording setup description strings as keys and corresponding LE_loadExp values as
    values
    """

    setup_info_df = get_setup_info_df()

    setup_info_df["description+LE_loadExp"] = setup_info_df.apply(
        lambda x: f"{x['Description']} (LE_loadExp={x['LE_loadExp']})", axis=1
    )

    return setup_info_df.set_index("description+LE_loadExp")[
        "LE_loadExp"
    ].to_dict()


def get_gdm_doc_df() -> pd.DataFrame:
    """
    Reads and returns pandas.Dataframe containing the descriptions of GDM columns
    """
    gdm_doc_csv = il_files(flags_and_metadata_definitions).joinpath(
        "glodatamix_columns_doc.csv"
    )
    with as_file(gdm_doc_csv) as f:
        return pd.read_csv(f)


def get_internal_test_files_path() -> str:
    """
    Returns the path of the internal test files directory as string
    :return: str
    """

    return test_files.__path__[0]
