# -*- coding: utf-8 -*-
"""
Created on Wed May 30 10:41:23 2018

@author: Giovanni Galizia

translation of view IDL files
this file contains the folder View_gr_reports
"""

# solution from https://stackoverflow.com/a/49480246
if __package__ is None or __package__ == '':   # if Master_Hannah2018.py is importing this file
    import ViewCalcData, ViewLoadData, ViewTools, IDL, ViewOverview, ImageALlocal
else:  # if we are importing this file from a package, e.g., using view.idl_translation_core.ViewOverview
    from . import ViewCalcData, ViewLoadData, ViewTools, IDL, ViewOverview, ImageALlocal

import os
import pandas as pd
import numpy as np
from view.python_core.movies import export_movie
from view.python_core.measurement_list import MeasurementList
from view.python_core.rois.roi_io import ILTISTextROIFileIO
from view.python_core.io import read_tif_2Dor3D
from view.python_core.overviews.ctv_handlers import PixelWiseCTVHandler
import pathlib as pl

# I need to solve the following command in jacob.py:
#View_gr_reports.gr_takefromlist('j080227b',2, flag)
def gr_takefromlist(inputLabel, SelectValue, flag, selectformat = 'analyze'):
    '''
    reads an IDL .lst file, and selects all rows with the tag divisible by "selectvalue"
    puts that information into flag and p1
    
    then goes through each line, reads the respective row, and calls
    subloop -> do all data analysis
    
    selects a measurement based on variable selectformat.
    IF selectformat == 'analyze', column 'analyze' is taken, with all entries that are divisible by SelectValue
    (this is the default, because it corresponds to gr_takefromlist in IDL)
    
    IF selectformat == 'subloop', then the line is taken with the tag SelectValue in the first column ('measu')
    in IDL, the command is, for example 
    > stg_reporttag = '030725bR'
    > subloop, '24' 
    in Python, I translate these two lines into
    gr_takefromlist(flag.STG_ReportTag, 24, flag, selectformat = 'subloop')
    '''
    
    #copy animal tag into flag
    flag.update_flags({'STG_ReportTag': inputLabel})
#    flag.STG_ReportTag = inputLabel # e.g. 030725bR

    #get a single measurement
#    flag.RM_NewColumn = 1 #why do I need this?

    # check if .lst.xls file exists, else use .lst use
    InputOdorFile_xl = os.path.join(flag["STG_OdorInfoPath"],flag["STG_ReportTag"]+'.lst.xls')
    InputOdorFile_lst = os.path.join(flag["STG_OdorInfoPath"], flag["STG_ReportTag"] + '.lst')
    if os.path.exists(InputOdorFile_xl):
        InputOdorFile = InputOdorFile_xl
    elif os.path.exists(InputOdorFile_lst):
        InputOdorFile = InputOdorFile_lst
    else:
        raise IOError(f"Could not find measurement list! I tried {InputOdorFile_xl} and {InputOdorFile_lst} and "
                      f"neither exist")

    # creates a MeasurementList object from the measurement list file
    measurement_list = MeasurementList.create_from_lst_file(InputOdorFile, flag["LE_loadExp"])

    if selectformat == 'analyze':
        # select only those to analyze, using SelectValue: all rows with reminder 0
        measus = measurement_list.get_measus(selection_divisor=SelectValue)

    elif selectformat == 'subloop':
        measus = []
        if SelectValue in measurement_list.get_measus():
            measus = [SelectValue]
    else:
        raise NotImplementedError("Currently, 'selectformat' can only be 'analyze' or 'subloop'")

    if len(measus) == 0:
        print("View_gr_reports.gr_takefromlist: requested measurements do not exist")
        return (0,0)

    # now go through each measurement
    countLoop = 0
    for measu in measus:
        print('View_gr_reports:gr_takefromlist: now looping row', measu)
        if selectformat == 'analyze':  # many rows taken from settings file, no info about columns
            if countLoop == 0:  # this is the first one to analyze, select new column
                flag.update_flags({'RM_NewColumn': 1}) 
                #flag["RM_NewColumn"] = 1  # selecting a new column should also create the right position
            else:
                flag.update_flags({'RM_NewColumn': 0}) 
                #flag["RM_NewColumn"] = 0
        p1 = measurement_list.get_p1_metadata_by_measu(measu)
        subloop(p1, flag)
        countLoop += 1
#    .squeeze()
#    flag.RM_NewColumn = 0 #why do I need this?
    return p1, flag


def subloop(p1,flag):
    # keep track
    print("View_gr_reports.subloop: running measurement: ", p1.metadata.messungszahl,'***',p1.metadata.ex_name)
##    pro SubLoop, InputFile
##inputOdorFile = inputfile
    ViewLoadData.loadDataMaster(flag, p1)
##;calculate signals
    print('Subloop.pro: now calculating data, method ',flag["LE_CalcMethod"])
    ViewCalcData.CalcSigMaster(flag, p1)
#$ CalcSigMaster, raw1, dark1, p1, flag[LE_CalcMethod], sig1
    
##IF flag[view_initCorr] ge 0 THEN begin
#correct, sig1, sig1corr, raw1, p1, flag[view_initCorr], filterTimeSize  ;diese Zeile raus um Speicher zu sparen
##end
##;data loaded
##;choose report method
    print('Subloop_ave: calling report ****************************************************************')
    flag = subloop_report(flag,p1)
##end ; SubLoop
    


def subloop_report(flag,p1):
    '''
        Calls which output to do in subloop
    '''
#common cfd
#common cfdconst
    reportflag = flag["VIEW_ReportMethod"]
    print('Subloop_report, running ',reportflag)
#;choose report method
#    if reportflag == 3 : ReportCoorGeli #ok for tobi Angelika
#    if reportflag == 4 : reportMask   #Silke
#    if reportflag == 5 : ReportCoorQuerGeli
#    if reportflag == 6 : ReportMaskQuer
#    if reportflag == 7 : TraceMidiMask
#    if reportflag == 9 : ReportCoorQuer
    if reportflag == 10 : flag = ReportTiff(flag, p1)
    # no need to convert flags to series here, it is done within ExportGlomeruli before using the flags
    # also, I need some methods of FlagManagers manager inside ExportGlomeruli. -AJ, 29.09.2019
    if reportflag == 11 : ExportGlomeruli(flag, p1) #, 1) # export entire time course
    # exportglomeruli does not use the number any more, use VIEW_reportmethod instead!
    if reportflag == 12:
        filetext = ImageALlocal.localodortext(flag, p1)
        outfilename = os.path.join(flag["STG_OdorReportPath"], filetext)
        export_movie(flag, p1, outfilename)
