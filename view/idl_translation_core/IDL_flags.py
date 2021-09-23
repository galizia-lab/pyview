# -*- coding: utf-8 -*-
"""
Created on Mon May 28 16:48:33 2018

@author: Giovanni Galizia
"""

# all flags from IDL now as lists
import pandas as pd
import os

def IDL_default_flags(STG_MotherOfAllFolders=''):
    # this version taken from master_jacob_sorted.pro
    # if STG_MotherOfAllFolders is empty, then current working directory is used
#, sample master file
#, containing all available flags as of september 2008
#, sorted in logical groups
#, note, however, that not all flag settings are mentioned
#, you still need to know what you can do and what the program does
#, and you still need to run the necessary constrols


# ALL IDL flags are in here now,
# ALSO those that were not called flags
# and the Movie flags also
# however - all commented out. Only free those that are being used
# in order to keep track of the new code
    
    if STG_MotherOfAllFolders == '':
        STG_MotherOfAllFolders = os.getcwd()
    
    IDL_flag     = pd.Series({
## system flags, many not necessary for the python version
            "VIEW_batchmode": 1, # choice between interactive mode and VIEW_batchmode
#            "MacSystem": "deprecated",
## format flags, not all necessary for python version
#            "TrueColour": 1,
            "SO_MV_colortable": 13,
##
##,*****************************
##,flags related to LOADING DATA
##,*****************************
##
##	,format of data files (used in LoadDataMaster.pro)
            "LE_loadExp" : 3, #20, # 3,4 	, 0 for old setup, to 1 for Visicam, 2 for confocal
##	,TILL photonics single wavelength: 3
##	,TILL photonics dual wavelength (FURA): 4
##	,ZEISS multiphoton data: 20
##
##	,should the raw data be median filtered? (used in ViewLoadData\MedianCorrection.pro)
            "Data_Median_Filter" : 0, #in ViewLoadData.MedianCorrection
##	,do a median correction when loading the data
##	,0: no median
##	,1: median in space fixed values
##	,2: median in time fixed values
##	,3: median in space and time, using flag values (Data_Median_Filter_space)(Data_Median_Filter_time)
            "Data_Median_Filter_space": 3,
##	, used with Data_Median_Filter eq 3
            "Data_Median_Filter_time": 0,
##	, used with Data_Median_Filter eq 3
##
##	,apply an off-line binning (shrinkFaktor).
            "LE_ShrinkFaktor": 0, #     ,no shrinkfaktor with 1
##
##	,are there different focal depth to be split?
#            "RM_separateLayers": 0,
##	,separates the layers in exportGlomeruli and SingleOverviews
##
##	,how to make movement correction based on .moveList file. (used in ViewLoadData\MovementCorrectionMaster.pro)
            "CSM_Movement": 0,
##	,set to 0: no movement correction (BUT shifts from .lst file are USED!)
##	,set to 1: on the spot movement correction
##	,set to 2: as 1, but calculated movements are saved in the moveList file
##	,set to 3: movement values are read from the moveList file
##	,set to 5: no movement correction, but shifts are taken from the movement file
##	,values above 10: mathiasCorrection.
#            "CSM_DataShift": 0,
##	,set to 0: data is NOT shifted, coordinates ARE shifted
##	,set to 1: data IS shifted, coordinate are NOT shifted
##	,set to 2: NONE is shifted
##
##	,trim the data frames to be loaded
##	,remove n frames at the beginning of each measurement
#            "CSM_SkipFrmUpFront": 0,
##	,remove n frames at the end of each measurement
#            "CSM_SkipFrmAtBack": 0,
##
##	,settings to reduce memory usage
#            "VIEW_No4Darray": 1,
##	,this reduces the sig1 array to a 3D array instead of a 4D array, not all routines work with this setting
##	,set to 1: odor 0 is cut off memory after loading the data, p1.odors is reduced by 1
#### Python: implement single odor use only, for now
#### therefore VIEW_No4Darray is 1 by default
#### sig1 is (x,y,t) and not (x,y,t,o)
##
            "VIEW_DeleteRawData": 0,
##	,this removes the raw data from memory after loading
##
##	,correct for scattered light, improving spatial resolution	(used in CalcSigAll3000.pro)
            "VIEW_ScatterLightFactor": 0,
##	,for the 3xyy and 4xyy family with scattered light correction, this factor gives the strength of the unsharp mask. Default: 1
##	,only used if (yy ne 00)
##
##	,load more than one experiment at the time
#            "view_MultiExp": 0, # 	, 0 for single experiment
##	,load AIR trial alongside the odor response (air trial is given in control column in the .lst file)
            "LE_AskForAir": 0, # 	, 0 for not loading air
##
##,END of flags related to loading data
##
##
##,************************************
##,flags related to CALCULATING SIGNALS
##,************************************
##
##	,how to calculate the data (used in ViewCalculateData\CalcSigMaster.pro)
            "LE_CalcMethod" : 4900, #see calcsigmaster3000
##	,family 3xyy (deltaF/f) and 4xyy (ratio) uses x for bleach correction settings, and yy for scattered light correction
##	,see  CalcSigAll3000.pro for detailed settings. Example are:
##			, setting:    0 1 2 3 4 5 6 7 8 9
##			,alPerimeter  + + + + - - - - C - , with 8 bleaching is in coordinates only (variable: CoorPerimeter)
##			,excludeStim  - + - + - + - + - - , exclude stimulus is obsolete - controled by LE_BleachStartFrame group
##			,addNoise     - - + + - - + + - -
##			,no bleach    - - - - - - - - - +
##			,air bleach   - - - - - - - - + - ,correct with bleach parameters taken from air trial
##	,set to 3 for no calculation (original data).
##
##	,which frames to use for calculating F in deltaF/F
            "LE_StartBackground"   		: 4,# for deltaF/F calculations, or bleach corrections
##	,set to -1 not to subtract background in data calculation, to frame for background start. Default: 4
            "LE_PrestimEndBackground"   : 1, # for deltaF/F calculations, or bleach corrections
##	,How many frames before stimulus to stop with background. Default: 2
##	,so: background is calculated from LE_StartBackground to StimulusOn - LE_PrestimEndBackground
##	,that means that StimulusOn is an important parameter and needs to be set correctly for deltaF/F
##
##	,settings for bleach correction when using CalcSigAll3000
            "LE_BleachStartFrame"	: 1, #start bleaching correction here
##	,for logarithmic bleach correction, all frames smaller are excluded in the fit function
##	,used in CalcSigAll3000, default 2
            "LELog_InitialFactor"	: 3, # weigh the frames before stimulus more than those after stimulus
##	,for logarithmic bleach correction, all frames before stimulus onset are more important by this factor
##	,used in CalcSigAll3000, default 1 for maximum compatibility
            "LELog_ExcludeSeconds"	: 6, #how many seconds should be excluded during stimulation for bleach log fitting?
##	,for logarithmic bleach correction, how many seconds after stimulus onset to exclude
##	,used in CalcSigAll3000, default 0 for maximum compatibility
##	,this uses the time information - therefore make sure that is correct
##	,graphic display of weights can be switched of and on in the program CalcSigAll3000
#            "LE_ClipPixels"	: -2000, #how many seconds should be excluded during stimulation for bleach log fitting?
##
##,END of flags related to calculating signals
##
##
##,************************************
##,flags related to SIGNAL CORRECTIONS
##,************************************
##,note: this is for the extra set of corrected signals, not for corrections done during loading or calculation
##
##
#            "VIEW_InitCorr"			: -1	,# 18 : inverted (Fura at 810nm). set to -1 in order not to create a corrected data set
#            "VIEW_CorrSignals"				: 0 	,# set to 1 to access corrected dataset, to 0 to access original data set
##
##
##
##,*************************************
##,flags related to data analysis OUTPUT
##,*************************************
##
            "VIEW_ReportMethod"		: 10	, #which output do you want? This is one of the main flags
##										, all settings are in View_gr_reports\subloop_report.pro, the most often used are
##										, 10: false-color coded pictures (calls reportTIFF)
##										, 11, 111: glodatamix (without, with tags)
##										, 12: movies
##										, 15: single TIFFs
##										, 19: 119: glodatamix with CTV (without, with tags)
##
            "CTV_Method"			: 22	, #curve-to-value function for single number output or still images
##										, 22 gives
##										, 22 is the difference between two fixed points
##										, 35 relates to the maximum within 3 secs after stimulus onset
##										, all values in ViewOverview\CurveToValue
##										, values below 0 go to personal program in ImageALlocal folder: CurveToValueLocal.pro
#            "CTVM_Method"			: 0,#		, for multiple CTV values at once, not safely implemented yet
##
## "firstframe" was not in flags
            "CTV_firstframe" 					: 18  ,# many CTVs use fixed frames. These use the variables firstFrame and lastFrame
            "CTV_lastframe"  					: 22	, #for example, CTV 22 calculates the difference between lastframe (3 frames) and firstframe (3 frames)
##
#            "LE_FirstBuffer"		: 1		, #sets which buffer to start with in output routines
##										, standard is 1. Set to 0 to start with 0 (generally 0 is empty)
##										, instead of LE_firstbuffer you can use LE_usefirstbuffer (synonymous)
##
##	,old flags, currently out of fashion
#            "PTA_PlotTimeRange"		: 0,#
#            "PTA_PlotMeanValue"		: 0,#
##
##	,flags specifically for graphical output (TIFF files and the like, i.e. "overviews")
            "SO_Method"			: 10	, #used in ViewOverview\Overview.pro. Only values 0 or 10 are used now
##										,  0 for calculations pixel by pixel (i.e. on the time-course in each pixel)
##										, 10 for calculations frame by frame (much faster, but not all functions are possible)
##										, for 10, the CTV value is applied within ViewOverview\overview10ctv.pro
            "SO_individualScale"			: 0,# what scaling to use? 0 for fixed values, else individual scale for each frame
##										, 3 for scaling within center of each frame
##										, can be used in quite sophisticated ways, see ViewOverview\SingleOverviews.pro
##										, also explained in the documentation
## "SO_MV_scalemax" was not in flags
            "SO_MV_scalemax":  18.000	,# value to scale maximum to with SO_indiScale equals 0
            "SO_MV_scalemin": -5.000	,# corresponding value for minimum
##
#            "SO_morphoBackgr"		: 0		, #Used to show an anatomical picture with an overlay of only the strongest POSITIVE responses
#            "SO_morphoBackgrNeg"	: 0		, #Used to show an anatomical picture with an overlay of only the strongest NEGATIVE responses
            "SO_withinArea"		: 1		, #False-color output limited to the mask in the .area file
##
            "CTV_scalebar"			: 1		, #some output options allow to print out the color scalebar (SingleOverviews.pro)
            "RM_fotook"				: 0		, #Overlay other information to overview output, (SingleOverviews.pro)
##										, 1: puts squares in the coordinate positions (from .coor file)
##										, 5: shows the perimeter of the .area file
#            "RM_differentViews"	: 0		,# Change view, e.g. mirror flip right ALs   (SingleOverviews.pro)
            "RM_unsharpmask"		: False		, #Post-hoc filter on false-color images     (SingleOverviews.pro)
##
            "RM_NewColumn"			: 1		, #Start a new column in "tapeten" output    (SingleOverviews.pro)
##										, this flag is generally set in the gr_XXX file
##
##	,old flags
#            "RM_PlotTrace"			: 0		,#
#            "RM_PrintAscii"		: 0		,#
#            "RM_PrintLine"			: 1		,#
            "RM_ROItrace"			: 0		,# to select area file in exportglomeruli
            "RM_nextposition"    : [0,0], #position of a frame in output canvas 
##
##
##	,flags for filters
            "RM_Radius"				: 5		, #For calculating traces (glodatamix), or for some spatial filters
                                            #used in CalcSigAll3000, also singleoverviews
## "Signal_FilterSpaceFlag" was not in flags
            "Signal_FilterSpaceFlag"	   : 1 	, #If set to 1, the signal is calculated on the time trace at each pixel
##										, after taking the mean of the pixels around it (RM_Radius). Therefor this is a slow filter
##										, If set to 0, this filter is switched off
            "Signal_FilterSpaceSize"	   : 3 	, #Filter size applied after overview calculation, always.
##										, set to 0 when Signal_FilterSpaceFlag is on, to avoid double filtering.
            "Signal_FilterTimeFlag"		: 1		, #Switch for the temporal filter
            "Signal_FilterTimeSize"    : 3		,# Size of the temporal filter
##
##
##,*******************************************
##,flags to control PATHS for input and output
##,*******************************************
##
##	, this is one standard arrangement of folders
##	, just adapt the STG_MotherOfAllFolders, but all subfolders must exist
##	, place where all files are
            "STG_MotherOfAllFolders": STG_MotherOfAllFolders , #
##
##
            "STG_ReportTag"		  : 'animal' , #this contains the animal flag, set this for each round and animal, ( jacob: if not using the gr_xxx method)
##											, this is set within the gr_file
            "STG_Measu"         : 0, # measurement tag in .lst file [added in Python]
##
##	, folder for the data files, STG_MotherOfAllFolders added below
####            "STG_Datapath": STG_MotherOfAllFolders + 'data_jacob_LSM\'
            "STG_Datapath"      :  os.path.join(STG_MotherOfAllFolders, 'data'),
##	, folder for the .inf files
            "STG_OdorInfoPath"	: os.path.join(STG_MotherOfAllFolders, 'Lists'),
##	, folder for the .coor and the .area file
            "STG_OdormaskPath"	: os.path.join(STG_MotherOfAllFolders, 'Coor'),
##	, folder for the all OUTPUT files
            "STG_OdorReportPath": os.path.join(STG_MotherOfAllFolders, 'IDLoutput'),
##	, folder for the all OUTPUT files
            "STG_OdorReportFile": 'XYZ',
##	, can be used for any text
#            "STG_Missing"		  : '999', 
##
##
##,************************************
##,flags used for MOVIE output
##,************************************
##
##, in interactive mode, these flags are overwritten by the values in
##, imageALlocal\SetExportMovieFlags.pro
##, the variables are defined in view.pro
##
            "mv_exportFormat"		: 'stack_tif' ,#'mpg4', #3		,# 1 for TIFF (single files), 2 for PICT (premiere), 3 for MPEG, 4 for multilayer GIF, 5: multilayer TIF
##										, 6 for uncompressed AVI (generally the best)
            # in python, mv_exportformat is not with numbers any more, but with strings
            "mv_realTime"			: 1		,# insert frames per second, 0 for no realTime, 24 for MPEG, 15 for GIF->QuickTime
##										, AVI can work with any time, therefore 0 IS realTIME. In the other formats, additional frames are invented to create real time
##										, if a negative number is given, that many frames are removed
            "mv_SpeedFactor"		: 1		,# for exportFormat 6, increase or decrease speed of movie
            "mv_reverseIt"			: 0		, #turn it upside down
            "mv_rotateImage"		    : 0		,# rotate only image,  , 0 for no action, 2 for 180 degrees
            "mv_cutborder"			: 0		,# how many pixels to cut from each side (border, to hide filter artefacts)
            "mv_morphoThreshold"		: 0		,# substitutes lower range with morphological image to be taken from file
            "mv_withinArea"			: 0		,# limits output to within the mask in xxx.area
            "mv_sdSignificanceCut"	: 0		,# cuts everything below that significance level. Stimulus is included in calculation, ignored if below 0.1.
##		,								, Not implemented yet
            "mv_markStimulus"			: 1		,# marks stimulus application with a red box
            "mv_percentileScale"		: False		,# scaling to a percentaje of noise. don´t use
            "mv_individualScale"		: 2		,# follows a similar logic to ("so_indiScale")
##										,0, 1: Pixmin and Pixmax are taken
##										,2 : min and maximum of sequence is taken
##										,3 : min and max of central region is taken
##										,4 : max of sequence is taken, min is Pixmin
##										,5 : min and max from area region
##										,6 : min from pixmin, max from area
##										,7 : min from pixmin, max from area but only stimulus + 2*stimulus length
##
            "mv_indiScale3factor"		: 0.2 	,# set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
##										, for mv_individualScale above 100
            "mv_percentileValue"		: 0		,# : float(individualScale MOD 100)/100.0
            "mv_xgap"					: 50	,# vertical + horizontal gaps, only even numbers!
            "mv_ygap"					: 50  	,# 6, 10
            "mv_correctStimulusOnset"	: 0 	,# value to be added to stimulus onset (in frames)
            "mv_displayTime"			: True		,# time in ss:ms as figures
            "mv_minimumBrightness"	: 0		,# creates a mask that depends on the brightnes of the foto
            "mv_suppressMilliseconds" : True,  
##
##
##		,these flags are for interactive use in view (fasttraces)
##		,but are also used in movies to select a frame range for movie output
##		,set both to -1 to calculate the entire movie, else to fixed frame numbers
            "FT_FirstFrame"				: -1		,# show trace subsed in fast traces in VIEW
            "FT_LastFrame"				: -1		,# show trace subsed in fast traces in VIEW
#the Ajay programs do not use FT_FirstFrame, but mv_FirstFrame, and more
            "mv_FirstFrame"				: -1		,# show trace subsed in fast traces in VIEW
            "mv_LastFrame"				: -1		,# show trace subsed in fast traces in VIEW


            "mv_bgColor" : 'b' ,
            "mv_bitrate": '1024k',
# values are 'single_tif', 'stack_tif', 'libx264' or other codecs
            "mv_fgColor": 'w'

##
##		,flags that are also relevant for movies, do NOT change them here to avoid confusion, change them above
##		,check program viewoverview\Exportmovie
##		,"ctv_scalebar"
##		,scaleMin
##		,scaleMax
##		,filterSpaceFlag
##		,filterSpaceSize
##		,SO_MV_colortable
##		,FILENAME defined in localOdorText
##,end of movie settings
##
##
##
##,************************************
##,flags NOT USED for off-line analysis
##,************************************
##
##	"LE_ShowBox"				: 0		,
##	"FT_AllOdors"				: 0		, show all odor traces in fast traces in VIEW
##	"FT_TimeXAxis"				: 0		, show time as x-axis in fast traces in VIEW
##	"FT_Subset"					: 0		, show trace subsed in fast traces in VIEW
##	"FT_SelectFrame"			: 0		, show trace subsed in fast traces in VIEW
##
##
##,"VIEW_InitCorr"			: -1 , erase this line after analysis of these animals
##,	"STG_OdorReportPath"		: STG_MotherOfAllFolders + 'IDL_jacob_glomInteraction\IDLoutput\movies\j080730b\'
##,gr_takefromlist, 'j080730b',2
##,	"STG_OdorReportPath"		: STG_MotherOfAllFolders + 'IDL_jacob_glomInteraction\IDLoutput\movies\j080730c\'
##,gr_takefromlist, 'j080730c',2
            })

# here: change STG paths to add "mother of all directories" to it
    

#test 
    return IDL_flag



#########################################################
########## Main starts here
#########################################################
    
#define flag structure
IDL_flag = IDL_default_flags('') # can also be called with empty brackets()


# end of program