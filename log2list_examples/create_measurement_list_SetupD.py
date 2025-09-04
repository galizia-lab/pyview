#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Mother of all Folders of your dataset
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
#STG_STG_STG_MotherOfAllFolders = r"/home/ajay/Nextcloud/VTK_2021/bee/HS_210521_test"
#STG_STG_STG_MotherOfAllFolders = r"/Users/galizia/Documents/DATA/VTK_test/YT_VTK"
#STG_STG_STG_MotherOfAllFolders = r"/Users/galizia/Documents/DATA/HS_210521_test"
#STG_MotherOfAllFolders = r"/Users/galizia/Nextcloud/VTK_2021/Bee_alarm_2022" # 01_DATA
STG_MotherOfAllFolders = r'/Users/galizia/Documents/DATA/elisabeth'
create_animal_list_file = True
show_correlation_plot = True

"""
Log2List for setupD


created June2022, based on pervious VTK2021 log2list
@author: galizia
last work: July 2025
Gio: environment ms_fid_2024

Opens a window, asks for till-photonics .log files
In the same folder, we expect the .txt file from Chronos/PAL


    1) read a .log file (Till Photonics), create a .lst file for this animal
    2) read a .txt file that comes from PAL/Chronos (Barcode Reader), add odor information to .lst file

    If there are more measurements in Chronos than in Till: fail
    If there are more measurements in Till than in Chronos: try to find the "hand-stimulus"

Structure:
    Set STG_MotherOfAllFolders first!
    
    Data (.log and .txt files) should be in subfolder 01_DATA
    List file goes into subfolder 02_LISTS
    
Naming of odorants/Stimuli:
    Within Till, names were ODOR-CONC_NUMBER,
    e.g. ISOE-5_10
    Extract these name using function get_odor_info_from_label_standard
    
    BUT
    
    Odor name and other information is taken from the Chronos file, not from Till!
    IF there are handgiven stimuli, change the label in TILL to odor_hand or odor_handgiven
    Program searches for 'hand' in the name, and extracts before underscore as odor

    Barcode reader (Chronos) gives information about the odor, concentration, user and date
    e.g. ISOE2HS2312
    where ISOE2 is the odor, HS23 is the user, 12 is the month
    If the odor is MOL, then the next two digits are the concentration, otherwise it
    is the next digit.

    New format for Chronos is (as of 2025)
    ISOE12-250612 or MOL12-250612 or ISOE2-250612
    where ISOE is the odor, then 1 or 2 digits concentration, then '-', then 250612 is the date in format YYMMDD
"""


from view.python_core.measurement_list import MeasurementList
from view.python_core.measurement_list.importers import get_importer_class
from view.python_core.flags import FlagsManager
from view.python_core.measurement_list.io import XLSIO

from collections import OrderedDict
import pandas as pd
import logging
import datetime as dt
import matplotlib.pyplot as plt
from numpy.polynomial.polynomial import polyfit
import numpy as np
import pathlib
import sys
import re
import os

logging.basicConfig(level=logging.INFO)

# ------------------- Some parameters about experimental setup, data structure and output file type --------------------
# 3 for single wavelength Till Photonics Measurements
# 4 for two wavelength Till Photonics Measurements
# 20 for Zeiss Confocal Measurements
LE_loadExp = 3



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

# ------------------ names of columns that will be overwritten by old values -------------------------------------------
# ------ these will only be used if a measurement list file with the same name as current output file exists -----------

overwrite_with_old_values = ["Line", "PxSzX", "PxSzY", "Age", "Sex", "Prefer",
                         "Comment", "Analyze", "Odour", "OConc"]


default_values = OrderedDict()

default_values['Measu'] = 0  # unique identifier for each line, corresponds to item in TILL photonics log file

default_values['Label'] = "none"
default_values['Odour'] = 'odor?'  # stimulus name, maybe extracted from label in the function "custom_func" below
default_values['OConc'] = 0  # odor concentration, maybe extracted from label in the function "custom_func" below
default_values['Analyze'] = -1  # whether to analyze in VIEWoff. Default 1

default_values['Cycle'] = 0  # how many ms per frame
default_values['DBB1'] = 'none'  # file name of raw data
default_values['UTC'] = 0  # recording time, extracted from file