#TODO change this: if mv_exportformat is an integer, switch to old procedure automatically
        # currently, 1200 is the old procedure (IDL translate)
    if reportflag == 1200 : ViewOverview.ExportMovie(flag.to_series(), p1) #Report12mpeg #calles exportmovie, settings in imageALlocalsetexportmovieflags.pro!!!!
    if reportflag == 13 : ReportTiff(flag.to_series(),p1) #single multilayered file
    if reportflag == 14 : ReportTiff(flag.to_series(),p1) #single multilayered file, raw data
    if reportflag == 15 : ReportTiff(flag.to_series(),p1) #one file for each frame, TifF
#    if reportflag == 16 : ExportGlomeruli, 2 # export CTV value only
#    if reportflag == 17 : ExportGlomeruli, 3 # export CTV value only, Martin Stetter
#    if reportflag == 18 : ExportTripleFrame # export frames with statistics as raw data
#    if reportflag == 19 : ExportGlomeruli, 4 # export CTV value and timeTrace
    if reportflag == 20 : ReportTiff(flag.to_series(),p1) #single multilayered file, only first odour
    if reportflag == 21 : ReportTiff(flag.to_series(),p1) #single multilayered file, diff. layers ('odors') sideways
#    if reportflag == 22 : Export22RawData #single multilayered file, diff. layers ('odors') sideways
#    if reportflag == 24 : Export24RawDataAppend #export sig1 as raw data, append several measurements
#    if reportflag == 25 : ExportGlomeruli, 25 # export multiple CTV values (Curve2MultiVAlues.pro)
#    if reportflag == 26 : ExportGlomeruli, 26 # export single trace (array2curve)
#    if reportflag == 111 : ExportGlomeruli, 111 # export  entire time course with column tags
    if reportflag == 111 : ExportGlomeruli(flag, p1) #, 1) # same as 11
#    if reportflag == 119 : ExportGlomeruli, 119 # export  entire time course with column tags
    if reportflag == 119 : ExportGlomeruli(flag, p1) #, 1) # same as 11
    
    
    
    if reportflag == -1 : print('Skip Subloop ....')
    # for report methods defined in the folder imageALMathias
#    if reportflag gt 1000 : Subloop_Report_Mathias #
#
#end subloop_report#
    

def ReportTiff(flag,p1):
    print('View_gr_reports.ReportTiff - calling ViewOverview.singleoverviews')
    flag = ViewOverview.singleoverviews(flag, p1)
    return flag
    
    
    
    
def read_glo_liste(flag,p1): #(NumListe, liste, inputFile, quiet=quiet, column4=column4):
    '''
    read liste of glomeruli coordinates
    called in IDL with            
    readListe, GlomeruliNum, liste, flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.coor' , column4=separateLayers
    !! option for different layers not implemented yet (i.e. insert flag.STG_ReportTag)

    '''
    # 
    inputfile = os.path.join(flag["STG_OdormaskPath"],flag["STG_ReportTag"]+'.coor')
    if not os.path.isfile(inputfile): #file does not exist, test different layers. Not tested
        inputfile = os.path.join(flag["STG_OdormaskPath"],flag["STG_ReportTag"]+str(p1.metadata.viewlabel)+'.coor')

    
#;check if file has mac format, if so replace with windows EOL format
#macFile_toIbm_replace, 'offlinemode', inputfile
#;open file for reading
#openR, unit,inputFile, /get_lun
#readF, unit, NumListe
    colnames = ['y_glo','x_glo','num_glo']
#############################################
    # python - row & columns are swapped, therefore first coordinate is y, second is x
    glom_liste = pd.read_csv(inputfile, sep='\t', encoding='latin-1', names=colnames, header=None)
    num_glo = glom_liste.y_glo[0] #only read this many glomeruli
    glom_liste.drop([0], inplace=True) #drop the first line, it only contains num_glo
    glom_liste = glom_liste.iloc[:num_glo,:] #keep only the first num_glo glomeruli
    #convert to integers
    glom_liste = glom_liste.astype(int)
#;are there 4 columns?
#IF KEYWORD_SET(column4) THEN column4=column4 ELSE column4=0
#;define Liste
#IF column4 THEN liste = IntArr(4,NumListe) ELSE liste = IntArr(3,NumListe)
#FOR i = 0, Numliste-1 do begin
#	IF column4 THEN readF, unit, a, b, c, d ELSE readF, unit, a, b, c
#	liste(0,i) = a ;koordinate x
#	liste(1,i) = b ;koordinate Y
#	liste(2,i) = c ;Identitt
#	IF column4 THEN liste(3,i) = d
#endfor
#IF KEYWORD_SET(quiet) THEN begin
#endIF else begin
#	print, rotate(liste,1)
#	print, Numliste
#endELSE
#;close file
#free_lun, unit
#end readLister
    ###include shifts here
    for index, row in glom_liste.iterrows():
#        print('Now glomerulus ',index, row)
        row.x_glo = row.x_glo + p1.metadata.shiftX
        row.y_glo = row.y_glo + p1.metadata.shiftY
#     ;shiftMaskeX, shiftMaske
#     liste(0,*) = liste(0,*) + p1.metadata.shiftX
#     liste(1,*) = liste(1,*) + p1.metadata.shiftY
#     ;consider shrinkfactor
#     IF (shrinkFactor gt 1) then begin
    if (flag["LE_ShrinkFaktor"] > 1): #no shrinking below 1?
        row.x_glo = row.x_glo / flag["LE_ShrinkFaktor"]
        row.y_glo = row.y_glo / flag["LE_ShrinkFaktor"]
#       liste(0,*) = liste(0,*)/shrinkFactor
#       liste(1,*) = liste(1,*)/shrinkFactor
    return glom_liste    




def ExportGlomeruli(flags, p1, measurement_row):
    '''Exports time traces of selected glomeruli or area, based on IDL code
    unlike original code, output is based on Pandas dataframe
    '''
    #convert flags to series because that is the way I wrote this at the beginning. 
    #this function needs to be rewritten anyway to accomodate for different formats
    flag = flags.to_series()
#    shrinkFactor = flag.LE_ShrinkFaktor #shrinkfactor considered in readglolist
#    setUp        = flag.LE_loadExp
    exportOption = flag.VIEW_ReportMethod # comes from flag.VIEW_ReportMethod
