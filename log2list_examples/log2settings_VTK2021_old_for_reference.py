# -*- coding: utf-8 -*-
"""
Program to read Till vision .log files
and write .settings.csv files

the program works like this (not all implemented yet):
- set flag settings that are default values
- read .log files and parse
- extract information that is in there

then, run Set_loca_Values_XXX, depending on reference_settings flag, e.g. 
    - get FURA measurement partners
    - set stimulus times
    - etc (all the personal information)
    - extract information from names

Since default flag settings are peculiar to every user,
and extracting information from names is too,
this program should be modified by everybody. 

Latest modification: 25.7.19 (Inga files)
Output is .lst.xls, into folder /Lists

"""

import scipy as sp
import datetime
import pandas as pd
import os
import tkinter as tk
from tkinter.filedialog import askopenfilenames
from tillvisionio.vws import  VWSDataManager
import pathlib as pl


flag_OneDirectoryUp = True #if True, settings file is saved one directory up
flag_intoListDirectory = True
flag_writeMovies    = False # not used any more
flag_outextension    = '.lst.xls'
dbb_withDir = True  # extract dbbXX.pst together with last directory, e.g. '190301_locust_ip16.pst/dbb6C.pst'



### set settings here!
reference_settings = 'Temp' # 'Or42b_GC6' 'Or22a_GC6'
## for Jibin: set values in function Set_Jibin_Values(lst_frame)


class OldFileHandlerBlank(object):

    def __init__(self):
        super().__init__()
        pass

    def backup(self):

        pass

    def write_old_values(self, df, columns):

        return df


class OldFileHandler(OldFileHandlerBlank):

    def __init__(self, lst_file):

        super().__init__()

        self.lst_fle = lst_file
        self.old_lst_df = pd.read_excel(self.lst_fle).reset_index()
        if "index" in self.old_lst_df.columns:
            del self.old_lst_df["index"]
        self.backup_path = None

    def backup(self):

        lst_fle_path = pl.Path(self.lst_fle)
        self.backup_path = lst_fle_path.with_suffix(f".{datetime.datetime.now().strftime('%Y%m%d')}.xls")
        self.old_lst_df.to_excel(str(self.backup_path))
        print("Output file existed! Old file saved as ")
        print(str(self.backup_path))

    def write_old_values(self, df, columns: list):

        if "Measu" not in columns:
            columns.append("Measu")

        mask = self.old_lst_df["Label"].apply(lambda x: x in df["Label"].values)

        old_df_subset = self.old_lst_df.loc[mask, columns].set_index("Measu")

        df_temp = df.set_index("Measu")

        combined_df = df_temp.combine(old_df_subset, func=lambda s1, s2: s2, overwrite=False)

        return combined_df.reset_index()


def get_old_file_handler(lst_file):

    if os.path.exists(lst_file):
        return OldFileHandler(lst_file)
    else:
        return OldFileHandlerBlank()


def Set_local_Values_Sercan(lst_frame):
    lst_frame['StimON']   = 20
    lst_frame['StimLen']  = 1000 
    lst_frame['Stim2ON']  = 60
    lst_frame['Stim2Len'] = 1000 
    lst_frame['Comment'] = 'log2lst_Sercan_CalciumGreen'

    lst_frame['Line']      = 'locust'
    lst_frame['Age']       = '-1'
    lst_frame['Sex']       = 'o'

    #!!odor and concentration extracted from label!!
    return lst_frame


def get_default_line():
    ################################################
    ###   default values    ########################
    ################################################

    # if there is a function such as Set_Jibin_Values, it will overwrite some of these
    default_comment = 'log2lst'
    default_line = 'locust'
    default_PxSzX = '1.5625'  # um per pixel, for 50x air objective, measured by Hanna Schnell July 2017, with a binning of 8
    default_PxSzY = '1.5625'
    default_age = '-1'
    default_sex = 'o'
    default_odor = 'unknown'
    default_NOConc = '0'
    default_setting = 'setting'
    default_prefer = '1'  # which area from KNIME to plot
    default_slvFlip = '0'

    ################################################

    # copy the default ones, some will be overwritten later

    lst_line = pd.Series()

    lst_line['Odour'] = default_odor
    lst_line['OConc'] = default_NOConc
    lst_line['setting'] = default_setting
    lst_line['Comment'] = default_comment
    lst_line['Line'] = default_line
    lst_line['PxSzX'] = default_PxSzX
    lst_line['PxSzY'] = default_PxSzY
    lst_line['Age'] = default_age
    lst_line['Sex'] = default_sex
    lst_line['Prefer'] = default_prefer
    lst_line["slvFlip"] = default_slvFlip

    return lst_line


