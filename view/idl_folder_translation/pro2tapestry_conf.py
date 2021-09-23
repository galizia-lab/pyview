import pkg_resources
import pathlib as pl
import re
import pandas as pd
import textfsm
import yaml


def get_template():
    """
    Read and return internal metadata definition as a DataFrame with internal metadata names as indices
    :return: pandas.DataFrame
    """
    pro_template_file = pkg_resources.resource_filename(
        'view', "idl_folder_translation/pro_fsm_template.txt")

    return pro_template_file


def parse_pro_file(pro_file):
    """
    Parse a .pro file to extract flag and measurement info for tapestry config files
    :param str pro_file: path of a .pro file
    :return: pandas.Dataframe
    """

    pro_template = get_template()

    with open(pro_file) as fle:
        raw_pro_file_str = fle.read()

    with open(pro_template) as fh:
        re_table = textfsm.TextFSM(fh)
        pro_data = re_table.ParseText(text=raw_pro_file_str)
        pro_data_df = pd.DataFrame(columns=re_table.header, data=pro_data)

    return pro_data_df


def parse_animal_tag(pro_file):
    """
    Given a .pro file, parse the filename to extract the animal tag
    :param str pro_file: path of a .pro file
    :return: animal tag
    :rtype: str
    """

    pro_filename = pl.Path(pro_file).name
    match = re.fullmatch("gr[^_]*_(\w+).pro", pro_filename, re.IGNORECASE)

    if not match:
        raise ValueError(f"Could not figure out the animal id of the pro file: {pro_file}")

    return match.group(1)


def convert_pro_to_tapestry_config(input_pro_file, output_yml_file, animal_tag, flags_to_override):
    """
    Parse info in a .pro file and convert it to a tapestry config file
    :param str input_pro_file: path of an input .pro file
    :param str output_yml_file: path of the output yml file to be created
    :param dict flags_to_override: these flags will override flags from .pro file if present, else be added
    """

    pro_df = parse_pro_file(input_pro_file)

    yml_dict = {}
    flags_to_change = {}

    for row_ind, row in pro_df.iterrows():

        if row["measus"]:
            measus = [int(x) for x in row["measus"]]
            yml_dict[f"row{row_ind}"] = {"measus": measus}
        else:
            flags_to_change = {k: v for k, v in zip(row["flag_names"], row["flag_values"])}

    first_row_key = list(yml_dict.keys())[0]

    flags_final = {}
    for k, v in flags_to_change.items():
        if k in ["scalemin", "scalemax"]:
            flags_final[f"SO_MV_{k}"] = v
            flags_final["SO_individualScale"] = 0
        else:
            flags_final[k] = v

    flags_final.update(flags_to_override)
    yml_dict[first_row_key]["flags"] = flags_final

    yml_dict[first_row_key]["animal"] = animal_tag

    with open(output_yml_file, 'w') as fh:
        yaml.dump(yml_dict, fh, Dumper=yaml.SafeDumper)