#;set exportOption to 1 for compatibility
#;else: exportoption = 1 gives the entire timecourse (flag.VIEW_ReportMethod == 12)
#;                     2 gives the curveToValue calculation (flag.VIEW_ReportMethod == 16)
#;					  3 gives the Martin Stetter estimates (not implemented yet) (flag.VIEW_ReportMethod == 17)
#;					  4 write timetrace AND ctv  (flag.VIEW_ReportMethod == 19)
#;					  25 write combined information, but multiple CTV values (flag.VIEW_ReportMethod == 25)
#;					  26 Calles Array2Curve (flag.VIEW_ReportMethod == 26)
#;					  111 timetrace, with column headers (flag.VIEW_ReportMethod == 111)
#;					  119 timetraces, CTV and headers# (flag.VIEW_ReportMethod == 119)
#;					  19 timetraces, CTV but no headers (not called from outside yet; Jan 08)
    radius = flag.RM_Radius
#    separateLayers = flag.RM_separateLayers
    reportAreas    = flag.RM_ROITrace #if set, reads a tiff file and gives glodatamix of the areas in there, instead of a list of glomeruli/squares
#;set reportAreas to '2' for only plotting the single area defined by ".area", for single-OR Drosophila antennae
#    timec     = np.zeros(p1.metadata.frames)

#;Use 'first buffer' or not?
#firstOdor = fix(flag[LE_UseFirstBuffer]) #section deleted in python

#;corrected or non-corrected data
#if correctFlag then signals = sig1corr ELSE signals = sig1   ;get correctflag from common vars

#;
#shrinkFrames = 0 ;IF there are more than 3000 frames, they are shrunk

#;Get Information about odours from external file
    GlomeruliListFile =  os.path.join(flag.STG_OdormaskPath,flag.STG_ReportTag+'.coor')
#   IF (setUp eq 0) THEN begin
#   	;get information for old setup
#     	GlomeruliListFile = flag[stg_OdorMaskPath]
#     	reportFile = flag[stg_OdorReportPath]
#     	GetOdourInfo, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', GlomeruliListFile, reportFile, shiftMaskeX, shiftMaskeY
#     	IF (strpos(STRUPCASE(GlomeruliListFile),'.COOR') lt 0) THEN GlomeruliListFile = GlomeruliListFile + '.coor'
#   ENDIF else BEGIN
#	;IF (setUp ge 3) THEN begin;TILL photonics;not the old setup
#	   	;position of glomeruli
#	   	IF fix(flag[RM_differentViews]) THEN begin
#    			GlomeruliListFile =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.metadata.viewLabel+'.coor'
#    		endIF else begin
#    			GlomeruliListFile =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.coor'
#    		endELSE
#     		reportFile = flag[stg_OdorReportPath]+flag[stg_ReportTag]+'.expGlo'
#	   	shiftMaskeX = p1.metadata.shiftX
#	   	shiftMaskeY = p1.metadata.shiftY
#	;ENDIF ;other options not implemented
#   ENDelse


#;now get information about the glomeruli
    ########### do not implement -1 in python
#IF (reportAreas eq -1) THEN begin ; use the coordinate at the center of the image - single glomerulus only
#   ;readListe, GlomeruliNum, liste, GlomeruliListFile, column4=separateLayers
#   glomerulinum = 1
#   ;define glomeruli list with one glomerulus
#   liste = IntArr(4,1)
#   ;glomerulus identity is 666
#   liste(2,0) = 666
#   ;x-coordinate is the center
#   liste(0,0) = fix(p1.metadata.format_x / 2)
#   liste(1,0) = fix(p1.metadata.format_y / 2)
#   ;got the liste of coordinates & identities
#
#   ;consider shifts
#   ;shiftMaskeX, shiftMaskeY
#   liste(0,*) = liste(0,*) + shiftMaskeX
#   liste(1,*) = liste(1,*) + shiftMaskeY
#     ;consider shrinkfactor
#     IF (shrinkFactor gt 1) then begin
#		liste(0,*) = liste(0,*)/shrinkFactor
#		liste(1,*) = liste(1,*)/shrinkFactor
#     endIF
#endIF ; reportAreas
    if (reportAreas == 0): # THEN begin ; get information about glomeruli coordinates
#   readListe, GlomeruliNum, liste, GlomeruliListFile, column4=separateLayers
        gloList = read_glo_liste(flag,p1)
#   ;got the liste of coordinates & identities, dataframe
        ########### python. glomeruli are not shifted to 1000 - you have to know what you do
#   IF total(liste(2,*)) eq 0 then begin
#   ;replace identity liste with index, ranging from 1000 onwards to avoid being mistaken for identity
#   	indexList = indgen(GlomeruliNum)
#   	indexList = indexList + 1001
#   	liste(2,*) = indexList
#   endIF
##################### but check for double glomeruli
        if sum(gloList.duplicated(['num_glo'])): #there is at least one duplicate
            print('ExportGlomeruli: Glomerulus liste badly defined. Double Glomerulus ')
            #break
#   ;check identity list for double occurances
#   exit = 0
#   For i=0,GlomeruliNum-1 do begin
#		;check for double occurrences
#		junk = where(liste(2,*) eq liste(2,i),count)
#		;also: wie viele glomeruli liste(2,i) gibt es in der ganzen liste?
#		IF count gt 1 THEN begin
#		   print, 'ExportGlomeruli: Glomerulus liste badly defined. Double Glomerulus ',i,liste(2,i)
#		   exit = 1
#		end
#   endfor
#   IF exit THEN stop
#   ;shiftMaskeX, shiftMaskeY
            ############# shifts are in readliste now!!!
#   liste(0,*) = liste(0,*) + shiftMaskeX
#   liste(1,*) = liste(1,*) + shiftMaskeY
#     ;consider shrinkfactor
#     IF (shrinkFactor gt 1) then begin
#		liste(0,*) = liste(0,*)/shrinkFactor
#		liste(1,*) = liste(1,*)/shrinkFactor
#     endIF
#endIF ; reportAreas
###########;all reportareas ge 1 use areas and not coordinates
    elif (reportAreas == 1 ): ## THEN begin ; get information from a TIFF file
#	; the name of the TIFF file follows the same convention as the .coor file, extension is .mask
#	GlomeruliListFile = strmid(GlomeruliListFile, 0, strlen(GlomeruliListFile)-4)+'mask'
        GlomeruliListFile = GlomeruliListFile[:-4]+'mask'
#	;open tiff file, read
        maskAreas, IDLpalette = IDL.read_tiff(GlomeruliListFile)
#	;shift tiff file
        maskAreas = np.roll(maskAreas, (p1.metadata.shiftX, p1.metadata.shiftY), axis=(1,0)) #in numpy, vertical is first