def parse_label(label):

    
    if reference_settings == "Temp":
        info = {}
        info["Odour"] = 'not set'
        info["OConc"] = 'not set'
    else:
        parts = label.split("_")
        info = {}
        info["Odour"] = parts[1]
        info["OConc"] = int(parts[2])

    return info



def convert_vws_names_to_lst_names(vws_measurement_series, default_line):
    """
    Convert values from vws.log nomenclaure to .lst nomenclature
    :param vws_measurement_series: pandas.Series
    :return: pandas.series
    """
    lst_line = default_line.copy()
    lst_line['Animal']    = vws_measurement_series["Label"]
    lst_line['Measu']     = vws_measurement_series['index'] + 1
    lst_line['Label']     = vws_measurement_series['Label']
    lst_line['DBB1']      = vws_measurement_series["Location"]
    lst_line['Cycle']     = vws_measurement_series["dt"]
    lst_line['Lambda']    = vws_measurement_series['MonochromatorWL_nm']
    lst_line['UTC']       = vws_measurement_series['UTCTime']
    lst_line['StartTime'] = vws_measurement_series['StartTime']
    lst_line["Analyze"] = vws_measurement_series["Analyze"]

    #all others, just to not have empty columns
    lst_line['dbb2']    = 'none'
    lst_line['dbb3']    = 'none'
    lst_line['MTime']    = 0
    lst_line['Countl']    = 0
    lst_line['Control']    = 0
    lst_line['StimISI']    = 0
    lst_line['PhConc']    = 0
    lst_line['PhTime']    = 0
    lst_line['Pharma']    = "no_pharma"
    lst_line['PosZ']    = 0
    lst_line['ShiftX']    = 0
    lst_line['ShiftY']    = 0
    lst_line['Stim2OFF']    = -1
    lst_line['Stim2ON']    = -1
    lst_line['StimOFF']    = -1
    lst_line['StimON']    = -1

    label_info = parse_label(vws_measurement_series["Label"])
    lst_line["Odour"] = label_info["Odour"]
    lst_line["OConc"] = label_info["OConc"]

    return lst_line

#####################################
## DEFINE REFERENCE ODOR AND TIME!!!!
#####################################



def log2settings(in_logFile, out_trunc, animal):
    """ converts a till photonics .vws.log into a lst. 
    Function is not split into
    read and write because that is never needed 
    Many columns may not be needed, but are still defined for compatibility fear
    """

    # # some constants and declarations
    # block_starts = []
    # block_ends   = []
    # block_names  = []
    # flag_oldvalues = False
    # in the future: replace with searching <end of info>
    lst_labels = ["Measu","Label","Odour","DBB1", "Cycle","MTime","OConc","Control",
                  "StimON","StimOFF","Pharma","PhTime","PhConc","Comment","ShiftX","ShiftY","StimISI",
                  "setting","dbb2","dbb3","PxSzX","PxSzY","PosZ","Lambda","Countl", "slvFlip", "Stim2ON","Stim2OFF",
                  "Age", "Analyze","UTC", "Animal"]
    # last_time = 0
    # if a settings file already exists, make a backup

  