default_values['PxSzX'] = '1.25'  # um per pixel, 1.5625 for 50x air objective, measured by Hanna Schnell July 2017 on Till vision system, with a binning of 8
default_values['PxSzY'] = '1.25'  # um per pixel, 1.5625 for 50x air objective, measured by Hanna Schnell July 2017 on Till vision system, with a binning of 8
default_values['Comment']  = 'PixelSize for 20x binninb=4'

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
default_values['Line'] = 'bee'
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

def get_odorinfo_from_label_standard(label):
    # format for label is: concentration to the right, with a minus sign
    # Odor next to it, separated by underscore
    # IMPERARIVE: only ONE "-"
    
    # format ISOE-2_13 or MOL_18

    # is the information for a concentration present? Detect "-"
    parts = label.split("_")
# take first part
    parts = parts[0]
    parts = parts.split("-")
    odor = parts[0]
    if len(parts) > 1:
        concentration = '-' + parts[1] 
    else:
        concentration = '0'
    return [odor, concentration]

def get_odorinfo_from_label(label):
    # for hand given stimuli only ODOR is given, no concentration
    # e.g. "NONL_hand"
    parts = label.split("_")
# take first part
    odor = parts[0]
    #concentration = 0
    return odor # [odor, concentration]

def get_odorinfo_from_chronos(label):
    # format for label in chronosis:
    # ROAI0HS223
    # first 4 are the odor (exeption: MOL, which leads to a shift in all subsequent positions)
    # next position is concentration if only single digit, else two positions is concentration
    # next two positions is user
    # next two positions is year
    # next position or two positions is month (all positions starting with 1)
    # examples: 
    # label = 'M2HN10HS2312'
    # label = 'M2HN9HS231'
    # label = 'MOL0HS231'
    #extract beginning: odor

# new format for chronos is:
    # New format for Chronos is (as of 2025)
    # ISOE12-250612 or MOL12-250612 or ISOE2-250612
    # where ISOE is the odor, then 1 or 2 digits concentration, then '-', then 250612 is the date in format YYMMDD


    new_re = re.compile(r"^(?P<odor>MOL|.{4})(?P<conc>\d{1,2})-(?P<date>\d{6})(?P<rest>.*)")
    old_re = re.compile(r"^(?P<odor>MOL|.{4})(?P<conc>\d{1,2})(?P<user>[a-zA-Z]{1,2})(?P<date1>\d{2})(?P<rest>.*)")


    match = new_re.match(label) or old_re.match(label)

    if not match:
        raise ValueError("Unrecognized label format")

# Access using match.group('prefix'), etc.
    odor = match.group('odor')
    concentration = '-' + str(match.group('conc'))
    # not all values are in all label formats, so use get to avoid KeyError
    result = match.groupdict()
    OdorUser = result.get('user', 'unknown')  # user is not always present, e.g. in MOL
    SampleDate = result.get('date', None)
    if not SampleDate:
        # if SampleDate is not present, it is in the old format, so use date1+rest
        SampleDate = result.get('date1', None)
        if SampleDate:
            SampleDate =  SampleDate + '/' + result.get('rest', '')

    return [odor, concentration, OdorUser, SampleDate]


def custom_func(list_row: pd.Series, animal_tag: str) -> pd.Series:
    #when stimuli are controlled by Till-System, adjust frame number accordingly
    if list_row['StimON']   == 'TTLOut2':
        list_row['StimON']   = 24
        # calculate frame of stimOFF
        list_row['StimOFF'] = int(int(list_row['StimON'])+int(list_row['StimLEN'])/list_row['Cycle'])
        
    if 'Stim2ON' in list_row:
        if list_row['Stim2ON']   == 'TTLOut2':
            list_row['Stim2ON']   = 36
        # calculate frame of stimOFF
        list_row['Stim2OFF'] = int(int(list_row['Stim2ON'])+int(list_row['Stim2LEN'])/list_row['Cycle'])
    # list_row['StimLen']  = 1000 
    # list_row['Stim2ON']  = 36
    # list_row['Stim2Len'] = 1000 
    # list_row['Line']     = 'bee'
    # # Examples:
    # list_row["StimON"] = 25
    if 'hand' in list_row['Label'].lower(): # hand stimulus, and TILL label contains hand
        list_row["Odour"] = get_odorinfo_from_label(list_row["Label"])        
    else:
        (list_row["Odour"],list_row["OConc"],list_row["OdorUser"],list_row["OdorDate"]) = get_odorinfo_from_chronos(list_row["Barcode"])
    
    if list_row['DualArm']   == 'Yes':
        (list_row["Odour_2"],list_row["OConc_2"],list_row["OdorUser_2"],list_row["OdorDate_2"]) = get_odorinfo_from_chronos(list_row["Barcode_2"])
    # if list_row["Measu"]
    # get Odor from another file based on the value of <animal_tag> and list_row["Label"]
    return list_row


