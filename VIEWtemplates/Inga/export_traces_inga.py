import view
import pandas as pd
import logging
import pathlib as pl

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
from view.python_core.gdm_generation.gdm_data_classes import GDMFile

moaf = r"/Users/galizia/Documents/DATA/inga_calcium/"

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
ymlfile = moaf + r"View_flags_inga_bin.yml"


# any  manual changes to flags, add to dictionary as required
flags_to_update = {
    "RM_ROITrace": 3,  # set to 0 for .coor files, 3 for .roi files and 4 for .roi.tif
    # Other flag changes can be included, for example:
    # CTV_scalebar: True,
    # mv_individualScale: 2,
    # .....
}

# list of animals for which traces are to be exported
animals = [
    "46_01"
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

        # get ROI information for this animal
        roi_data_dict, roi_file = view_obj.get_roi_info_for_current_animal()

        # initialize and empty data frame to accumulate data
        gdm_file = GDMFile()

        # iterate over measurements of the animal
        for measu in view_obj.get_measus_for_current_animal(analyze_values_to_use=(1,-1)):

            # load a measurement for the animal
            view_obj.load_measurement_data_from_current_animal(measu)

            # calculate signals
            view_obj.calculate_signals()

            # create glodatamix for the loaded measurement
            gdm_file_this_measu, _ = view_obj.get_gdm_file_for_current_measurement(roi_data_dict)

            # accumulate
            gdm_file.append_from_a_gdm_file(gdm_file_this_measu)

        # compose output file name and create parent directory if needed
        output_file = view_obj.flags.get_gloDatamix_file_for_current_animal()
        pl.Path(output_file).parent.mkdir(exist_ok=True)

        # save gloDatamix file
        gdm_file.write_to_csv(output_file)
        logging.getLogger("VIEW").info(f"Wrote gloDatamix to {output_file}")

        # backup this script and the yml file used next to the created GDMs
        view_obj.backup_script_flags_configs_for_GDMs(files=[__file__, ymlfile])