#	maskAreas = shift(maskAreas, p1.metadata.shiftX, p1.metadata.shiftY)
#	;consider shrinkfactor # not implemented in python yet
#	maskAreas = rebin(maskAreas, p1.metadata.format_x, p1.metadata.format_y, /sample)
#	;calculate number of glomeruli: GlomeruliNum
#	areaList = intarr(255,2)
#        GlomeruliNum = 0
        gloList = pd.DataFrame(columns=['glo','count'])
        for glo in range(253): # do begin; exclude 255 =black, 0= white
            print(glo)
            sum_glo = sum(maskAreas == (glo+1))            
#			list1 = where (maskAreas eq glo, count)
            if (sum_glo > 1): # then begin ;*********** areas with only 1 pixel are NOT accepted because averaging crashes below
#			    IF (GlomeruliNum eq 0) THEN gloList = [glo,count] ELSE gloList = [gloList, [glo,count]]
#				GlomeruliNum = GlomeruliNum + 1
                 gloList.loc[glo] = [glo,sum_glo] #this syntax would overwrite equal glo
#			endif
#	endFOR
#	gloList = reform(glolist,2,GlomeruliNum)
#endIF
    elif (reportAreas == 2): ## THEN begin ; get information from a TIFF file
#IF (reportAreas eq 2 ) THEN begin ; get information of a single area from the .area file
#	; the name follows the same convention as the .coor file, extension is .area
        ######### but the name is fixed in the IDL.restore function
        maskframe = IDL.restore_maskframe(flag) #restores maskframe from file
#	areafilename = strmid(GlomeruliListFile, 0, strlen(GlomeruliListFile)-4)+'area'
#        GlomeruliListFile = GlomeruliListFile[:-4]+'area'
#	;open area file, read
#		OPENR, 1, areafilename, ERROR = err	;Try to open the file demo.dat.
#		IF (err NE 0) then begin
#			print, 'Looking for file: ',areaFileName
#			areaFileName = Dialog_Pickfile(Path=flag[stg_OdorMaskPath], get_Path = inPath, Filter='*.Area', title='Choose perimeter file (or cancel and correct program)!')
#			flag[stg_OdorMaskPath] = inpath
#		endIF else begin
#			close, 1 ; file exists, all ok
#		endELSE
# 		restore, areaFileName
#		;now AL perimeter is in variable 'maskframe'
#	;just rename it, and use the code for TIFF from above
#	maskAreas = maskFrame
#	;(I know it's not nice programming...)
#	;shift tiff file
#	maskAreas = shift(maskAreas, p1.metadata.shiftX, p1.metadata.shiftY)
        maskAreas = np.roll(maskframe, (p1.metadata.shiftX, p1.metadata.shiftY), axis=(1,0)) #in numpy, vertical is first
#	;consider shrinkfactor
#	maskAreas = rebin(maskAreas, p1.metadata.format_x, p1.metadata.format_y, /sample)
        gloList = pd.DataFrame(columns=['glo','count'])
        for glo in range(253): # do begin; exclude 255 =black, 0= white
            print(glo)
            sum_glo = sum(maskAreas == (glo+1))            
#			list1 = where (maskAreas eq glo, count)
            if (sum_glo > 1): # then begin ;*********** areas with only 1 pixel are NOT accepted because averaging crashes below
#			    IF (GlomeruliNum eq 0) THEN gloList = [glo,count] ELSE gloList = [gloList, [glo,count]]
#				GlomeruliNum = GlomeruliNum + 1
                 gloList.loc[glo] = [glo,sum_glo] #this syntax would overwrite equal glo

    elif reportAreas in (3, 4):

        if reportAreas == 3:
            roi_filepath = flags.get_existing_filename_in_coor(measurement_label=p1.metadata.ex_name, extension=".roi")
            roi_datas = ILTISTextROIFileIO.read_roi_file(str(roi_filepath))
            roi_masks_list = [x.get_boolean_mask((p1.metadata.format_x, p1.metadata.format_y)) for x in roi_datas]
        else:

            mask_tif_filepath = flags.get_existing_filename_in_coor(
                measurement_label=p1.metadata.ex_name, extension=".roi.tif")

            roi_masks_3D = read_tif_2Dor3D(str(mask_tif_filepath))
            roi_masks_list = [roi_masks_3D[:, :, ind] for ind in range(roi_masks_3D.shape[2])]

        gloList = pd.DataFrame()
        for roi_ind, roi_mask in enumerate(roi_masks_list):
            tempS = pd.Series()
            tempS["num_glo"] = roi_ind
            tempS["pixel_count"] = roi_mask.sum()
            tempS.name = roi_ind + 1
            #gloList = gloList.append(tempS)
            gloList = pd.concat([gloList, tempS])



#	;calculate number of glomeruli: GlomeruliNum
#	areaList = intarr(255,2)
#	GlomeruliNum = 0
#	for glo=1, 254 do begin; exclude 255 =black, 0= white
#			list1 = where (maskAreas eq glo, count)
#			if (count gt 1) then begin ;*********** areas with only 1 pixel are NOT accepted because averaging crashes below
#			    IF (GlomeruliNum eq 0) THEN gloList = [glo,count] ELSE gloList = [gloList, [glo,count]]
#				GlomeruliNum = GlomeruliNum + 1
#			endif
#	endFOR
#	gloList = reform(glolist,2,GlomeruliNum)
#endIF
    GlomeruliNum = len(gloList) ##how many rows, corresponds to number of glomeruli

#python
##the following would be done best with a class based on a pandas dataframe. For now, however, I copy the IDL code
#;got all information, define structures
#fltArr (p1.metadata.frames, GlomeruliNum) !!! p1.metadata.ferames are the ROWS in python
#;containes the time-courses
#;define a text array with the labels for each numerical column
#ArrayNumLabels = strArr(numinfos)
#;each position with the following meaning:
    ctv_tag = 'CTV_'+str(flag.CTV_Method)
    Num_columns = [ 'NGloTag'	,# 		;integer name of glomerulus, or fictive name >300, or incrementative >1000
                    'NOdorNr'	,# 		;integer code of odor
                    'NOConc'	,#	 	;concentration of odour stimulus, always TENFOLD logarithmic, i.e. -23 is 10 to the -2.3
                    'NStim_on'	,# 		;stimulus onset, frame (first frame WITH odor)
                    'NStim_off'	,# 	;stimulus offset, frame (last frame WITH odor)
                    'NNoFrames' ,# ;number of frames in one measurement
                    'NFrameTime',#	 	;inverse of frequency, in ms. Set to 0 for uneven frequencies
                    'NRealTime'	 ,#	;time in minutes
                    'NPhConc'   ,#		; 1 for treatment, eg 1: ptx, 0: wash or pre-ptx, includes concentration of treat
                    'NshiftX'   ,#
                    'NshiftY'   ,#
                    'NcontMeasu',# 		;zahl der kontrollmessung
                    'NNumMeasu' ,#		; zahl der messung
                    'Nstim_ISI'	,#	; interval between stimuli
                    'NodorN'	,#		;, i.e. no Measu for old setup, or slice for 3D measus new setup, 4th dimension in sig1 and sig1corr
                    'Nstim2ON'	,#		;onset second stimulus
                    'Nstim2OFF'	,#	;offset second stimulus
                    'NAge'		,#  		;age of the animal
                    'NAgeMax'	,#			;age of the animal
                    ctv_tag]
    ArrayNumInfos = pd.DataFrame(np.zeros([GlomeruliNum, len(Num_columns)], dtype=int), columns=Num_columns)
    ArrayNumInfos[ctv_tag].astype(float)  #ctv is not an integer