# ----------------------------------------------------------------------------------------------------------------------

# ------------------ A function defining the criteria for excluding measurements ---------------------------------------
# ------------------ Currently applicable only for tillvision setups ---------------------------------------------------


def measurement_filter(s):
    # exclude blocks that have in the name "Snapshot" or "Delta"
    # or that do not have any "_"
    name = s["Label"]
    label_not_okay = name.count('Snapshot') > 0 or name.count('Delta') > 0 or name.count('_') < 1
    label_okay = not label_not_okay

    # exclude blocks with less than two frames or no calibration
    atleast_two_frames = False
    if type(s["Timing_ms"]) is str:
        if len(s["Timing_ms"].split(' ')) >= 2 and s["Timing_ms"] != "(No calibration available)":
            atleast_two_frames = True

    return label_okay and atleast_two_frames


# ______________________________________________________________________________________________________________________
# ______________________________________________________________________________________________________________________
# section for chronos specific routines, to be modified into object later


def get_chronos_filename(logfilename, str_pos=0, chronosfilename=None):
    '''

    Parameters
    ----------
    logfilename : TYPE
        full path with filename for .log file from till photonics.
    str_pos : TYPE, optional
        DESCRIPTION. The default is 0.
        used to go through the positions os all possible file names
    chronosfilename : TYPE, optional
        DESCRIPTION. The default is None.
        list of all filenames in the directory, sequentially reduced to the only one

    Returns
    -------
    chronosfilename : TYPE
        DESCRIPTION.
        the file name in the directory that has the longest equality to logfilename

    '''
    if isinstance(logfilename, (list, tuple)):
        # logfilename is a list, with the only entry logfilename
        # ask for the list, so it also works if logfilename is the filename only, i.e. in the iteration
        logfilename = logfilename[0]
    if not chronosfilename:
        # first run, get list of all filenames in the directory that belongs to logfilename
        logfilename_directory = pathlib.Path(logfilename).parents[0]
        chronosfilename = [item.name for item in logfilename_directory.glob("*.txt")]
        # keep only files that end in '.txt'

    log_filename = pathlib.Path(logfilename).name
    chronosfilename = [f for f in chronosfilename if f[str_pos] == log_filename[str_pos]]
    str_pos += 1
    # iterate if more than one solution
    if len(chronosfilename) == 0:
        print('')
        print('ERROR:')
        print('create_measurement_list_SetupD: no or more than one compatible chronos file found for: ')
        print(logfilename)
        return('')
    if len(chronosfilename) > 1:
        chronosfilename = get_chronos_filename(logfilename, str_pos, chronosfilename)
    return chronosfilename



def read_chronos_file_old(fle, path_to_fle):
    '''
 Reads a chronos file, returns information as a dataframe
 This is the obsolete old program, where Chronos information was in a single line
 can be deleted, for now (Mar 23) I keep it in case I would need some info from it
 
    '''
    #fle = '/Users/galizia/Nextcloud/VTK_2021/Bee_alarm_2022/01_DATA/HS_220607_ChronosLog.txt'
    #line = '2022-06-07 12:26:12	Samplename Right arm (DoubleStim_RightArm.cam):  ISOE3HS225'
    if isinstance(fle, (list, tuple)):
        # logfilename is a list, with the only entry logfilename
        # ask for the list, so it also works if logfilename is the filename only, i.e. in the iteration
        fle = fle[0]
    print('opening chronos file: ', fle)
    fle = path_to_fle / fle
    chronos_df = pd.DataFrame()
    with open(fle, encoding='utf-8-sig') as f:
        for line in f:
            if len(line) <= 20: #if the line is too short, it cannot be
            # for now, I take every line that is as long as the timestamp
                pass
            else: # there is something in the line.
                linedict = {}
                timestamp = line[0:20].strip() #e.g. '2022-06-07 12:26:12'
                # convert datetime
                fmt = "%Y-%m-%d %H:%M:%S"
                measurementtime = dt.datetime.strptime(timestamp, fmt)
                linedict['ChronosTime'] = measurementtime

                # take the reminder of the line
                line = line[20:]
                colon_split = line.split(':') 
                linedict['Comment'] = colon_split[0].strip()
                linedict['Stimulus'] = colon_split[1].strip() # e.g. 'ISOE3HS225'
                
                # Append this line to the dataframe
                chronos_df = pd.concat([chronos_df, pd.DataFrame([linedict])], ignore_index=True)
    # sort in ascending order, just in case chronos was not
    chronos_df = chronos_df.sort_values(by='ChronosTime',ascending=True)

    return chronos_df


