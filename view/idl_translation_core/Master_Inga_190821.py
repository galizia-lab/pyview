# -*- coding: utf-8 -*-
"""
Created on Wed May 30 10:13:47 2018

@author: Giovanni Galizia

copy of master
in C:\\Users\\Giovanni Galizia\\Documents\\Code\\ShareWinXP\\WindowsExchange\\IDL_Data\\spont_activity\\00_copy_IDL

changed May 2019
to run Hanna Apis2018 as sample data
on mac gio: run in environment idl_py

"""

### gio 25.5.2019: "from view.idl_translation_core import View_gr_reports " does not work,
#                    direct import does: import View_gr_reports as...
#                  in spyder, anaconca env idl_py, mac. 
#from view.idl_translation_core import View_gr_reports as View_gr_reports, IDL_flags as IDL_flags
import View_gr_reports as View_gr_reports, IDL_flags as IDL_flags
from sys import platform
#show images inline:
#%matplotlib inline
#show images in extra window
#%matplotlib qt
import shutil


def Set_my_flags(flag):
    # use this to change any flags that are important locally
    #flag.STG_reporttag		= '030725bR'
    flag.LE_loadExp = 4
    flag.CSM_Movement = 0 # 2 for movement correction on the spot - is slow!
    flag.VIEW_batchmode    = 1 # fo
    
    flag.LE_CalcMethod = 4900
    
    flag.VIEW_ReportMethod = 10 #10 for overviews, 11 for Glodatamix, 12 for movies
    flag.SO_Method    = 10
    flag.SO_individualScale= 3
    flag.SO_MV_scalemax     = 18.0
    flag.SO_MV_scalemin     = -2.0
    flag.SO_withinArea= 0
    flag.CTV_firstframe   = 18
    flag.CTV_lastframe    = 30
    flag.CTV_Method   = 22  #22
    flag.RM_FotoOk    = 0
    flag.RM_NextPosition = (0,0)
    flag.CTV_scalebar = 0
    
    flag.Signal_FilterSpaceFlag = 1
    flag.Signal_FilterSpaceSize = 5
    flag.mv_individualScale = 3
    
    flag.RM_Radius = 5
    flag.SO_MV_colortable = 11

    
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


def Inga_2019_Fura_test(flag):
    #list all animals to be processed
    flag.SO_MV_scalemax =3.000
    flag.SO_MV_scalemin =  -2.000
#list animals to work with here
    animallist = ['190607_locust_ip32', '190702_locust_ip33']

    for i,animal in enumerate(animallist):
        print(i, animal)
        flag.STG_ReportTag =animal
    # run gr_190227_locust_ip14 to select also the order of how measurements are evaluated
    #(p1, flag) = gr_190227_locust_ip14(flag)
    # run gr_takefromlist to use the 'analyze' column
#list what to do with each animal here
        (p1, flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 1, flag, selectformat ='analyze')
    
    return p1, flag
# end of Inga_2019_Fura_test


def gr_190227_locust_ip14(flag):
    #single animal selection of order how measurements are evaluated
    flag.RM_NewColumn = 1
    ### IDL commant is this
    # subloop, '14';  12_AIR
    ### converts into Python like this
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 1, flag, selectformat ='subloop')
    flag.RM_NewColumn = 0
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 3, flag, selectformat ='subloop') #  01_LINT-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 5, flag, selectformat ='subloop') #  02_LINT-3
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 7, flag, selectformat ='subloop') #  14_LINT-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 9, flag, selectformat ='subloop') #  00_MOL
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 11, flag, selectformat ='subloop') #  13_MOL
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 13, flag, selectformat ='subloop') #  15_NONL-3
    
    return p1, flag

def gr_190227_locust_ip16(flag):
    #single animal selection of order how measurements are evaluated
    flag.RM_NewColumn = 1
    ### IDL commant is this
    # subloop, '14';  12_AIR
    ### converts into Python like this
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 1, flag, selectformat ='subloop')
    flag.RM_NewColumn = 0
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 3, flag, selectformat ='subloop') #  01_LINT-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 5, flag, selectformat ='subloop') #  02_LINT-3
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 7, flag, selectformat ='subloop') #  14_LINT-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 9, flag, selectformat ='subloop') #  00_MOL
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 11, flag, selectformat ='subloop') #  13_MOL
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 13, flag, selectformat ='subloop') #  15_NONL-3
    
    return p1, flag

#########################################################
########## Main starts here
#########################################################

# define flags
    #IDL.flags.IDL_default_flags sets the general rules
    #Set_my_flags modifies these
#on my windows system
#STG_MotherOfAllFolders = 'C:\\Users\\Giovanni Galizia\\Documents\\Code\\ShareWinXP\\WindowsExchange\\IDL_Data\\spont_activity' #if empty, working directory is used
#if platform == 'darwin':
#    STG_MotherOfAllFolders = '/Users/galizia/Documents/Code/ShareWinXP/WindowsExchange/IDL_Data/spont_activity'

print()
print('Running this master file: ', __file__)
print()

# Inga data on my mac
STG_MotherOfAllFolders = '/Users/galizia/Documents/KN_Group/19_Inga/Inga_locust_best_SampleTree'


flag = Set_my_flags(IDL_flags.IDL_default_flags(STG_MotherOfAllFolders))
#flag.STG_OdorReportPath		= os.path.join(STG_MotherOfAllFolders + 'IDL_output\\movies\\'

# call program that opens .lst file and performs analysis
# the command in spont_activity_master.pro was "subloop, '24'
#(p1,flag) = View_gr_reports.gr_takefromlist('030725bR', 3, flag)


####make sure all settings/flags are set, then call this animal
(p1,flag) = Inga_2019_Fura_test(flag)

#document how this analysis was done, by copying this file into the output folder
shutil.copy(__file__, flag.STG_OdorReportPath)
#TODO also copy the .yml file if that contains flag settings



