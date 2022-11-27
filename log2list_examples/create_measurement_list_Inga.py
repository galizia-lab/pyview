'''
Creates .lst file from/for  Inga single-frame single-tif files
Author: Giovanni, September 2022, based on template in VIEW folder 

Expected data structure:
    In the folder "01_DATA", each animal has a folder
    - Data is from SetupB, new CCD as of 2021
    - Format of the data is: every single frame is an individual .tif file, with sequential numbering
    - Next to all .tif files, there is a .txt file with the experimental parameters
    
    There is a sister folder "02_LISTS" (created if not yet present)
    Location is in STG_MotherOfAllFolders (set it below)
    
Output:
    In the folder "02_LISTS", for every animal:
        There will be a file Animal.lst.xlsx, e.g. "glom17_210923_bee11.lst.xlsx"
        That file contains one line for each measurement.
        Measurements that have no time dimension (snapshots, z-stacks) will have "0" in the column "analyze"

Dataformat:
    DBB1 contains the name of the .txt file
    dbb2 contains a list with the individual .tif files, one for each frame
    

        
What to do next?
    In THIS file, change values that are global
    or insert a function that can extract odor name or concentration name from somewhere
    
    In the Animal.lst.xlsx file, correct/complete entries (e.g. odor names, odor concentrations)
    Make sure stimulus timing information is correct
    
    When you run this program again on the same dataset, and the Animal.lst.xlsx file is already present,
    some columns will NOT be overwritten, but will be taken from the previous .lst.xlsx file,
    protecting your manually entered information. 
    Which columns? Specify them below in 
    overwrite_old_values

Why do I need a .lst.xlsx file?
    Load measurements in pyVIEW using this .lst file, so that stimulus information is correct
    For off-line analysis, information is taken from this file. 

Good to know:
    Information, where possible, is taken from the OME header of the incoming .tif file.
    If that information is wrong, incomplete, or else, modify the code 
    
'''
from view.python_core.measurement_list import MeasurementList
from view.python_core.measurement_list.importers import get_importer_class
from view.python_core.flags import FlagsManager
from collections import OrderedDict
import pandas as pd
import logging
import pathlib as pl
import numpy as np
from view.python_core.io import read_SingleWavelengthTif_MultiFileInga, write_tif_2Dor3D


logging.basicConfig(level=logging.INFO)

# ------------------ names of columns that will be overwritten by old values -------------------------------------------
# -- if you run the same animal a second time!
# ------ these will only be used if a measurement list file with the same name as current output file exists -----------

overwrite_old_values = ["Line", "PxSzX", "PxSzY", "Age", "Sex", "Prefer",
                        "Comment", "Analyze", "Odour", "OConc"]

# ______________________________________________________________________________________________________________________




# ------------------- Some parameters about experimental setup, data structure and output file type --------------------
# 3 for single wavelength Till Photonics Measurements
# 4 for two wavelength Till Photonics Measurements
# 20 for Zeiss Confocal Measurements
# 21 for Leica Confocal Measurements: .lif file
# 32 for multiple TIF files, one for each frame
LE_loadExp = 32 #32 for multiple TIF files

# Mother of all Folders of your dataset
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_MotherOfAllFolders = r'/Users/galizia/Documents/DATA/inga_calcium/'
#01_DATA/220609_Animal46_greg_socialmodulation/01_Data/Trial01'
#STG_MotherOfAllFolders = r'/Users/galizia/Documents/DATA/Marco_lif'

# path of the "Data" folder in VIEW organization containing the data
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_Datapath = r"01_DATA"

# path of the "Lists" folder in VIEW organization containing the list files
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_OdorInfoPath = r"02_LISTS"

# Choose measurement list output extension among ".lst", ".lst.xlsx", ".settings.xlsx"
# VIEW does not support writing .xls list files anymore (nonetheless, it can read them and revise/update them to .xlsx)
measurement_output_extension = ".lst.xlsx"

# ------------------- A dictionary containing default values for metadata.----------------------------------------------
# ------------------- Only metadata included in this dictionary will be written ----------------------------------------
# ----Note that columns of the output measeurement list files will have the same order as below.------------------------

default_values = OrderedDict()

default_values['Measu'] = 0  # unique identifier for each line, corresponds to item in TILL photonics log file

default_values['Label'] = "none"
default_values['Odour'] = 'odor?'  # stimulus name, maybe extracted from label in the function "custom_func" below
default_values['OConc'] = 0  # odor concentration, maybe extracted from label in the function "custom_func" below
default_values['Analyze'] = -1  # whether to analyze in VIEWoff. Default -1, which means "not checked yet"

default_values['Cycle'] = 0  # how many ms per frame
default_values['DBB1'] = 'none'  # file name of raw data
default_values['UTC'] = 0  # recording time, extracted from file

