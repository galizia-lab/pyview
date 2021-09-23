# -*- coding: utf-8 -*-
"""
Created on Wed May 30 10:13:47 2018

@author: Giovanni Galizia

copy of master
in C:\\Users\\Giovanni Galizia\\Documents\\Code\\ShareWinXP\\WindowsExchange\\IDL_Data\\spont_activity\\00_copy_IDL
"""

#from view.idl_translation_core
import View_gr_reports as View_gr_reports, IDL_flags as IDL_flags
from sys import platform
#show images inline:
#%matplotlib inline
#show images in extra window
#%matplotlib qt


def Set_my_flags(flag):
    # use this to change any flags that are important locally
    #flag.STG_reporttag		= '030725bR'
    flag.CSM_Movement = 0 # 2 for movement correction on the spot - is slow!
    flag.VIEW_batchmode    = 1 # fo
    flag.LE_CalcMethod = 3950
    
    flag.VIEW_ReportMethod = 10
    flag.SO_Method    = 10
    flag.SO_individualScale= 3
    flag.SO_MV_scalemax     = 18.0
    flag.SO_MV_scalemin     = -2.0
    flag.SO_withinArea= 0
    flag.CTV_firstframe   = 18
    flag.CTV_lastframe    = 22
    flag.CTV_Method   = 35  #22
    flag.RM_fotook    = 1
    flag.CTV_scalebar = 1
    return flag


def ChooseFileFolder():  
    import tkinter as tk
    from tkinter.filedialog import askopenfilenames

    # Choose raw files
    root = tk.Tk()
    root.withdraw() # so that windows closes after file chosen 
    root.attributes('-topmost', True)
    # the mac system does not accept filetypes, therefore ask for system
    if platform == 'darwin':
        filenames = askopenfilenames(
                        parent=root,
                        title='Select one or more settings files (*.settings.xls)',
                        ) # ask user to choose file
    else:
        filenames = askopenfilenames(
                    parent=root,
                    title='Select one or more settings files',
                    filetypes=[('settings files', '*.settings.xls'), ('all files', '*')]
                    ) # ask user to choose file
    return filenames


#########################################################
########## Main starts here
#########################################################

# define flags
    #IDL.flags.IDL_default_flags sets the general rules
    #Set_my_flags modifies these
#on my windows system
STG_MotherOfAllFolders = 'C:\\Users\\Giovanni Galizia\\Documents\\Code\\ShareWinXP\\WindowsExchange\\IDL_Data\\spont_activity' #if empty, working directory is used
if platform == 'darwin':
    STG_MotherOfAllFolders = '/Users/galizia/Documents/Code/ShareWinXP/WindowsExchange/IDL_Data/spont_activity'
flag = Set_my_flags(IDL_flags.IDL_default_flags(STG_MotherOfAllFolders))
#flag.STG_OdorReportPath		= os.path.join(STG_MotherOfAllFolders + 'IDL_output\\movies\\'

# call program that opens .lst file and performs analysis
# the command in spont_activity_master.pro was "subloop, '24'
(p1,flag) = View_gr_reports.gr_takefromlist('030725bR', 3, flag)

# debug within takefromlist
inputLabel = '030725bR'#, 2, flag
SelectValue = 3