#     # read log and parse
#     with open(in_logFile, 'r') as fh:
#         lines = [line.strip() for line in fh.readlines()]
#     for i,line in enumerate(lines):
#         match = re.search('^\[(.*)\]',line) # looks for lines with []
#         if match:
#             block_starts.append(i)
#             block_names.append(match.group(1))
#         match = re.search('end of info',line) # looks for lines with end of info
#         if match:
#             block_ends.append(i)
#
# # make a list of those blocks that follow the naming conventions
#     valid_blocks = []
#     # remove blocks that have in the name "Snapshot" or "Delta"
#     # or that do not have any "_"
#     # 'Fluo340nm_00' would pass
#     for i,name in enumerate(block_names):
#         if name.count('Snapshot') > 0 \
#             or name.count('Delta') > 0 \
#             or name.count('_') < 1:
#             pass
#         else:
#             valid_blocks.append([i,block_starts[i],name,block_ends[i]])
# # make a list for what is written in each block, with label. The log file has lines such as Date: 04/04/18
#             # and this will move into e.g. {'Date ': ' 04/04/18'}
#     Measurements = []
#     for i,block_info in enumerate(valid_blocks):
#         Measurements.append({'index':block_info[0],'label':block_info[2]})
#         block = lines[block_info[1]+1:block_info[3]] # all the lines that belong to this block
#         for line in block:
#             line_split = line.split(':')
#             if len(line_split) == 2:
#                 key,value = line_split
#             if len(line_split) > 2:
#                 key = line_split[0]
#                 value = ':'.join(line_split[1:]).strip()
#             Measurements[i][key] = value
#
#     lst_frame  = pd.DataFrame(columns=lst_labels)
#     for Measurement in Measurements:  # Measurement = Measurements[0]
#         lst_line  = pd.DataFrame(columns=lst_labels) #one line for ease of writing
#
#         # analyze label given in TILL for odor and concentration - not used in Jibin
# #        label_split = Measurement['label'].split('_')
# #        Odour = default_odor
# #        NOConc = default_NOConc
# #        setting = default_setting
# #        feedback = True
# #        if len(label_split) == 4: ## e.g. GC_06_ETBE_-2
# #            tmp, setting, Odour, NOConc = label_split
# #            setting = tmp + '_' + setting #reassemble
# #            feedback = False
# #        if len(label_split) == 3: ## e.g. GC06_ETBE_-2
# #            setting,Odour,NOConc = label_split
# #            feedback = False
# #        if len(label_split) == 2: ## eg. ETBE_-4
# #            Odour,NOConc = label_split
# #            feedback = False
# #        if feedback:
# #            print()
# #            print("names in TILL should be of the type xxx_odor_conc, e.g. GC00_ETBE_-2")
# #            print("or ETBE_-2 or GC_00_ETBE_-6")
# #            print()
#
#         # time & analyze
#         try:
#             times = Measurement['timing [ms]'].strip()
#             times = sp.array(times.split(' '),dtype='float64')
#             # calculate frame rate as time of (last frame - first frame) / (frames-1)
#             dt = str((times[-1]-times[0])/(len(times)-1))
#             analyze = '1' # since there are at least two frames, and thus a time, I suppose it is worth analyzing
#         except:
#             dt = '-1'
#             analyze = '0'
#
#         # location, check if pst, else -1
#         ext = os.path.splitext(Measurement['Location'])[1]
#         if ext != '.pst':
#             Location = '-1'
#         else:
#             #tanimal = os.path.splitext(os.path.splitext(os.path.basename(fname))[0])[0] # tanimal
#             dbb = os.path.splitext(Measurement['Location'].split('\\')[-1])[0] # dbb wo pst
#             # Location = '\\'.join([tanimal + '.pst',dbb])  #use this line to add the animal's .pst directory
#             Location = dbb #for \\Jibin\\JJ_01_C_F_180404a.pst\\dbbBA.pst, return 'dbbBA'
# #    "MTime","Control","StimON","StimOFF","Pharma","PhTime","PhConc","ShiftX","ShiftY","StimISI","dbb2","dbb3","PosZ","Countl","slvFlip","Stim2ON","Stim2OFF",]

    def measurement_filter(s):

        # remove blocks that have in the name "Snapshot" or "Delta"
        # or that do not have any "_"
        name = s["Label"]
        label_not_okay = name.count('Snapshot') > 0 or name.count('Delta') > 0 or name.count('_') < 1
        label_okay = not label_not_okay

        atleast_two_frames = False
        if type(s["Timing_ms"]) is str:
            if len(s["Timing_ms"].split(' ')) >= 2:
                atleast_two_frames = True

        return label_okay and atleast_two_frames

    def additional_cols(s):

        # time & analyze
        try:
            times = s['Timing_ms'].strip()
            times = sp.array(times.split(' '), dtype='float64')
            # calculate frame rate as time of (last frame - first frame) / (frames-1)
            dt = str((times[-1]-times[0])/(len(times)-1))
            analyze = '1' # since there are at least two frames, and thus a time, I suppose it is worth analyzing
        except Exception as e:
            dt = '-1'
            analyze = '0'

        # location, check if pst, else -1
        ext = os.path.splitext(s['Location'])[1]
        if ext != '.pst':
            Location = '-1'
        else:
            # for "....\\Jibin\\JJ_01_C_F_180404a.pst\\dbbBA.pst", return 'JJ_01_C_F_180404a.pst\\dbbBA.pst'
            dbb = pl.PureWindowsPath(s["Location"])
            if dbb_withDir:
                Location = str(pl.Path(dbb.parts[-2]) / dbb.stem)

                out_trunc_path = pl.Path(out_trunc)
                expected_path = out_trunc_path.parent.parent / "Data" / pl.Path(dbb.parts[-2]) / dbb.name
                if os.path.isfile(str(expected_path)):
                    print(f"File found at expected location: {str(expected_path)}")
                else:
                    print(f"File NOT found at expected location: {str(expected_path)}")

            else:
                Location = dbb.stem

        return {"dt": dt, "Analyze": analyze, "Location": Location}

    vws_manager = VWSDataManager(in_logFile)
    measurements = vws_manager.get_all_metadata(filter=measurement_filter, additional_cols_func=additional_cols)

    this_lst_frame = pd.DataFrame()

    for measurement_index, measurement_row in measurements.iterrows():

        lst_line = convert_vws_names_to_lst_names(vws_measurement_series=measurement_row,
                                                  default_line=get_default_line())