def read_chronos_file(fle, path_to_fle):
    """
    Written March 2023 
    
    Parse text at given filepath
    from: https://www.vipinajayakumar.com/parsing-text-with-python/
    
    for more complex regex, see
    https://stackoverflow.com/questions/47982949/how-to-parse-complex-text-files-using-python

    Parameters
    ----------
    fle, path_to_fle
        Filepath for file to be parsed

    File is a Chronos .txt file. Information is in blocks,
    Block starts with a timestamp at the beginning of the line
    Block ends with <End Of Measurement> line

    Returns
    -------
    data : pd.DataFrame
        Parsed data

    """
    #fle = '/Users/galizia/Nextcloud/VTK_2021/Bee_alarm_2022/01_DATA/HS_220607_ChronosLog.txt'
    #line = '2022-06-07 12:26:12	Samplename Right arm (DoubleStim_RightArm.cam):  ISOE3HS225'
    if isinstance(fle, (list, tuple)):
        # logfilename is a list, with the only entry logfilename
        # ask for the list, so it also works if logfilename is the filename only, i.e. in the iteration
        fle = fle[0]
    print('opening chronos file: ', fle)
    filepath = path_to_fle / fle

    data = []
    dict_of_data = dict()
    with open(filepath, 'r', encoding='utf-8-sig') as file:
        SecondTimestamp = False #first group is a new group
        line = file.readline()
        while line:
            reg_match = _RegExLib(line)

            if reg_match.TimeStampLine:
                dict_of_data.update({'ChronosTimeStamp' : reg_match.TimeStampLine.group(1).strip()})
                # fmt = "%Y-%m-%d %H:%M:%S"
                # measurementtime = dt.datetime.strptime(reg_match.TimeStampLine.group(1).strip(), fmt)
                # dict_of_data.update({'ChronosTime' : measurementtime})

                for i in range(2,6): #ranges from 2 to 5 included
                    items   = reg_match.TimeStampLine.group(i).split(':')
                    items = [x.strip() for x in items] # remove blanks
                    print(items)
                    if SecondTimestamp: items[0] = items[0] + '_2'
                    dict_of_data.update({items[0]:':'.join(items[1:])})
                SecondTimestamp = True # next one will be a second timestamp                    

            elif reg_match.VariableInfo:
                value_type = reg_match.VariableInfo.group(1).strip()
                value      = reg_match.VariableInfo.group(2).strip()
                dict_of_data.update({value_type : value})

            elif reg_match.Endblock:
                SecondTimestamp = False #block ends here, so next one is a new group
                data.append(dict_of_data) # add all values to the list
                dict_of_data = dict() # delete the dictionary

            line = file.readline()

    data_df = pd.DataFrame(data)
    # data.set_index(['School', 'Grade', 'Student number'], inplace=True)
    #     # consolidate df to remove nans
    # data = data.groupby(level=data.index.names).first()
    #     # upgrade Score from float to integer
    # data = data.apply(pd.to_numeric, errors='ignore')
    return data_df