default_values['PxSzX'] = '0.0'  # um per pixel, 1.5625 for 50x air objective, measured by Hanna Schnell July 2017 on Till vision system, with a binning of 8
default_values['PxSzY'] = '0.0'  # um per pixel, 1.5625 for 50x air objective, measured by Hanna Schnell July 2017 on Till vision system, with a binning of 8

default_values['Lambda'] = 0  # wavelength of stimulus. In TILL, from .log file, In Zeiss LSM, from .lsm file

# These will be automatically filed for LE_loadExp=4
default_values['dbb2'] = 'none'  # file name of raw data in dual wavelength recordings (FURA)

# To include more columns, uncomment entries below and specify a default value.
# #
# block for first stimulus
# default_values['StimON'] = -1  # stimulus onset, unit: frames, count starts at frame 1.
# default_values['StimOFF'] = -1  # stimulus offset, unit: frames, count starts at frame 1.
# default_values['StimLen'] = 0  # stimulus onset in ms from beginning - alternative to StimON
# default_values['StimONms'] = -1  # stimulus length in ms - alternative to StimOFF
# #
# block for second stimulus
# default_values['Stim2ON'] = 0  # stimulus onset, unit: frames, count starts at frame 1.
# default_values['Stim2OFF'] = 0  # stimulus offset, unit: frames, count starts at frame 1.
# default_values['Stim2Len'] = 0  # stimulus onset in ms from beginning - alternative to StimON
# default_values['Stim2ONms'] = -1  # stimulus length in ms - alternative to StimOFF
# #
# default_values['Age'] = -1
# default_values['Sex'] = 'o'
# default_values['Side'] = 'none'
# default_values['Comment'] = 'none'
# #
# default_values['MTime'] = 0
# default_values['Control'] = 0
# default_values['Pharma'] = 'none'
# default_values['PhTime'] = 0
# default_values['PhConc'] = 0
# default_values['ShiftX'] = 0
# default_values['ShiftY'] = 0
# default_values['StimISI'] = 0
# default_values['setting'] = 'none'
# default_values['dbb3'] = 'none'
# default_values['PosZ'] = 0
# default_values['Countl'] = 0
# default_values['slvFlip'] = 0
# ----------------------------------------------------------------------------------------------------------------------

# ----------------- A function used to modify list entries after automatic parsing of metadata -------------------------
# ----------------- This function indicates what needs to be done for a row --------------------------------------------
# ----------------- The same is internally applied to all rows of the measurement list----------------------------------



# def get_odorinfo_from_label(label):

# # format for file name (label) is: 
# # odor_concentration_anything_else.tif
# # separating element is underscore
#     # is the information for a concentration present? Detect "-"
#     parts = label.split("_")
#     if len(parts) > 1:
#         odor = parts[0] 
#         concentration = parts[1] 
#         # in the case the name is odor_conc.tif:
#         if concentration[-4:] == '.tif':
#             concentration = concentration[:-4]
#     else:
#         odor = 'odor?'
#         concentration = 'conc?'
#     return [odor, concentration]


# Inga's data is very large. Apply post-hoc binning?
# e.g., with post_hoc_binning of 8, the 1024x1023 images will be 128x128 large - good to see and compare many measurements simultaneously
# with binning of 4, we get 256x256, which is already high resolution
# if set to 0, thos is not used. 
# if set to a value (has to be a divisor of both axes, in the case of 1024x1024 a multiple of 2)
# we will create a second path structure, and save binned data there, and create an appropriate .lst file
# format will be single multilayer tiff file
bin_post_hoc = 8
bin_data_format = 33 # 33 means generic multilayer tif file. Check which are possible below
bin_Datapath = r"01_DATA_BIN"
# path of the "Lists" folder in VIEW organization containing the list files
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
bin_OdorInfoPath = r"02_LISTS_BIN"






def custom_func(list_row: pd.Series, animal_tag: str) -> pd.Series:

    
#TODO
#add info "analyze" and set to 0 for snapshots
    # Examples:
    # list_row["StimON"] = 25
    # list_row["Odour"] = get_odor_from_label(list_row["Label"])
    # if list_row["Measu"]
    # get Odor from another file based on the value of <animal_tag> and list_row["Label"]
    # list_row["StimONms"] = '3000'
    # list_row["StimLen"]  = '2000'
    # list_row["Comment"]  = 'create_measurement_list_lif'
    # list_row["Line"]     = 'bee'
    
#extract odor and concentration from name
#    (list_row["Odour"],list_row["OConc"]) = get_odorinfo_from_label(list_row["Label"])
    # try:
    #     float(list_row["OConc"])
    # except: #Odour concentration is not a number, set to fictive 0
    #     list_row["OConc"] = '0.0'
    
    # if  list_row["Label"][-4:] == '.tif':
    #         list_row["Label"] = list_row["Label"][:-4]
        
    return list_row