#        this_lst_frame = this_lst_frame.append(lst_line, ignore_index=True)
        this_lst_frame = pd.concat([this_lst_frame,lst_line], ignore_index=True)


    labels_not_initialzed = set(lst_labels) - set(this_lst_frame)
    assert labels_not_initialzed == set(), f"Some required columns were not initialized:\n{labels_not_initialzed}"

    #     # if .settings existed before, maybe some entries were already given
    #     # this assumes that the rows are the same!
    #     # better: find row where old_lst_df.label == label
    #     if flag_oldvalues:
    #         this_lst_df = old_lst_df.loc[old_lst_df.Label == lst_line['label'],:] #till uses "label", I use "Label"
    #         lst_line.loc[index,'Line']    = this_lst_df.iloc[0]["Line"]
    #         # alternative, in one code line: line = old_lst_df.loc[old_lst_df.Label == Label].iloc[0]['line']
    #         lst_line.loc[index,'PxSzX']   = this_lst_df.iloc[0]["PxSzX"]
    #         lst_line.loc[index,'PxSzY']   = this_lst_df.iloc[0]["PxSzY"]
    #         lst_line.loc[index,'Age']     = this_lst_df.iloc[0]["Age"]
    #         lst_line.loc[index,'Sex']     = this_lst_df.iloc[0]["Sex"]
    #         lst_line.loc[index,'Prefer']  = this_lst_df.iloc[0]["Prefer"]
    #         lst_line.loc[index,'Comment'] = this_lst_df.iloc[0]["Comment"]
    #         lst_line.loc[index,'Analyze'] = this_lst_df.iloc[0]["Analyze"]
    #         #get old entry, for age, sex, line, comment.PxSzY, PxSzX, odorshift
    #
    #     # now collect all this into a dataframe, and move to next
    #     lst_frame = lst_frame.append(lst_line)
    #


    return this_lst_frame
# end function log2settings
#now lst_frame contains all information
        










#######################################################################
# MAIN starts here 
#######################################################################
# Choose raw files
root = tk.Tk()
root.withdraw() # so that windows closes after file chosen 
root.attributes('-topmost', True)
filenames = askopenfilenames(
                parent=root,
                title='Select one or more Till .log files',
                filetypes=[('settings files', '*.log'), ('all files', '*')]
                ) # ask user to choose file
# i = 0 #for debugging       
for i in range(len(filenames)):
    in_logFile = filenames[i]
    if flag_OneDirectoryUp:
        #slowly. e.g. c:/me/myself/I/animaldir/animal.vws.log
        lst_trunc = os.path.splitext(os.path.splitext(in_logFile)[0])[0] #remove two extensions
        fn_tmp    = os.path.split(lst_trunc)[1] # name of the file (without extensions)
        dir_oneup = os.path.split(os.path.split(lst_trunc)[0])[0] #path to parent directory
        if flag_intoListDirectory:
            out_trunc = os.path.join(dir_oneup,'Lists', fn_tmp) #add filename to "Lists" folder in path
        else:
            out_trunc = os.path.join(dir_oneup, fn_tmp) #add filename             
        #result: 'c:/me/myself/I/animal'   extension, e.g. .lst.xls to be added
    else:
        out_trunc = os.path.splitext(os.path.splitext(in_logFile)[0])[0] # + '.settings' # removes both .vws and .log

    animal = os.path.basename(out_trunc)

    old_file_handler = get_old_file_handler(f"{out_trunc}{flag_outextension}")
    old_file_handler.backup()

    # read values from log file, into dataframe
    lst_frame = log2settings(in_logFile, out_trunc, animal)
    #'''''
    #Outside the measurements loop. Set values according to a list, depends on reference_settings
    #
    # modify this and calculate additional things, depending on reference_settings
    if reference_settings == 'Inga':
        lst_frame = Set_local_Values_Sercan(lst_frame)
#        lst_frame = CalcFuraFilms(lst_frame, out_trunc) # calculate and write a FURA film for each 340 in lst_frame

    lst_frame = old_file_handler.write_old_values(lst_frame, ["Line", "PxSzX", "PxSzY", "Age", "Sex", "Prefer",
                                                                   "Comment", "Analyze", "Odour", "OConc"])
    
    # write lst_frame
    # write dataframe version to .xls file
    print('writing to ',out_trunc,' and extension', flag_outextension)
    if flag_outextension == '.lst.xls':
        lst_frame.to_excel(out_trunc+'.lst.xls')  
    if flag_outextension == '.lst':
        lst_frame.to_csv(out_trunc+'.lst',sep='\t')
    
    # think about creating response overview image, and single-area glodatamix - copy from log2settings_valid
    # write_martin_glodatamix(os.path.splitext(lst_fname)[0], lst_trunc, mask)
    