#txtinfos = 11
#ArrayTxtInfos	= strArr (txtinfos, GlomeruliNum)
#;define a text array with the labels for each text column
#ArrayTxtLabels = strArr(txtinfos)
#;each position with the following meaning:
    Txt_columns = [ 'TGloInfo'	,# 	;comment text for the glomerulus
                    'TOdour'	,# 	;name of odor stimulus, e.g. 'HX1'
                    'T_dbb1'	,# 	;experimental file, or measurement (TILL) expDatei
                    'Tcomment'	,# 	;any comment
                    'TPharma'   ,#	;text of treatment
                    'TPhtime' 	,#	; application time of treatment
                    'Tos9time'  ,# 	; time of measurement
                    'TviewLabel',#   	; label view
                    'Tlabel'    ,# 	;unique name of measurement
                    'Tanimal'   ,# 	;unique name of animal
                    'T_dbb2']	# 	;second dbb file - can be misused (e.g. male/female)
    #TODO : here I initialize ArrayTxtInfos with numbers, but I need text - really, I only need glo lines
    ArrayTxtInfos = pd.DataFrame(np.zeros([GlomeruliNum, len(Txt_columns)]), columns=Txt_columns)
#make ArrayGloTraces into a DataFrame with titles Frame0....FrameN
    Frame_columns = ['Frame{0}'.format(s) for s in range(p1.metadata.frames)]
    ArrayGloTraces = pd.DataFrame(np.zeros([GlomeruliNum, p1.metadata.frames]), columns=Frame_columns)
#;now go through odours
#for duft = firstOdor, p1.metadata.odors do begin ###there is only one odor in python
#			;numerical information that is equal for all glomeruli
#    ArrayNumInfos.iloc[:,1] = 999 #OdorToNumber deprecated. 
    # better syntax options:
#    ArrayNumInfos[NOdorNr] = 999
#    ArrayNumInfos.loc[:,NOdorNr] = 9999
#			ArrayNumInfos(1, *) = OdourToNumber(p1.metadata.odor(duft));number code of odour
    ArrayNumInfos['NOdorNr'] = 999
#			ArrayNumInfos(2, *) = p1.metadata.odor_nr(duft);number code of odour concentration
    ArrayNumInfos['NOConc'] = p1.metadata.odor_nr
#			ArrayNumInfos(3, *) = p1.metadata.stimulus_on;stimulus on
    ArrayNumInfos['NStim_on'] = p1.metadata.stimulus_on
#			ArrayNumInfos(4, *) = p1.metadata.stimulus_end;stimulus off
    ArrayNumInfos['NStim_off'] = p1.metadata.stimulus_end
#			ArrayNumInfos(5, *) = p1.metadata.frames;no of frames
    ArrayNumInfos['NNoFrames'] = p1.metadata.frames
#			ArrayNumInfos(6, *) = fix(1000/p1.metadata.frequency);inverse of frequency in ms, Cycletime
    ArrayNumInfos['NFrameTime'] = 1000/p1.metadata.frequency
#			ArrayNumInfos(7, *) = p1.metadata.os9time(0)*60 + p1.metadata.os9time(1) - (p1.metadata.odors-duft) ;measurement time, check calculation
    ArrayNumInfos['NRealTime'] = p1.metadata.os9time  ## simplified version
#			ArrayNumInfos(8, *) = p1.metadata.treat_conc;number code of concentration of treatment
    ArrayNumInfos['NPhConc'] = p1.metadata.treat_conc
#			ArrayNumInfos(9, *) = p1.metadata.shiftX
    ArrayNumInfos['NshiftX'] = p1.metadata.shiftX
#			ArrayNumInfos(10,*) = p1.metadata.shiftY
    ArrayNumInfos['NshiftY'] = p1.metadata.shiftY
#			ArrayNumInfos(11,*) = p1.metadata.kontrollmessung ; zahl der kontrollmessung
    ArrayNumInfos['NcontMeasu'] = p1.metadata.kontrollmessung
#			ArrayNumInfos(12,*) = p1.metadata.messungszahl ; zahl der messung
    ArrayNumInfos['NNumMeasu'] = p1.metadata.messungszahl
#			ArrayNumInfos(13,*) = p1.metadata.stimulus_ISI ; interstimulus Interval
    ArrayNumInfos['Nstim_ISI'] = p1.metadata.stimulus_ISI
#			ArrayNumInfos(15,*) = p1.metadata.stim2On ; second stimulus onset
    ArrayNumInfos['Nstim2ON'] = p1.metadata.stim2ON
#			ArrayNumInfos(16,*) = p1.metadata.stim2Off ; second stimulus offset
    ArrayNumInfos['Nstim2OFF'] = p1.metadata.stim2OFF
#			ArrayNumInfos(17,*) = p2.age ;age of the animal
    ArrayNumInfos['NAge'] = p1.metadata.Age
#			ArrayNumInfos(18,*) = p2.ageMax ;age of the animal
    ArrayNumInfos['NAgeMax'] = p1.metadata.Agemax
