from view import VIEW
from view.python_core.matfile import export_processed_data_as_mat_file

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
ymlfile = r""

# any  manual changes to flags, add to dictionary as required
flags_to_update = {
    # Example: flags for CTV specification
}

# list of animals for which MAT files are to be generated
animals = [
    "",
    ""
]

if __name__ == '__main__':

    # create a view object
    view_obj = VIEW()

    # load flags from yml file
    view_obj.update_flags_from_ymlfile(ymlfile)

    # update flags specified locally
    view_obj.update_flags(flags_to_update)

    # iterate over animals
    for animal in animals:

        # initialize view object with animal
        view_obj.initialize_animal(animal=animal)

        # export data as MAT file
        export_processed_data_as_mat_file(view_obj, analyze_values_to_use=(1,))

    # backup this script and the yml file used next to the created MAT files
    view_obj.backup_script_flags_configs_for_processed_data_output(files=[__file__, ymlfile], format_name="MAT")



