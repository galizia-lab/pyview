'''
Creates .lst file for dual wavelength TIFF files (FURA) in the format used in Trondheim
Author: Giovanni, Dec 2021, based on template in VIEW folder by Ajay

Expected data structure:
    In the folder "01_DATA", each animal has a folder, e.g. "190815_h2_El", 
        and located in that folder are all .tif files for that animal
    There is a sister folder "02_LISTS"
    
Output:
    In the folder "02_LISTS":
        There will be a file Animal.lst.xlsx, e.g. "190815_h2_El.lst.xlsx"
        That file contains one line for each measurement.
        
What to do next?
    In this file, change values that are global
    or insert a function that can extract odor name or concentration name from somewhere
    
    In the Animal.lst.xlsx file, correct/complete entries (e.g. odor names, odor concentrations)
    Make sure stimulus timing information is correct

Why do I need a .lst.xlsx file?
    Load measurements in pyVIEW using this .lst file, so that stimulus information is correct
    For off-line analysis, information is taken from this file. 

Good to know:
    Information, where possible, is taken from the OME header of the incoming tif file.
    If that information is wrong, incomplete, or else, modify the code in:
        importers.py:P1DualWavelengthTIFSingleFileImporter:parse_metadata
'''



from view.python_core.measurement_list import MeasurementList
from view.python_core.measurement_list.importers import get_importer_class
from view.python_core.flags import FlagsManager
from collections import OrderedDict
import pandas as pd
import logging
import pathlib as pl

logging.basicConfig(level=logging.INFO)

# ------------------- Some parameters about experimental setup, data structure and output file type --------------------
# 3 for single wavelength Till Photonics Measurements
# 4 for two wavelength Till Photonics Measurements
# 20 for Zeiss Confocal Measurements
LE_loadExp = 35

# Mother of all Folders of your dataset
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_MotherOfAllFolders = r"/Users/galizia/Nextcloud/VTK_2021/Bente_Test_2021"

# path of the "Data" folder in VIEW organization containing the data
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_Datapath = r""

# path of the "Lists" folder in VIEW organization containing the list files
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_OdorInfoPath = r""

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
default_values['Analyze'] = -1  # whether to analyze in VIEWoff. Default 1

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


def get_odorinfo_from_label(label):
    # format for file name (label) is: 
# odor_concentration_anything_else.tif
# separating element is underscore
    # is the information for a concentration present? Detect "-"
    parts = label.split("_")
    if len(parts) > 1:
        odor = parts[0] 
        concentration = parts[1] 
        # in the case the name is odor_conc.tif:
        if concentration[-4:] == '.tif':
            concentration = concentration[:-4]
    else:
        odor = 'odor?'
        concentration = 'conc?'
    return [odor, concentration]



def custom_func(list_row: pd.Series, animal_tag: str) -> pd.Series:

    # Examples:
    # list_row["StimON"] = 25
    # list_row["Odour"] = get_odor_from_label(list_row["Label"])
    # if list_row["Measu"]
    # get Odor from another file based on the value of <animal_tag> and list_row["Label"]
    
    list_row["StimONms"] = '3000'
    list_row["StimLen"] = '2000'
    list_row["Comment"] = 'create_measurement_list_bente'
    list_row["Line"] = 'ham'
#extract odor and concentration from name
    (list_row["Odour"],list_row["OConc"]) = get_odorinfo_from_label(list_row["Label"])
    
    
    return list_row

def measurement_filter(s):
    # exclude blocks that have in the name "Snapshot" or "Delta"
    # or that do not have any "_"
    # only necessary for old format, but not for .tif files
    name = s["Label"]
    label_not_okay = name.count('Snapshot') > 0 or name.count('Delta') > 0 or name.count('_') < 1
    label_okay = not label_not_okay

    # exclude blocks with less than two frames or no calibration
    atleast_two_frames = False
    if type(s["Timing_ms"]) is str:
        if len(s["Timing_ms"].split(' ')) >= 2 and s["Timing_ms"] != "(No calibration available)":
            atleast_two_frames = True

    return label_okay and atleast_two_frames