class _RegExLib:
    """Set up regular expressions"""
    # use https://regexper.com to visualise these if required
    #line = '2023-03-15 10:39:39	Barcode:  ISOE2HS231; Tool: HS 1; Position: Tray Holder 2:Slot1:9;' 
    _reg_TimeStampLine = re.compile(r'^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\t(.+);(.+);(.+);(.+)$')
    #end of block
    #line = '<End Of Measurement>'
    _reg_EndBlock = re.compile(r'<End Of Measurement>')
    # any entry in between, syntax is:  'Label : Value'
    # line = 'StimON: TTLOut2'
    _reg_VariableInfo = re.compile(r'^(.+?):(.+)$') #.+? is non-gready, therefore first colon is used
   
    def __init__(self, line):
        # check whether line has a positive match with all of the regular expressions
        self.TimeStampLine = self._reg_TimeStampLine.match(line)
        self.Endblock = self._reg_EndBlock.match(line)
        self.VariableInfo = self._reg_VariableInfo.match(line)

def plotTill_vs_Chronos_times(inDF, tillColumn, chronosColumn):
    '''

    Parameters
    ----------
    tillColumn : TYPE
        DESCRIPTION. column name for UTC times
    chronosColumn : TYPE
        DESCRIPTION. column name for UTC times

    Returns
    -------
    Plot on screen, to check that the time follow a linear shape.

    '''
    x = np.array([float(i) for i in inDF[chronosColumn]])
    y = np.array([float(i) for i in inDF[tillColumn]]) #'UTC
    starttime = min(np.nanmin(x),np.nanmin(y))
    x = (x-starttime)/60.0
    y = (y-starttime)/60
    idx = np.isfinite(x) & np.isfinite(y) #drop NaN
    b, m = polyfit(x[idx], y[idx], 1) # fit a line

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(x, y,marker='.', c='green')
    ax.plot(x, b + m * x, '-')
    ax.set_xlabel("Chronos-time (minutes)")
    ax.set_ylabel("Till-time (minutes)")
    ax.set_title(animal_tag+'.  N ='+str(len(x)))
    if show_correlation_plot: plt.show()
    # on my mac environment, this crashes often, so I use show_correlation_plot
    plt.close()
    
def print_debug_info(all_df, chronos_df, animal_tag):
        print('Here are the Till measurements and the chronos times:')
        inspection_df = pd.DataFrame({
            "Till_Label": all_df["Label"],
            "Till_MTime": all_df["MTime"],
            "Chronos_Timestamp": chronos_df["ChronosTimeStamp"],
            "Barcode": chronos_df["Barcode"]
        })

        inspection_df["Chronos_ExpTime"] = (
            inspection_df["Chronos_Timestamp"] - chronos_df["ChronosTimeStamp"].min()
        )

        print("\nSide-by-side DataFrame:\n")
        print(inspection_df.to_string(index=False))  # no row index for cleaner debug view