#			;text information that is equal for all glomeruli
#			ArrayTxtInfos(1,*) = p1.metadata.odor(duft);text code of odour
#			ArrayTxtInfos(2,*) = p1.metadata.experiment;experiment
#			ArrayTxtInfos(3,*) = p1.metadata.remark;any comment
#			ArrayTxtInfos(4,*) = p1.metadata.treatment;any comment
#			ArrayTxtInfos(5,*) = stringzero(2,p1.metadata.pharma_time(0))+ ':' +stringzero(2,p1.metadata.pharma_time(1))+':'+stringzero(2,p1.metadata.pharma_time(2)) ; appplacation time of treatment
#			ArrayTxtInfos(6,*) = stringzero(2,p1.metadata.os9time(0))    + ':' +stringzero(2,p1.metadata.os9time(1))    +':'+stringzero(2,p1.metadata.os9time(2)) ; appplacation time of treatment
#			ArrayTxtInfos(7,*) = p1.metadata.viewLabel;any comment
#			ArrayTxtInfos(8,*) = p1.metadata.ex_name;any comment
#			ArrayTxtInfos(9,*) = flag[stg_reporttag]
#			ArrayTxtInfos(10,*) = p2.dbb2
    ArrayTxtInfos.iloc[:,1] = p1.metadata.odor #;text code of odour
    ArrayTxtInfos.iloc[:,2] = p1.metadata.experiment #;experiment
    ArrayTxtInfos.iloc[:,3] = p1.metadata.remark #;any comment
    ArrayTxtInfos.iloc[:,4] = p1.metadata.treatment #;any comment
    ArrayTxtInfos.iloc[:,5] = str(p1.metadata.pharma_time) #stringzero(2,p1.metadata.pharma_time(0))+ ':' +stringzero(2,p1.metadata.pharma_time(1))+':'+stringzero(2,p1.metadata.pharma_time(2)) ; appplacation time of treatment
    ArrayTxtInfos.iloc[:,6] = str(p1.metadata.os9time) #stringzero(2,p1.metadata.os9time(0))    + ':' +stringzero(2,p1.metadata.os9time(1))    +':'+stringzero(2,p1.metadata.os9time(2)) ; appplacation time of treatment
    ArrayTxtInfos.iloc[:,7] = p1.metadata.viewlabel #;any comment
    ArrayTxtInfos.iloc[:,8] = p1.metadata.ex_name #;any comment
    ArrayTxtInfos.iloc[:,9] = flag.STG_ReportTag
    ArrayTxtInfos.iloc[:,10] = p1.metadata.dbb2
#			;now goes to all glomeruli, insert their data into TraceArray
    print('ExportGlomeruli: os9time and pharma_time: ', p1.metadata.os9time, p1.metadata.pharma_time)
    print('ExportGlomeruli info: ', ArrayTxtInfos.iloc[0,5], ' ', ArrayTxtInfos.iloc[0,6])

    GloMask = IDL.bytarr(p1.metadata.format_x,p1.metadata.format_y)
#			for glo=0, GlomeruliNum-1 do begin
    for (glo,row) in gloList.iterrows():
        glo -= 1 # in read_glo_liste, index starts with 1 (because the first row is used)
            # but I use glo for .iloc, therefore it has to start with 0 -> subtract 1
            
#				IF (reportAreas ge 1) THEN begin ; get areas from TIFF or area file
        if reportAreas in (1, 2):  ##check that the right columns in gloList are used, the IDL code uses x and y
            GloMask = (maskAreas == row.num_glo)
#				    positions = where(maskAreas eq gloList(0,glo))
#			    	;write information which is peculiar to this glomerulus
            ArrayNumInfos.iloc[glo,0] = row.num_glo
#			    	ArrayNumInfos(0,glo) = gloList(0,glo)
            ArrayTxtInfos.iloc[glo,0] = 'Area'+str(row.num_glo)+'; Pixels: '+ str(row.y_glo)
#			    	ArrayTxtInfos(0,glo) = 'Area'+strtrim(string(gloList(0,glo)),2)+':Pixels'+strtrim(string(gloList(1,glo)),2) ;gives the name of the area
            ArrayNumInfos[glo,14] = 0
#					ArrayNumInfos(14,glo) = DUFT # in python, there is only odor 0 DUFT ; layer/odor
#					bufferset = DUFT
        elif reportAreas in (3, 4):
            GloMask = roi_masks_list[glo]
            ArrayNumInfos.iloc[glo, 0] = row.num_glo
            ArrayNumInfos[glo, 14] = 0
            if reportAreas == 3:
                ArrayTxtInfos.iloc[glo, 0] = roi_datas[glo].write_to_text_line().rstrip("\n")
            else:
                ArrayTxtInfos.iloc[glo, 0] = 'ILTIS-AreaTIF ' + str(row.num_glo) + '; Pixels: ' + str(row.pixel_count)

        else:
#				endIF else begin ;get glomeruli as coordinate
            x = row.x_glo
            y = row.y_glo
            xborders = [x-radius,x+radius+1] #add 1, because python does not include the right value
            xborders = np.clip(xborders, 0, p1.metadata.format_x) #simplified in python, no print feedback
#			    	IF ((xborders(0) lt 0) OR (xborders(1) gt (p1.format_x-1))) THEN begin
#			    		xborders = (xborders > 0 ) < (p1.format_x-1)
#			    		print, 'x coordinates clipped: ',x, xborders,' in glo ',glo
#						ArrayTxtInfos(3,glo) = 'coordinates clipped';any comment
#			    	ENDif
            yborders = np.clip([y-radius,y+radius+1], 0, p1.metadata.format_y)
#			    	IF ((yborders(0) lt 0) OR (yborders(1) gt (p1.format_y-1))) THEN begin
#			    		yborders = (yborders > 0 ) < (p1.format_y-1)
#			    		print, 'y coordinates clipped: ',y, yborders,' in glo ',glo
#			    		ArrayTxtInfos(3,glo) = 'coordinates clipped';any comment
#			    	ENDif
#			    	;write information which is peculiar to this glomerulus
            ArrayNumInfos.iloc[glo,0] = row.num_glo # gloList[2,glo]
            ArrayTxtInfos.iloc[glo,0] = 'Coor'+str(x)+' : '+str(y) # ;gives the coordinates
#			    	;choose relevant dataset, for multiple layers, column 4 in coor file
#separateLayers not implemented in python
#			    	IF separateLayers THEN begin
#			    		bufferSet = liste(3,glo)
#			    	endIF else begin
#			    		bufferSet = DUFT
#			    	endELSE
            ArrayNumInfos.iloc[glo,14] = 0 # there is only one odor in python, and no layers bufferSet ; layer/odor
#					;create dummy mask for this glomerulus
            GloMask[:] = 0
            GloMask[xborders[0]:xborders[1],yborders[0]:yborders[1]] = 1
#            positions = GloMask == 1
#				endELSE ;reportAreas
        ArrayGloTraces.iloc[glo,:] = ViewTools.calc_timetrace(p1.sig1, GloMask) #x,y,t
        # python, moved here from below because CTV is always calculated
        ctv_handler_obj = PixelWiseCTVHandler(flags=flags, p1=p1)
        ArrayNumInfos.loc[glo,ctv_tag] = ctv_handler_obj.apply_pixel(ArrayGloTraces.iloc[glo,:])