# ----------------------------------------------------------------------------------------------------------------------

# ------------------ A function defining the criteria for excluding measurements ---------------------------------------
# ------------------ Currently applicable only for tillvision setups ---------------------------------------------------



# ______________________________________________________________________________________________________________________


# ------------------ names of columns that will be overwritten by old values -------------------------------------------
# ------ these will only be used if a measurement list file with the same name as current output file exists -----------

overwrite_old_values = ["Line", "PxSzX", "PxSzY", "Age", "Sex", "Prefer",
                        "Comment", "Analyze", "Odour", "OConc"]

# ______________________________________________________________________________________________________________________

if __name__ == "__main__":

    # initialize a FlagsManager object with values specified above
    flags = FlagsManager()
    flags.update_flags({"STG_MotherOfAllFolders": STG_MotherOfAllFolders,
                        "STG_OdorInfoPath": STG_OdorInfoPath,
                        "STG_Datapath": STG_Datapath})

    # initialize importer
    importer_class = get_importer_class(LE_loadExp)
    importer = importer_class(default_values)

    # open a dialog for choosing raw data files
    # this returns a dictionary where keys are animal tags (STG_ReportTag) and
    # values are lists of associated raw data files
    animal_tag_raw_data_mapping = importer.ask_for_files(default_dir=flags["STG_Datapath"])
    # make sure some files were chosen
    assert len(animal_tag_raw_data_mapping) > 0, IOError("No files were chosen!")

    for animal_tag, raw_data_files in animal_tag_raw_data_mapping.items():

        # automatically parse metadata
        metadata_df = importer.import_metadata(raw_data_files=raw_data_files,
                                               measurement_filter=measurement_filter)
        # inform user if no usable measurements were found
        if metadata_df.shape[0] == 0:
            logging.info(f"No usable measurements we found among the files "
                         f"chosen for the animal {animal_tag}. Not creating a list file")
        else:
            # create a new Measurement list object from parsed metadata
            measurement_list = MeasurementList.create_from_df(LE_loadExp=LE_loadExp,
                                                              df=metadata_df)

            # apply custom modifications
            measurement_list.update_from_custom_func(custom_func=custom_func, animal_tag=animal_tag)
            

            # set anaylze to 0 if raw data files don't exist
            flags.update_flags({"STG_ReportTag": animal_tag})
            measurement_list.sanitize(flags=flags,
                                      data_file_extensions=importer.movie_data_extensions)

            # sort by time as in column "UTC"
            #sorted_df = df.sort_values(by=['Column_name'], ascending=True)
            measurement_list.measurement_list_df = measurement_list.measurement_list_df.sort_values(by=['UTC'], ascending=True)


            # construct the name of the output file
            #AskAjay - what I am writing seems crude to me (Giovanni Dec 21)
            #Ajay: out_file = f"{flags.get_lst_file_stem()}{measurement_output_extension}"
            singlefilein = pl.Path(raw_data_files[0])
            #singlefilein could be:
            #'/Users/galizia/Nextcloud/VTK_2021/Bente_Test_2021/01_DATA/190815_h2_El/B_1.tif'
            #output should be: 
            #'/Users/galizia/Nextcloud/VTK_2021/Bente_Test_2021/02_ANALYSIS/190815_h2_El.lst.xlsx'
            out_file = pl.Path(singlefilein.parent.parent.parent)
            out_file = pl.Path.joinpath(out_file,  '02_LISTS' , singlefilein.parts[-2])
            out_file = f"{out_file}{measurement_output_extension}"
    
            # write measurement file to list
            measurement_list.write_to_list_file(lst_fle=out_file, columns2write=default_values.keys(),
                                                overwrite_old_values=overwrite_old_values)