def integrate_chronosInfo(chronos_df, all_df, animal_tag):
    '''
    Integrates Till and Chronos information about the measurements

    Parameters
    ----------
    chronos_df : TYPE
        dataframe with all chronos info.
    all_df : TYPE
        dataframe for output list, as created from till photonics data.

    Returns
    -------
    updated all_df.

    '''

    # convert date_string to datetime object
    chronos_df['ChronosTimeStamp'] = pd.to_datetime(chronos_df['ChronosTimeStamp'], format='%Y-%m-%d %H:%M:%S')
    chronos_df['ChronosUTC'] = pd.Series(chronos_df['ChronosTimeStamp'].apply(dt.datetime.timestamp).apply(int))
    #add animal tag to df
    all_df['Animal'] = animal_tag
    
    #move all columns from chronos into the main df; but crashes because some columns have same name. 
    #but first, rename 'Comment' because it exists in both all_df and chronos_df
    chronos_df = chronos_df.rename(columns={'Comment': 'ChronosComment'})

    
    # merge the dataframes, taking columns with the same name from df2
    #all_df = all_df.merge(chronos_df, on=all_df.columns.intersection(chronos_df.columns).tolist(), how='left')


    if len(all_df['UTC']) == len(pd.Series(chronos_df['ChronosTimeStamp'])):
        # the two sources TILL and Chronos have equal length, so join them into one
        new_df = pd.concat([all_df, chronos_df], axis=1)
        # give visual output to check that chronos and till times work together
        # x = all_df['ChronosUTC'].to_list()
        # y = all_df['UTC'].to_list()
        plotTill_vs_Chronos_times(new_df, 'UTC', 'ChronosUTC')
        
    elif len(all_df['UTC']) < len(pd.Series(chronos_df['ChronosTimeStamp'])):
        print('')
        print('More Chronos entries than Till-Imaging entries in: ', animal_tag)
        print_debug_info(all_df, chronos_df, animal_tag)
        sys.exit('ERROR: Incompatible length of data rows')

    else: #if len(all_df['UTC']) > len(pd.Series(chronos_df['ChronosTimeStamp'])):
        print('')
        print('Less Chronos entries than Till-Imaging entries in: ', animal_tag)
        print('Trying to find the hand-stimulus measurements')
        
        #check if the Labels in TILL contain 'hand' in some places
        if sum(~all_df['Label'].str.contains('hand')) == len(pd.Series(chronos_df['ChronosTimeStamp'])):
            print('Number of "hand" measurements matches the overnumerary measurements - use labels')
            # join all those measurements that do not contain 'hand'
            Till_noHand = all_df[~all_df['Label'].str.contains('hand')]
            Till_noHand.reset_index(drop=True, inplace=True)  # reset index for concat                  
            chronos_df.reset_index( drop=True, inplace=True)  # reset index for concat                  
            new_df = pd.concat([Till_noHand, chronos_df], axis=1, join='inner')
            #new_df now contains all measurements done with Chronos

            # join those that contain 'hand' as rows
            new_df = pd.concat([all_df[all_df['Label'].str.contains('hand')], new_df], axis=0)
            new_df.sort_values(by='UTC', inplace=True)
            new_df.reset_index(drop=True, inplace=True)  # reset index for concat                  
            plotTill_vs_Chronos_times(new_df, 'UTC', 'ChronosUTC') #visual feedback
        else:
            print('More TILL than Chronos measurements found - change label in Till adding the string "hand" or check for old chronos entries')
            print('Alternative, develop program to spot the hand-given measurements in create_measurement_list_SetupD.py')
            print_debug_info(all_df, chronos_df, animal_tag)
            sys.exit('ERROR in integrate_Chronosinfo: Incompatible length of data rows')

    return new_df

# ______________________________________________________________________________________________________________________


def add_to_AnimalListFile(list_filepath, settings_df):
    """
    Adds a line for this animal to the excel file that lists all animals.
    Done Aug. 2025, Giovanni. Based on gerstel2settings in the FID folder
    Unlike gerstel2settings, uses info in memory 
    """
    
    settings_first_row = settings_df.iloc[0]
    # settings file loaded. Extract info
    this_Animal   = settings_first_row["Animal"]
    this_refOdor  = 'unknown'
    this_Sex      = 'unknown' # settings_first_row['sex']  # take from first line
    this_Age      = 'unknown' # settings_first_row['age']
    this_Bodyside = 'unknown' # settings_first_row['side']
    this_Version  = 'unknown' # settings_first_row['version']
    this_Line     = settings_first_row['Line']
    this_Setup    = 'D' # settings_first_row['Setup'] # flags["default_setup"]  # variable from outside
    # now the empty entries, to be filled with comments
    this_Analyze          = -1  # default is 1, needs to be changed to 1 in excel for animals to consider,
                                # can be changed to 0 in excel for animals to ignore
    this_RefOdorComment   =  'none'
    this_AreaComment      =  'none'
    this_MovementComment  =  'none'
    this_CheckComment     =  'none'
    this_CheckComplete    =  0 # no check done yet, set to 1 when done
    this_DateComplete     = '08.03.1997'

    # date taken from "UTC" entry of first measurement
    this_Date = pd.to_datetime(settings_first_row["UTC"], unit='s').strftime("%y%m%d")

    #when movement correction is done, include info here
    this_MovementSize = 0
    this_MovementComment = 'not implemented'
    
    
    # animal list file name
    # open the file, get content into a dataframe. Or initialize if not there
        #initialize if not there
        # dataframe version
    # what is to be saved? Create labels for DF
    animals_labels = [
        "Animal",         # which animal is this
        "Analyze",        # set to 0 if this animal should not be considered further
        "RefOdor",        # which odor is the reference odor
        "MovementSize",   # once we'll have automatic movement correction, there should be a magnitude of the necessary correction
        "MovementComment",# text comment, by opearator
        "CheckComment",   # text comment, by opearator
        "CheckComplete",  # text comment, by opearator
        "DateComplete",   # text comment, by opearator
        #"Stimuli",       # format: odor,odor,odor
        #"StimuliConc",   # concentrations, format: -2,-4,-6
        "Sex",            # m/f
        "Age",            #
        "BodySide",       # l/r
        "Version",        # e.g. 'oct18'
        "Line",           #
        "Setup",          #
        "Date",
        #"blankOdors",
        ]
    animals_lst = pd.DataFrame(columns=animals_labels)        
    animals_lst.loc[len(animals_lst)] = \
        [
            this_Animal, this_Analyze, this_refOdor,
            this_MovementSize, this_MovementComment,
            this_CheckComment, this_CheckComplete,
            this_DateComplete,
            this_Sex, this_Age, this_Bodyside,
            this_Version, this_Line, this_Setup,
            this_Date 
         ]

    # create new df line for current animal
    # check if this animal already exists, if so, overwrite line
    # save file 
    # where do we write the animal file? Same directory as settings file
    animal_file = pathlib.Path(list_filepath).parent / 'AnimalListFile.xlsx'
    # does the file already exist? If yes, act accordingly
    if os.path.exists(animal_file):
        #read old file
        old_animals_lst = XLSIO.read(animal_file)
        # maybe that analyze existed already? In that case, keep the ANALYZE info
        old_info = old_animals_lst[old_animals_lst.Animal == animals_lst.Animal[0]]
        if (len(old_info) == 1):
            animals_lst.loc[0,'Analyze'] = old_info.iloc[0]['Analyze']

        # # if any column specified in <animals_labels> above is not found in the old animal list file, add it and fill
        # # old rows with value "unknown"
        # for col in animals_labels:
        #     if col not in animals_lst.columns:
        #         animals_lst[col] = "unkown"

        # remove this animal from the old list, if it had been included before already
        old_animals_lst = old_animals_lst[old_animals_lst.Animal != animals_lst.Animal[0]]
        # add this new animal to the old list
        animals_lst = pd.concat([old_animals_lst, animals_lst], ignore_index=True)

    # now save (overwrite)
    XLSIO.write(animals_lst, animal_file, index=False)  # save without index column

    possibly_remaining_xls = animal_file.with_suffix(".xls")
    if possibly_remaining_xls.is_file():
        possibly_remaining_xls.rename(possibly_remaining_xls.with_suffix(".xls.bak"))
    # add_to_AnimalListFile done. 
    logging.getLogger("FID").info(f"add_to_AnimalListFile done, written to {animal_file}")
