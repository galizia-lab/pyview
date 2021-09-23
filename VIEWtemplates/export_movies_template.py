import view

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
ymlfile = r""

# any  manual changes to flags, add to dictionary as required
flags_to_update = {
    # Example:
    # "CTV_scalebar": True,
    # "x_gap": 30,
    # "y_gap": 30,
    # "mv_individualScale": 2,
    # .....
}

# list of animals for which movies are to generated
animals = [
    "",
    ""
]

if __name__ == '__main__':

    # create a view object
    view_obj = view.VIEW()

    # load flags from yml file
    view_obj.update_flags_from_ymlfile(ymlfile)

    # update flags specified locally
    view_obj.update_flags(flags_to_update)

    # iterate over animals
    for animal in animals:

        # initialize view object with animal
        view_obj.initialize_animal(animal=animal)

        # iterate over measurements of the animal
        for measu in view_obj.get_measus_for_current_animal(analyze_values_to_use=(1,)):

            # load a measurement for the animal
            view_obj.load_measurement_data_from_current_animal(measu)

            # calculate signals
            view_obj.calculate_signals()

            # save movie for the loaded data
            view_obj.export_movie_for_current_measurement()

    # backup this script and the yml file used next to the created GDMs
    view_obj.backup_script_flags_configs_for_movies(files=[__file__, ymlfile])