# ----------------------------------------------------------------------------------------------------------------------

# ------------------ A function defining the criteria for excluding measurements ---------------------------------------
# ------------------ Currently applicable only for tillvision setups ---------------------------------------------------


def measurement_filter(s):
    # exclude blocks that have in the name "Snapshot" or "Delta"
    # or that do not have any "_"
    name = s["Label"]
    label_not_okay = name.count('Snapshot') > 0 # or name.count('Delta') > 0 or name.count('_') < 1
    label_okay = not label_not_okay

    # # exclude blocks with less than two frames or no calibration
    # atleast_two_frames = False
    # if type(s["Timing_ms"]) is str:
    #     if len(s["Timing_ms"].split(' ')) >= 2 and s["Timing_ms"] != "(No calibration available)":
    #         atleast_two_frames = True

    return label_okay # and atleast_two_frames

#inga has very large data - create a software 'binning' as if that would have been on chip
def binning_2D(in_array, binning_factor=4):
    #create my own resampling filter (binning)
    #binning_factor = 4
    dims = list(in_array.shape)
    new_dims = [int(dim/binning_factor) for dim in dims]
    new_array = np.zeros(new_dims, dtype='float')
    for i in  range(new_dims[0]):
        for j in range(new_dims[1]):
            #fill i,j of new array
            new_array[i,j] = np.mean(
                in_array[i*binning_factor:(i+1)*binning_factor,
                      j*binning_factor:(j+1)*binning_factor])
    new_array = new_array.astype(int)
    return new_array

def binning_3D(in_array, binning_factor=4, axis=2):
    #create my own resampling filter (binning)
    #default binning_factor = 4
    #time axis is axis 2, not binned by default
    print('Running binning_3D - slow implementation, please wait...')
    if axis != 2:
        print('Only implemented for Axis equals 2! ')
    dims = list(in_array.shape)
    new_dims = [int(dim/binning_factor) for dim in dims]
    new_dims[axis] = dims[axis] # do not change time dimension
    new_array = np.zeros(new_dims, dtype='float')
    for t in range(new_dims[axis]): #go through timepoints
        for i in  range(new_dims[0]):
            for j in range(new_dims[1]):
                #fill i,j of new array
                new_array[i,j,t] = np.mean(
                    in_array[i*binning_factor:(i+1)*binning_factor,
                             j*binning_factor:(j+1)*binning_factor,
                             t])
    new_array = new_array.astype(int)
    print('...done binning_3D - slow implementation, thanks for waiting!')
    return new_array



# ______________________________________________________________________________________________________________________

# fle = '/Users/galizia/Documents/DATA/inga_calcium/01_DATA/220609_Animal46_greg_socialmodulation/Trial01/protocol.txt'

if __name__ == "__main__":

    # initialize a FlagsManager object with values specified above
    flags = FlagsManager()
    flags.update_flags({"STG_MotherOfAllFolders": STG_MotherOfAllFolders,
                        "STG_OdorInfoPath"      : STG_OdorInfoPath,
                        "STG_Datapath"          : STG_Datapath})

    # initialize importer
    importer_class = get_importer_class(LE_loadExp)
    importer       = importer_class(default_values)

    # open a dialog for choosing raw data files
    # this returns a dictionary where keys are animal tags (STG_ReportTag) and
    # values are lists of associated raw data files
    animal_tag_raw_data_mapping = importer.ask_for_files(default_dir=flags["STG_Datapath"])
    # make sure some files were chosen
    assert len(animal_tag_raw_data_mapping) > 0, IOError("No files were chosen!")

    for animal_tag, raw_data_files in animal_tag_raw_data_mapping.items():
        print('running ', animal_tag, raw_data_files)

        # automatically parse metadata
        metadata_df = importer.import_metadata(raw_data_files=raw_data_files,
                                               measurement_filter=measurement_filter)
        # inform user if no usable measurements were found
        if metadata_df.shape[0] == 0:
            logging.info(f"No usable measurements was found among the files "
                         f"chosen for the animal {animal_tag}. Not creating a list file")
        else:
            # create a new Measurement list object from parsed metadata
            # but this gets everything messed up
            # was copied from another version (LIF?)
            # measurement_list = MeasurementList.create_from_df(LE_loadExp=LE_loadExp,
            #                                                    df=metadata_df)

            # # apply custom modifications
            metadata_df['OConc'] = 0 #
            ## rename from Inga nomenclature to VIEW nomenclature
            metadata_df = metadata_df.rename(columns={'S1_on':'StimON', 
                                                      'S1_off':'StimOFF', 
                                                      'S2_on':'Stim2ON',
                                                      'S2_off':'Stim2OFF',
                                                      'Stimulus':'Odour',
                                                      'DBB_Folder':'DBB1'})
            # measurement_list.update_from_custom_func(custom_func=custom_func, animal_tag=animal_tag)

            # shift a few columns to the front
            cols_to_move = ['Measu','Analyze','Label', 'Odour', 'OConc']
            metadata_df = metadata_df[ cols_to_move + [ col for col in metadata_df.columns if col not in cols_to_move ] ]

            #because ILTIS uses column 'Stimulus' and not 'Odour', duplicate that information
            metadata_df['Stimulus'] = metadata_df['Odour']

            # # set anaylze to 0 if raw data files don't exist
            # flags.update_flags({"STG_ReportTag": animal_tag})
            # measurement_list.sanitize(flags=flags,
            #                           data_file_extensions=importer.movie_data_extensions)

            # # sort by time as in column "UTC"
            # #sorted_df = df.sort_values(by=['Column_name'], ascending=True)
            # # does not work if the list file already existed. 
            # measurement_list.measurement_list_df = measurement_list.measurement_list_df.sort_values(by=['UTC'], ascending=True)


            # construct the name of the output file
            outputfile = pl.Path(STG_MotherOfAllFolders) / STG_OdorInfoPath
            # for the file name, take the label of the first measurement
            fle_name = f"{metadata_df['Label'][0]}{measurement_output_extension}"
            outputfile = outputfile / fle_name
            

            # write measurement file to list
            # measurement_list.write_to_list_file(lst_fle=outputfile, columns2write=default_values.keys(),
            #                                     overwrite_old_values=overwrite_old_values)
            metadata_df.to_excel(outputfile)
            print('create_measurement_list_inga. Written file to: ', outputfile)