#				;calculate Traces
#				For i=0, p1.metadata.frames-1 do begin
#					dummyFrame = signals(*,*,i,bufferSet)
#					ArrayGloTraces(i,glo) = mean(dummyFrame(positions))
#				endFOR
#			    ;now the signals are in traceArray
#			    ;set all values to -99 for fake glomeruli
############ skip the fake glomeruli in python
#                IF (reportAreas eq 0) then begin
#
#			    	IF (liste(2,glo) lt 0) then begin
#			    		for i = 0, p1.metadata.frames-1 do begin
#			    			ArrayGloTraces ( i, glo) = -99
#			    		endFOR
#			    	endIF
#			    endif
#			endfor; glo


#################### all done, now write data
#			;filenames
    traces_dir_path = pl.Path(flags.get_op_traces_dir())
    traces_dir_path.mkdir(parents=True, exist_ok=True)
    user_spec_label = flags.get_measurement_label(measurement_row)
    reportFileData = str(traces_dir_path / user_spec_label)
#;   			reportFileInfoNum     = flag[stg_OdorReportPath]   + flag[stg_ReportTag] + '.gloInfN'
#;   			reportFileInfoTxt     = flag[stg_OdorReportPath]   + flag[stg_ReportTag] + '.gloInfT'
#;			;write the curves of this odour to file
#;			openu, unit, reportFileData, /get_lun ,/append
#;			formatLine1 = '((F8.3,'+ strtrim(string(p1.metadata.frames-1),2) + '("' + string(9b) + '",F8.3)))'
#;			printf,unit, ArrayGloTraces, FORMAT=formatline1
#;			free_lun, unit
#;			;write numerical information
#;			openu, unit, reportFileInfoNum, /get_lun ,/append
#;			formatLine2 = '((I,8("' + string(9b) + '",I)))' ;
#;			printf,unit, ArrayNumInfos, FORMAT=formatline2
#;			free_lun, unit
#;			;write text information
#;			openu, unit, reportFileInfoTxt, /get_lun ,/append
#;			formatLine3 = '((A,5("' + string(9b) + '",A)))' ;
#;			printf,unit, ArrayTxtInfos, FORMAT=formatline3
#;			free_lun, unit


#### write .glodatamix in Python simplified:
    # always write CTV
    # always write all info
    if exportOption: #this is always the case, 
        #change once in python there are more options
        reportFileData = reportFileData + '.gloDatamix.csv'
        # joint the num, txt, glo dataframes; does not work on columns, because they have different names
        ArrayAll = pd.concat([ArrayNumInfos,ArrayTxtInfos,ArrayGloTraces], axis=1)
        # check if file exists, load it
        # if os.path.isfile(reportFileData):
        #     ArrayOld = pd.read_csv(reportFileData, sep=';',header=0)
        #     ArrayAll = pd.concat([ArrayOld,ArrayAll], axis=0)
        #now write the file to data
        ArrayAll.to_csv(reportFileData, sep=';',header=1, index=False)
