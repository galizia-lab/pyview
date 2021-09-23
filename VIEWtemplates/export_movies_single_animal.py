import view

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
ymlfile = r""

# any  manual changes to flags, add to dictionary as required
flags_to_update = {
    ## Example:
    # "CTV_scalebar": True,
    # "mv_xgap": 30,
    # "mv_ygap": 30,
    # "mv_exportFormat": "stack_tif",
    # .....
}

# specify the animal to use
animal = ...

# specify the measus for which movies are to be generated and corresponding flag value changes
measu_flags_dict = {
    ## Example
    # 34:
    #     {
    #      "mv_FirstFrame": 40,
    #      "mv_LastFrame": 160
    #     },
    # 36:
    #     {
    #      "mv_FirstFrame": 30,
    #      "mv_LastFrame": 140
    #     },
    # 50:
    #     {
    #      "mv_FirstFrame": 160,
    #      "mv_LastFrame": 270
    #     },
    # 56: {},
    # 58:
    #     {
    #       "mv_FirstFrame": 80,
    #       "mv_LastFrame": 260
    #     }
}

if __name__ == '__main__':

    # iterate over measurements of the animal
    for measu, measu_flags in measu_flags_dict.items():

        # create a view object
        view_obj = view.VIEW()

        # load flags from yml file
        view_obj.update_flags_from_ymlfile(ymlfile)

        # update flags specified locally
        view_obj.update_flags(flags_to_update)

        # initialize view object with animal
        view_obj.initialize_animal(animal=animal)

        # load a measurement for the animal
        view_obj.load_measurement_data_from_current_animal(measu)

        # calculate signals
        view_obj.calculate_signals()

        # update movie flags for this measu
        view_obj.update_flags(measu_flags)

        # save movie for the loaded data
        view_obj.export_movie_for_current_measurement()

    if len(measu_flags_dict):
        # backup this script and the yml file used next to the created GDMs
        view_obj.backup_script_flags_configs_for_movies(files=[__file__, ymlfile])