###############################            
            # List-file has been created for this animal. 
            # Now, do we need post-hoc binning?
            if bin_post_hoc: # value other than 0
                #load object for Inga file types, using the .txt file
                # go through each measurement in this .lst file
                for index, row in metadata_df.iterrows():   
                    #first test that this value is possible 
                    print('Running stack ', index+1 , ' of ', len(metadata_df), ' measurements')
                    if (row['FrameSizeX'] % bin_post_hoc != 0) or (row['FrameSizeY'] % bin_post_hoc != 0):
                        print('ERROR: post-hoc binning needs a true divisor of the frame size')
                        raise NotImplementedError(f"Change the program! bin_post_hoc is: {bin_post_hoc}")

            # read data into memory
                    txt_file = raw_data_files[0]
                    measu = row['Measu']
                    this_stack = read_SingleWavelengthTif_MultiFileInga(txt_file, measu)
                    
            # reduce data size
                    new_stack = binning_3D(this_stack, binning_factor=bin_post_hoc, axis=2)
            # save stack data into folder 01_DATA_SM
                    outputfile = pl.Path(STG_MotherOfAllFolders) / bin_Datapath / row['Label']#/ fle
                    outputfile.mkdir(parents=True, exist_ok=True)
                    fle = row['Label']+'_'+str(index)+'.tif'
                    outputfile = outputfile / fle
                    write_tif_2Dor3D(new_stack, outputfile, dtype=None, scale_data=False, labels=None)
            # change DBB1, sizeX, sizeY
                    metadata_df.at[index,'FrameSizeX'] = row['FrameSizeX'] // bin_post_hoc
                    metadata_df.at[index,'FrameSizeY'] = row['FrameSizeY'] // bin_post_hoc
                    metadata_df.at[index,'PxSzX'] = row['PxSzX'] / bin_post_hoc
                    metadata_df.at[index,'PxSzY'] = row['PxSzY'] / bin_post_hoc
                    metadata_df.at[index,'DBB1'] = row['Label']+'/'+ fle
                    metadata_df.at[index,'AnimalLabel'] = row['Label'] # for filename creation
                    metadata_df.at[index,'Label'] = row['Label']+'_'+str(index)
                    metadata_df.at[index,'dbb2'] = ' '
                    metadata_df.at[index,'Comment'] = 'Inga Post-Hoc Binned data '

            # save file as fle_SM.
            metadata_df.pop('dbb2')
            outputfile = pl.Path(STG_MotherOfAllFolders) / bin_OdorInfoPath
            outputfile.mkdir(parents=True, exist_ok=True)
            # for the file name, take the label of the first measurement
            fle_name = f"{metadata_df['AnimalLabel'][0]}{measurement_output_extension}"
            outputfile = outputfile / fle_name
            

            # write measurement file to list
            # measurement_list.write_to_list_file(lst_fle=outputfile, columns2write=default_values.keys(),
            #                                     overwrite_old_values=overwrite_old_values)
            metadata_df.to_excel(outputfile)
            print('create_measurement_list_inga. Written binned file to: ', outputfile)
            
            
            


