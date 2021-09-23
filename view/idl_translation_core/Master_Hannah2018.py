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


def Set_my_flags(flag):
    # use this to change any flags that are important locally
    #flag.STG_reporttag		= '030725bR'
    flag.LE_loadExp = 3
    flag.CSM_Movement = 0 # 2 for movement correction on the spot - is slow!
    flag.VIEW_batchmode    = 1 # fo
    
    flag.LE_CalcMethod = 3900
    
    flag.VIEW_ReportMethod = 12 #10 for overviews, 12 for movies
    flag.SO_Method    = 10
    flag.SO_individualScale = 3
    flag.SO_MV_scalemax     = 18.0
    flag.SO_MV_scalemin     = -2.0
    flag.SO_withinArea= 0
    flag.CTV_firstframe   = 18
    flag.CTV_lastframe    = 22
    flag.CTV_Method   = 35  #22
    flag.RM_FotoOk    = 1
    flag.CTV_scalebar = 1
    
    flag.Signal_FilterSpaceFlag = 0
    flag.mv_individualScale = 3
    
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


def Apis2018_summer(flag):
    #list all animals to be processed
    flag.SO_MV_scalemax =3.000
    flag.SO_MV_scalemin =  -2.000
    flag.STG_ReportTag ='HS_bee_PELM_180406a'
    (p1, flag) = gr_HS_bee_PELM_180406a(flag)
    #gr_takefromlist, 'HS_bee_PELM_180406a', 2

#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180409'
#    gr_HS_bee_OXON_PELM_180409
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180409', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180411'
#    gr_HS_bee_OXON_PELM_180411
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180411', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_PELM_180416b'
#    gr_HS_bee_PELM_180416b
#    #gr_takefromlist, 'HS_bee_PELM_180416b', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180417'
#    gr_HS_bee_OXON_PELM_180417
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180417', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_PELM_180418'
#    gr_HS_bee_PELM_180418
#    #gr_takefromlist, 'HS_bee_PELM_180418', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_PELM_180424b'
#    gr_HS_bee_PELM_180424b
#    #gr_takefromlist, 'HS_bee_PELM_180424b', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180420'
#    gr_HS_bee_OXON_PELM_180420
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180420', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180427'
#    gr_HS_bee_OXON_PELM_180427
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180427', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180503'
#    gr_HS_bee_OXON_PELM_180503
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180503', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180507'
#    gr_HS_bee_OXON_PELM_180507
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180507', 2
#    
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180509'
#    gr_HS_bee_OXON_PELM_180509
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180509', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_PELM_180718'
#    gr_HS_bee_OXON_PELM_180718
#    #gr_takefromlist, 'HS_bee_OXON_PELM_180718', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_180716'
#    gr_HS_bee_OXON_180716
#    #gr_takefromlist, 'HS_bee_OXON_180716', 2
#
#    flag.SO_MV_scalemax =3.000
#    flag.SO_MV_scalemin =  -2.000
#    flag.stg_reporttag ='HS_bee_OXON_180727'
#    gr_HS_bee_OXON_180727
    #gr_takefromlist, 'HS_bee_OXON_180727', 2    
    return p1, flag
# end of Apis2018_summer, i.e. list of all animals

def gr_HS_bee_PELM_180406a(flag):
    #single animal selection of order how measurements are evaluated
    flag.RM_newcolumn = 1
    ### IDL commant is this
    # subloop, '14';  12_AIR
    ### converts into Python like this
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 21, flag, selectformat ='subloop')
    flag.RM_newcolumn = 0
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 10, flag, selectformat ='subloop') #  01_LINT-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 11, flag, selectformat ='subloop') #  02_LINT-3
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 23, flag, selectformat ='subloop') #  14_LINT-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 9, flag, selectformat ='subloop') #  00_MOL
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 22, flag, selectformat ='subloop') #  13_MOL
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 6, flag, selectformat ='subloop') #  15_NONL-3
    
    flag.RM_newcolumn = 1
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 12, flag, selectformat ='subloop') #  03_OXON-10
    flag.RM_newcolumn = 0
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 13, flag, selectformat ='subloop') #  04_OXON-9
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 14, flag, selectformat ='subloop') #  05_OXON-8
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 15, flag, selectformat ='subloop') #';  06_OXON-7
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 16, flag, selectformat ='subloop') #';  07_OXON-6
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 17, flag, selectformat ='subloop') #';  08_OXON-5
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 18, flag, selectformat ='subloop') #';  09_OXON-4
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 19, flag, selectformat ='subloop') #';  10_OXON-3
    (p1,flag) = View_gr_reports.gr_takefromlist(flag.STG_ReportTag, 20, flag, selectformat ='subloop') #  11_OXON-2
    
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

# Hannah data on my mac
STG_MotherOfAllFolders = '/Users/galizia/Documents/KN_Group/19_Hannah_Burger/Apis2018/Hanna_OXON-PELM_summer2018'


flag = Set_my_flags(IDL_flags.IDL_default_flags(STG_MotherOfAllFolders))
#flag.STG_OdorReportPath		= os.path.join(STG_MotherOfAllFolders + 'IDL_output\\movies\\'

# call program that opens .lst file and performs analysis
# the command in spont_activity_master.pro was "subloop, '24'
#(p1,flag) = View_gr_reports.gr_takefromlist('030725bR', 3, flag)


####make sure all settings/flags are set, then call this animal
(p1,flag) = Apis2018_summer(flag)




