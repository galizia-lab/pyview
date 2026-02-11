import view
import pathlib as pl

#mother of all folders
moaf = pl.Path(__file__).parents[1]

ymlfile = moaf / r"view_synthetic_666.yml"


# please enter the paths of tapestry configuration files in ABSOLUTE form.
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
tapestry_config_files = [
    moaf / r"06_PROGS/tapestry_ctv22_global.yml" ,
    moaf / r"06_PROGS/tapestry_ctv22_individual.yml" 
    ]


# define a function that takes a row of the measurement list and returns a string. This string will be placed
# below the overview
def text_below(row):
    # Example 1: the label below each overview will just be the odor  
    return row['Label']+'_'+row['Odour']

    # Example 2: the label below each overview will be the odor and concentration separated by an underscore ("_")
    # return f"{row['Odour']}_{row['OConc']}"


# define a function that takes a row of the measurement list and returns a string. This string will be placed
# next to the overview on the top right.
def text_right_top(row):
    pass


# define a function that takes a row of the measurement list and creates the string to be placed below the overview
def text_right_bottom(row):
    # return row['OConc']
    return tapestry_config_file.name[-9:-4]
    #pass


if __name__ == '__main__':

    for tapestry_config_file in tapestry_config_files:
        # When text_right_bottom_func and text_right_top_func are specified to be None, the upper and lower limits
        # of the data shown in an overview will be printed to its right top and right bottom side
        # To customize the strings printed there, please define the functions 'text_right_top' and
        # 'text_right_bottom above and pass them appropriately below, in the place on 'None'.
        html_out_file, view_obj = view.create_tapestry(init_yml_flags_file=ymlfile,
                                                       tapestry_config_file=tapestry_config_file,
                                                       text_below_func=text_below,
                                                       text_right_top_func=None,
                                                       text_right_bottom_func=text_right_bottom)

        # backup this script and the yml file used next to the created tapestries
        view_obj.backup_script_flags_configs_for_tapestries(files=[__file__, ymlfile, tapestry_config_file])
