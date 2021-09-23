import pathlib as pl
from view.idl_folder_translation.pro2tapestry_conf import parse_animal_tag, convert_pro_to_tapestry_config

# input files are expected to be in this folder
input_folder_containing_pros = r""

# output files will be created in this folder
output_folder_for_tapestry_configs = r""

# just the name of the file, without the path
# each of these files are expected to be found in the folder pointed to by `input_folder_containing_pros`
pro_file_names = [
    "",
    ""
]

# these flags will override flags initializations from .pro files if present, else will be added.
flags_to_override = {
    "SO_individualScale": 3
}


if __name__ == '__main__':

    # iterate through each of
    for pro_file_name in pro_file_names:

        # parse the animal tag from the file name of the .pro file
        animal_tag = parse_animal_tag(pro_file_name)

        # construct the full path of the .pro file
        pro_file_path = pl.Path(input_folder_containing_pros) / pro_file_name

        # construct the path for the output yml file
        pro_file_name_stem = pro_file_name.split(".")[0]
        op_yml_path = pl.Path(output_folder_for_tapestry_configs) / f"{pro_file_name_stem}.yml"

        # convert
        convert_pro_to_tapestry_config(
            input_pro_file=pro_file_path, output_yml_file=op_yml_path, animal_tag=animal_tag,
            flags_to_override=flags_to_override
        )