#
#
#		IF (exportOption eq 111)  then begin
#			;write the header of the glodatamix file
#			;but only if the file is new
#			;then continue as with exportOption eq 1
#			;check for file existence
#			existFileFalse = NOT(existFile(reportFileData+'.gloDatamix'))
#			;openu, unit, reportFileData+'.gloDatamix', /get_lun ,/append new IDL: openw
#			IF existfilefalse THEN begin ;create new file, write header
#				;create a text array for the data
#				ArrayDataLabels = replicate('data',p1.metadata.frames) + strtrim(indgen(p1.metadata.frames),2)
#				openw, unit, reportFileData+'.gloDatamix', /get_lun ,/append
#			 	printf,unit, ArrayNumLabels,ArrayTxtLabels,ArrayDataLabels, $
#			 			FORMAT=format_line([numinfos,txtinfos,p1.metadata.frames],['A','A','A'])
#			 	close, unit
#			 	free_lun, unit
#				print, 'written column headers in file: ',reportFileData+'mix'
#			endIF
#			;reset exportOption for this odor, and for the next
#			exportoption = 1
#		endIF
#
#
#		IF (exportOption eq 119) then begin ;write timetrace AND ctv; but CTV to the right
#			;write the header of the glodatamix file
#			;but only if the file is new
#			;then continue as with exportOption eq 1
#			;check for file existence
#			existFileFalse = NOT(existFile(reportFileData+'.gloDatamix'))
#			;openu, unit, reportFileData+'.gloDatamix', /get_lun ,/append new IDL: openw
#			IF existfilefalse THEN begin ;create new file, write header
#				;create a text array for the data
#				ArrayDataLabels = replicate('data',p1.metadata.frames) + strtrim(indgen(p1.metadata.frames),2)
#				openw, unit, reportFileData+'.gloDatamix', /get_lun ,/append
#				ctvString = 'N_CTV'+strtrim(string(fix(flag[ctv_method])),2)
#			 	printf,unit, ArrayNumLabels,ctvString,ArrayTxtLabels,ArrayDataLabels, $
#			 			FORMAT=format_line([numinfos,1,txtinfos,p1.metadata.frames],['A','A','A','A'])
#			 	close, unit
#			 	free_lun, unit
#				print, 'written column headers in file '
#			endIF
#			;write combined information
#			;openu, unit, reportFileData+'.ctv.gloDatamix', /get_lun ,/append ; new IDL: openW
#			openw, unit, reportFileData+'.gloDatamix', /get_lun ,/append
#			ctvString = 'CTV'+strtrim(string(fix(flag[ctv_method])),2)
#			For i = 0, GlomeruliNum-1 do begin
#					ctvValue = CurveToValue(ArrayGloTraces(*,i))
#			 		printf,unit, ArrayNumInfos(*,i),ctvValue,ArrayTxtInfos(*,i), ArrayGloTraces(*,i), $
#						FORMAT=format_line([numInfos,1,txtInfos,p1.metadata.frames],['I','F8.3','A','F8.3'])
#			 			;FORMAT='((F8.3,'+strtrim(string(numinfos),2)+'("' + string(9b) + '",I)),('+strtrim(string(txtinfos+1),2)+'("' + string(9b) + '",A)),('+ strtrim(string(p1.metadata.frames),2) + '("' + string(9b) + '",F8.3)))'
#			EndFor
#
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'.gloDatamix'
#		endIF
#
#
#		IF (exportOption eq 1) then begin
#			;write combined information
#			;openu, unit, reportFileData+'.gloDatamix', /get_lun ,/append new IDL: openw
#			openw, unit, reportFileData+'.gloDatamix', /get_lun ,/append
#			IF (p1.metadata.frames gt 3000) THEN begin
#				ArrayGloTraces = congrid(ArrayGloTraces,3000,GlomeruliNum,/interp)
#				shrinkFrames = p1.metadata.frames
#				p1.metadata.frames = 3000
#				print, 'WARNING in exportGlomeruli!!! Frames artificially reduced to 3000'
#			endIF
#			For i = 0, GlomeruliNum-1 do begin
#			 		printf,unit, ArrayNumInfos(*,i),ArrayTxtInfos(*,i), ArrayGloTraces(*,i), $
#			 			FORMAT='((I,'+strtrim(string(numinfos-1),2)+'("' + string(9b) + '",I)),('+strtrim(string(txtinfos),2)+'("' + string(9b) + '",A)),('+ strtrim(string(p1.metadata.frames),2) + '("' + string(9b) + '",F8.3)))'
#			EndFor
#
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'mix'
#		endIF
#
#		IF (exportOption eq 2) then begin
#			;write combined information, but only CTV value
#			;openu, unit, reportFileData+'.CTV.gloDatamix', /get_lun ,/append new IDL: openw
#			openw, unit, reportFileData+'.CTV.gloDatamix', /get_lun ,/append
#			;calculate CTV
#			ctvString = 'CTV'+strtrim(string(fix(flag[ctv_method])),2)
#			For i = 0, GlomeruliNum-1 do begin
#					ctvValue = CurveToValue (ArrayGloTraces(*,i))
#			 		printf,unit, ArrayNumInfos(*,i),ArrayTxtInfos(*,i),ctvString, ctvValue , $
#			 			FORMAT='((I,'+strtrim(string(numinfos-1),2)+'("' + string(9b) + '",I)),('+strtrim(string(txtinfos+1),2)+'("' + string(9b) + '",A)),('+ strtrim(string(1),2) + '("' + string(9b) + '",F8.3)))'
#			EndFor
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'CTV'
#		endIF
#
#		IF (exportOption eq 3) then begin ;write data vertically
#			;write combined information
#			;openu, unit, reportFileData+'.trans1.gloDatamix', /get_lun ,/append new idl, openw
#			openw, unit, reportFileData+'.trans1.gloDatamix', /get_lun ,/append
#			for i = 0, numInfos-1	do begin ; write numeric information
#			 	printf, unit, ArrayNumInfos(i,*), $
#			 			FORMAT='(I,'+strtrim(string(GlomeruliNum-1),2)+'("' + string(9b) + '",I))'
#			endFOR
#			for i = 0, txtInfos-1	do begin ; write numeric information
#			 	printf, unit, ArrayTxtInfos(i,*), $
#			 			FORMAT='(A,'+strtrim(string(GlomeruliNum-1),2)+'("' + string(9b) + '",A))'
#			endFOR
#			for i = 0, p1.metadata.frames-1	do begin ; write numeric information
#			 	printf, unit, ArrayGloTraces(i,*), $
#			 			FORMAT='(F8.3,'+strtrim(string(GlomeruliNum-1),2)+'("' + string(9b) + '",F8.3))'
#			endFOR
#
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'mix'
#		endIF
#
#		IF (exportOption eq 4) then begin ;write timetrace AND ctv
#			;write combined information
#			;openu, unit, reportFileData+'.ctv.gloDatamix', /get_lun ,/append ; new IDL: openW
#			openw, unit, reportFileData+'.ctv.gloDatamix', /get_lun ,/append
#			ctvString = 'CTV'+strtrim(string(fix(flag[ctv_method])),2)
#			IF (p1.metadata.frames gt 3000) THEN begin
#				ArrayGloTraces = congrid(ArrayGloTraces,3000,GlomeruliNum,/interp)
#				p1.metadata.frames = 3000
#				print, '******************* WARNING in exportGlomeruli!!! Frames artificially reduced to 3000'
#			endIF
#			For i = 0, GlomeruliNum-1 do begin
#					ctvValue = CurveToValue(ArrayGloTraces(*,i))
#			 		printf,unit, ctvValue,ArrayNumInfos(*,i),ctvString,ArrayTxtInfos(*,i), ArrayGloTraces(*,i), $
#						FORMAT=format_line([1,numInfos,1+txtInfos,p1.metadata.frames],['F8.3','I','A','F8.3'])
#			 			;FORMAT='((F8.3,'+strtrim(string(numinfos),2)+'("' + string(9b) + '",I)),('+strtrim(string(txtinfos+1),2)+'("' + string(9b) + '",A)),('+ strtrim(string(p1.metadata.frames),2) + '("' + string(9b) + '",F8.3)))'
#			EndFor
#
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'mix'
#		endIF
#
#		IF (exportOption eq 25) then begin
#			;write combined information, but multiple CTV values
#			;openu, unit, reportFileData+'.CTV.gloDatamix', /get_lun ,/append new IDL: openw
#			openw, unit, reportFileData+'.CTMV.gloDatamix', /get_lun ,/append
#			;calculate CTMV
#			ctvString = 'CTMV'+strtrim(string(fix(flag[ctvm_method])),2)
#			For i = 0, GlomeruliNum-1 do begin
#					ctvValue = Curve2MultiValue (ArrayGloTraces(*,i))
#					;how many elements in ctvValue?
#					ctvSize = n_elements(ctvValue)
#					;call: formatline = format_line([3,5,3,4],['I','A','F8.3','A'] for 3 integers, 5 chars, 3 floats, 4 chars
#			 		printf,unit, ArrayNumInfos(*,i),ArrayTxtInfos(*,i),ctvString, ctvValue , $
#						FORMAT=format_line([numInfos,txtinfos+1,ctvSize],['I','A','F8.3'])
#			EndFor
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'CTV'
#		endIF
#
#;					  26 Calles Array2Curve
#
#		IF (exportOption eq 26) then begin
#			;write a single trace from the entire array
#			;as calculated in array2curve - A2C
#			openw, unit, reportFileData+'.A2C.gloDatamix', /get_lun ,/append
#			;calculate CTMV
#			ctvString = 'A2C'+strtrim(string(flag[ctv_method]),2)
#			array2curve, ArrayGloTraces, outCurve
#			;outcurve is the trace to plot
#			;use glomerulus 0 in arraynuminfo and arraytxtinfo
#			printf,unit, ArrayNumInfos(*,0),ArrayTxtInfos(*,0),ctvString, outCurve(*), $
#						FORMAT=format_line([numInfos,txtinfos+1,p1.metadata.frames],['I','A','F8.3'])
#			close, unit
#			free_lun, unit
#			print, 'printed reportfiles: ',reportFileData+'.A2C.gloDatamix'
#		endIF

    print('done ExportGlomeruli')
    return reportFileData
