import view 
from view.python_core import view_object
from view.python_core.io import write_tif_2Dor3D
from view.python_core.matfile import export_processed_data_as_mat_file
import pathlib as pl
import numpy as np

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
moaf = r"/Users/galizia/Documents/DATA/elisabeth/"

# this tells view all settings including the folder structure of your project
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
ymlfile = moaf + r"Elisabeth_pyView exportTiff.yml"
# any  manual changes to flags, add to dictionary as required
# any  manual changes to flags, add to dictionary as required
flags_to_update = {
    "RM_ROITrace": 0,  # set to 0 for .coor files, 3 for .roi files and 4 for .roi.tif
    "LE_CalcMethod": 3,  # 0 for raw data, 3 for dF/F
    # CTV_scalebar: True,
    # mv_individualScale: 2,
    # .....
}

# list of animals for which MAT files are to be generated
animals = [
    'ES_250724d_cal520_PN',
#    'ES_250627d_cal520_PN'
]
analyze_values_to_use=(2,-1)

if __name__ == '__main__':

    # create a view object
    view_obj = view.VIEW()

    # load flags from yml file
    view_obj.update_flags_from_ymlfile(ymlfile)

    # update flags specified locally
    view_obj.update_flags(flags_to_update)

    # iterate over animals
    for animal in animals:
        print(f"Processing animal {animal}...")
        # collect all signal movies for the animal
        signal_movies = []

        # initialize view object with animal
        view_obj.initialize_animal(animal=animal)

        # iterate over measurements of the animal
        for measu in view_obj.get_measus_for_current_animal(analyze_values_to_use=analyze_values_to_use):
            print(f"Processing measurement {measu}...")

            # load a measurement for the animal
            view_obj.load_measurement_data_from_current_animal(measu)

            # calculate signals
            view_obj.calculate_signals()

            # accumulate signal
            signal_movies.append(view_obj.p1.sig1)

            # save movie for the loaded data
            #view_obj.export_movie_for_current_measurement()

        # export all accumulated signal movies to a tiff file
        # signal_movies = [arr1, arr2, ..., arr23]
        big_stack = np.concatenate(signal_movies, axis=2)

        # get filename to save tiff
        tif_dir_path = view_obj.flags.get_animal_op_dir_path()
        tif_dir_path.mkdir(parents=True, exist_ok=True)
        # add CalcMethod to filename
        filename = f"{animal}_calc{view_obj.flags['LE_CalcMethod']}.tiff"
        op_filepath = (tif_dir_path / filename)
        

        print(f"Saving animal {animal} with shape {big_stack.shape}")
        write_tif_2Dor3D(big_stack, op_filepath, dtype=None, scale_data=False, labels=None)
        
        # export measurement list for the animal, only measurements with analyze=1 or -1
        filename = f"{animal}_calc{view_obj.flags['LE_CalcMethod']}.lst.xlsx"
        op_filepath = str(tif_dir_path / filename)
        print(f"Saving .lst file for animal {animal} as {filename}")
        # select only those that have been exported
        sub_measurements = view_obj.measurement_list.sub_select_based_on_analyze(analyze_values_accepted=analyze_values_to_use)
        sub_measurements.write_to_list_file(lst_fle=op_filepath, columns2write=None)
        #                                        overwrite_old_values=overwrite_old_values)
    # backup this script and the yml file used next to the created GDMs
    #view_obj.backup_script_flags_configs_for_movies(files=[__file__, ymlfile])