#end function add_to_AnimalListFile





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
        print('running animal_tag: ', animal_tag)
        
        # automatically parse metadata
        metadata_df = importer.import_metadata(raw_data_files=raw_data_files,
                                               measurement_filter=measurement_filter)
        # inform user if no usable measurements were found
        if metadata_df.shape[0] == 0:
            logging.info(f"No usable measurements we found among the files "
                         f"chosen for the animal {animal_tag}. Not creating a list file")
        else:
# insert information from chronos
            chronos_filename = get_chronos_filename(raw_data_files)
            if len(chronos_filename) == 1: # a solution was found, i.e. a single chronos file exists
                chronos_df = read_chronos_file(chronos_filename, pathlib.Path(raw_data_files[0]).parents[0])
                metadata_df = integrate_chronosInfo(chronos_df, metadata_df, animal_tag)
    
    
    
                # create a new Measurement list object from parsed metadata
                measurement_list = MeasurementList.create_from_df(LE_loadExp=LE_loadExp,
                                                                  df=metadata_df)
    
                # apply custom modifications
                measurement_list.update_from_custom_func(custom_func=custom_func, animal_tag=animal_tag)
    
                # set anaylze to 0 if raw data files don't exist
                flags.update_flags({"STG_ReportTag": animal_tag})
                measurement_list.sanitize(flags=flags,
                                          data_file_extensions=importer.movie_data_extensions)
    
    
    
    
    
                # construct the name of the output file
                out_file = f"{flags.get_lst_file_stem()}{measurement_output_extension}"
    
                # write measurement file to list
                measurement_list.write_to_list_file(lst_fle=out_file, columns2write=default_values.keys(),
                                                    overwrite_old_values=overwrite_with_old_values)
                # inform user about the output file
                print(f"Measurement list file for {animal_tag} was created: {out_file}")

                # add line to animal list file
                if create_animal_list_file:
                    add_to_AnimalListFile(out_file, measurement_list.measurement_list_df)
