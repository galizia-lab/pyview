import numpy as np
import scipy.ndimage as sci
import logging
from view.python_core.areas import read_area_file

# solution from https://stackoverflow.com/a/49480246
from .bleach_correction import fitlogdecay, get_bleach_weights

if __package__ is None or __package__ == '':  # if Master_Hannah2018.py is importing this file
    pass
else:  # if we are importing this file from a package, e.g., using view.idl_translation_core.ViewOverview
    pass
#import scipy.optimize as sco


def CalcSigMaster(flag, p1):
    #PRO CalcSigMaster, raw, dark, p, method, relative_changes

    method1 = flag["LE_CalcMethod"] #keep this renaming for the lines below
#    if ((method1 gt  1000) AND (method1 lt  2000)) THEN method1= 1000
#    if ((method1 ge  3000) AND (method1 lt  4000)) THEN method1= 3000
#    if ((method1 ge  4000) AND (method1 lt  5000)) THEN method1= 4000
#    if ((method1 ge  5000) AND (method1 lt  6000)) THEN method1= 5000
#    if ((method1 ge 10000) AND (method1 lt 19000)) THEN method1=10000
#
#; Master Procedure to calculate relative changes from rawdata for all odors
#; several different Methods can be used

# addMeasurement = fix(flag[view_MultiExp])
################################################
# these numbers do not match the IDL numbers any more
    
    if method1 == 0:
        p1 = CalcSigAll0(p1, flag) #absolute values / 1000, effectively raw data
        # in IDL, this was method 3
    elif method1 == 1:
        p1 = CalcSigAll1(p1, flag) #tbw
#    elif method1 == 2:
#        p1 = CalcSigAll2(p1, flag) #tbw
    elif method1 == 3: #simple deltaF, no thrills
        p1 = CalcSigAll3(p1, flag) #
    elif method1 == 4: #simple ratio, no thrills
        p1 = CalcSigAll4(p1, flag) #pure ratio, no thrills
        # in IDL, this was 15
#9: BEGIN
#		;calculates deltaF, F0 are initial frames to be set in program
#		;includes median bleach correction
#		;and baseline shift to inital values to be set in program
#       CalcSigAll9, raw, dark, p, relative_changes
#  END
#10: BEGIN
#		;calculates RATIOS for fura, and deltaF into air control memory
#		;includes median bleach correction
#		;and baseline shift to initial values, to be set in program
#       CalcSigAll10, raw, dark, p, relative_changes
#  END
#11: BEGIN
#		;calculates RATIOS for fura, and deltaF into air control memory
#		;no baseline shift
#       CalcSigAll11, raw, dark, p, relative_changes
#  END
#12: BEGIN
#		;calculates RATIOS for fura into odour 2, and deltaF 340 into air control memory, deltaF 380 into odour 1
#		;baseline shift
#       CalcSigAll12, raw, dark, p, relative_changes
#  END
#13: BEGIN
#		;calculates RATIOS for fura into odour 2, and deltaF 340 into air control memory, deltaF 380 into odour 1
#		;baseline shift
#       CalcSigAll13, raw, dark, p, relative_changes
#  END
#14: BEGIN
#		;calculates RATIOS for fura into odour 2, and deltaF 340 into air control memory, deltaF 380 into odour 1
#		;baseline shift
#		;constant background correction
#		;unsharp mask correction
#       CalcSigAll14, raw, dark, p, relative_changes
#  END
#15: BEGIN
#		;calculates RATIOS for fura into buffer 1, no other treatment/filter/shift/etc whatsoever
#       CalcSigAll15, raw, relative_changes
#  END
#19: BEGIN
#		;same as 9 but only central region 0.2-0.8 in x and y
#		;calculates deltaF, F0 are initial frames to be set in program
#		;includes median bleach correction
#		;and baseline shift to inital values to be set in program
#       CalcSigAll9, raw, dark, p, relative_changes
#  END
#29: BEGIN
#		;same as 9 but left and right half frames are median corrected separatedly
#       CalcSigAll29, raw, dark, p, relative_changes
#  END
#30: BEGIN
#		;calculates FURA ratio and CaGr-deltaF signals from dual sets (Silke 2001)
#       CalcSigAll30, raw, dark, p, relative_changes
#  END
#39: BEGIN
#		;same as 9 but only AL perimeter is considered
#       CalcSigAll39, raw, dark, p, relative_changes
#  END
#1000: BEGIN
#		; method for substracting a smoothed background (smooth function in IDL)- test version
#		CalcSigAll1000, raw, dark, p, relative_changes, method
#  END
    elif (method1 >= 3000 & method1 < 6000): 
        p1,flag = CalcSigAll3000(p1, flag) #tbw
#		; calculates delta F / F (3000) or FURA (4000) or raw data (5000)
#		; family of methods: first position after the 3 gives the following options
#		; setting:    0 1 2 3 4 5 6 7 8 9
#		;alPerimeter  + + + + - - - - - - select central area or alperimeter for bleach corr
#		;excludeStim  - + - + - + - + - - exclude stimulus time + 3 sec from bleach corr
#		;addNoise     - - + + - - + + - - add high frequency noise to bleach corr
#		; decimals and units give a radius in micrometers for correction of spread light
#		CalcSigAll3000,  method

#8000: BEGIN
#		CalcSigAll8000, method ;
#		;8000 is for multi-focal short ratio measurements, collapses to one depth taking the maximum
#  END
#9000: BEGIN
#		CalcSigAll9000, method ;
#		;9000 is for multi-focal short ratio measurements, collapses to one depth taking the mean
#  END
#10000: BEGIN
#		CalcSigAll10000, method ;10000 has the common blocks
#		;10000 is for multi-focal short ratio measurements, with 3D correction and many sub-options
#  END
    else: print('ViewCalcData.CalcDataMaster: flag.CalcMethod not implemented')
    return 



def CalcSigAll3000(p1, flag):
    #settings values
    FlagRatioSetting   = int(flag["LE_CalcMethod"] / 1000) # first digit. int is like floor
    RatioSetting 	= (FlagRatioSetting == 4)  # is this a FURA measurement?
    startbackground 		   = flag["LE_StartBackground"] # background ab frame ..-
    prestim_endbackground 	= flag["LE_PrestimEndBackground"] # background till n frames before stimulus
    subtractBeginning 		= (startbackground >= 0)


    #run CalcSigAll3000 for the single wavelength in p1.raw1
    p1, flag = CalcSigAll3000_raw(p1, flag) #run the full program on raw1
    # p1.sig is already the perfect calculation if not a ratio
    if RatioSetting: #fura measurement - so far we worked on raw1, i.e. 340
        # run the same thing for p1.raw2(380), therefore do some copying
        p2 = p1.copy() #make a flat copy into p2
        # raw1 is 340, raw2 is 380
        p2.raw1 = p2.raw2 #copy second wavelength into the first slot
        p2, flag = CalcSigAll3000_raw(p2, flag) #run the full program on raw2 (called raw1 here)
    # now calculate the ratio, put into p1.
    # 340/380 is p1/p2
    #but sig1 is deltaF/F, i.e. not F/F0, therefore add 1
        p1.sig1 = (p1.sig1 +1)/(p2.sig1 + 1) # times multiplyFactor for percentages, not defined in python
        #p1.raw1 = p2.raw1 #CalcSigAll3000 modifies raw1 also
        p1.metadata.bleachpar2 = p2.metadata.bleachpar #keep track of the bleach parameters
#	;since this was the ratio of the deltaF, we have to multiply with the inverse of the backframes to get the true ratio
#	;we did the delta F first because otherwise the log-bleach-correction would not work
        backBackFrame = p1.metadata.backframe/p2.metadata.backframe
        for i in range(p1.metadata.frames): #remove the effect of calculating F/F0
            p1.sig1[:,:,i] = p1.sig1[:,:,i]  * backBackFrame
        print('ViewCalcData/CalcSigAll3000: calculated ratio based on method 4xyy ',flag["LE_CalcMethod"])

#;subtract beginning
    if subtractBeginning:

        (startbackground, endbackground) = p1.metadata.background_frames

        backbackframe = np.mean(p1.sig1[:,:,startbackground:endbackground], axis=2) #takes the average for selected time frames
        for i in range(p1.metadata.frames):
            p1.sig1[:,:,i] -= backbackframe 
    return p1, flag # no need to return p1, since it is modified anyway



def CalcSigAll3000_raw(p1, flag):

#;method 4xyy, where x is the setting (see table below), and y is the radius for scatter correction
#3000 for deltaF, 4000 for Fura
#5000 for raw data

#
#;fixed settings: need to go into flags, all of them!
#
#lightThresholdFlag =0 ;not well tested yet, implemented for 3D-2photon.Nov 1007
#;switch OFF until exported to an external flag
#
    noiseseconds   	= 1 #; high frequency cutoff in seconds for lamp noise reduction, when set
#rawDataCopy    		= 0 ; puts raw data into odour set 0, if OFF puts deltaF/F of SLAVE into odour set 0
#;set rawDataCopy to 2 to put bleach corrected raw data into raw1
#;with new '5000' family of loading, do not use any more
#; calculate nr of last frame that will be used for background average
#multiplyfactor 		= 100.0   ; set to 100 to get percentage values
    lightmeanvalue	= 1000.0 #; raw data are first scaled to this mean light value
    cutedge 			= 0.2 #; border area not to be considered for bleach correction when not using area
    bleachmean 		= 0 #; use mean over time and frames as trace to do the bleach correction with; else median

    rawdatadelete	   = flag["VIEW_DeleteRawData"] != 0 # ; deletes raw data at the end, saves disk space
    logexcludeseconds = flag["LELog_ExcludeSeconds"] #]) ; how many seconds after stimulus onset to exclude, when set
    bleachstartframe 	= flag["LE_BleachStartFrame"] #] ); set to 2 to exclude 2 frames at the beginning from log-fit
# frames before bleachstartframe are ignored for bleach correction
    loginitialfactor  = flag["LELog_InitialFactor"]#] ) ; weight factor for curve stretch before stimulus onset
# frames after bleachstartframe and before stimulus-logexccludeseconds are valued with this weight

# for example: curve 5 Hz, 100 Frames long, odor at frame 21
# LogExcludeSeconds=5, BleachStartFrame=3, LogInitialFactor=2
# LogFitting will be made using frames 3:20 and 46:99, but 3:20 will count double
# prestim_endbackground 	(see below) is also used for bleach correction

#variable settings
    flagratiosetting   = int(flag["LE_CalcMethod"] / 1000) # first digit. int is like floor
    myMethod       = int(flag["LE_CalcMethod"] / 100) % 10 #second digit. contains settings for bleach correction
    alperimeter    = myMethod in [0,1,2,3]      #;for 0,1,2,3
    excludestimulus= myMethod in [1,3,5,7] # for 1,3,5,7 (,9)
    addnoise       = myMethod in [2,3,6,7] # for 2,3,6,7
    nobleach       = myMethod in [9]
    airbleach      = myMethod in [8]
#AirBleachAddNoise = 0 ; local setting  - option not implemented yet
#;IF AirBleach THEN alPerimeter = 1 ;use this line for bleach in AL perimeter only

#; setting:    0 1 2 3 4 5 6 7 8 9
#;alPerimeter  + + + + - - - - C - ; with 8 bleaching is in coordinates only (variable: CoorPerimeter = AirBleach)
#;excludeStim  - + - + - + - + - -
#;addNoise     - - + + - - + + - -
#;no bleach    - - - - - - - - - +
#;air bleach   - - - - - - - - + - ;correct with bleach parameters taken from air trial

#;ratiosetting of 3: deltaF/F
#;ratiosetting of 4: make ratio of odor buffer 0 / buffer1
#    ratiosetting 	= (FlagRatioSetting == 4) #not used because the fura is controlled from outside
    # in here, I only work on the main data raw1.
    returnrawdata 	= (flagratiosetting == 5)
    #returnrawdata returns the bleach corrected data to raw1

#external settings
    shrinkfactor 	= flag["LE_ShrinkFaktor"]
#Memory_3Dim				= fix(flag[VIEW_No4Darray]) ; use arrays with only one odor-buffer to save space
    startbackground 		= max(flag["LE_StartBackground"],0) # background ab frame ..- at least 0
#    subtractbeginning 	= (startbackground >= 0)
    prestim_endbackground 	= flag["LE_PrestimEndBackground"] # background till n frames before stimulus
#firstOdor 				= fix(flag[LE_FirstBuffer])
#   radius 					= flag.RM_Radius # necessary for coordinate analysis
# the next lines not translated to Python, because they relate to the way the data was put into the sig variable
# if RatioSetting 		THEN 	firstOdor = 0 ; 0 contains master
#if (firstOdor eq -1) 	then begin ;settings as befor the introduction of LE_usefirstbuffer
#	IF (total(raw1(*,*,*,0)) eq 0) then firstOdor = 1 ELSE firstodor = 0
#endIF

    (startbackground, endbackground) = p1.metadata.background_frames


#SETTING should I do unsharpmask?
    smoothvalue  = int(flag["LE_CalcMethod"] % 100) # last two digits, radius of filter in um
    unsharpmask  = smoothvalue > 0

    if airbleach:
        print('ViewCalcData.CalcSigAll3000: airBleach not implemented yet in Python')
#	IF RatioSetting Then Begin
#		airBleach = 0
#		print, 'CalcSigAll3000: AirBleach not implemented with Ratio dyes'
#	endIF
#	IF (firstOdor gt 0) Then Begin
#		;airBleach = 0
#		firstodor = 0
#		print, 'CalcSigAll3000: using AirBleach with flag[LE_FirstBuffer] greater 0 (???)'
#	endIF
#	IF (total(raw1(*,*,*,0)) eq 0) then begin
#		airBleach = 0
#		firstodor = 1
#		print, 'CalcSigAll3000: AirBleach not useful without data in buffer 0 (air is missing)'
#	endIF
#	IF AirBleachAddNoise THEN begin
#		print, '************CalcSigAll3000 - local flag set to addNoise with AirBleachAddNoise'
#		addNoise = 1
#	endIF

#loadct, SO_MV_colortable



#
#;define variables
#sig1 = fltarr(p1.format_x, p1.format_y, p1.frames, p1.odors+1)
#backframe        = fltarr(p1.format_x, p1.format_y)
# Python: will use p1.sig1 and p1.backframe

###### start calculation: create maskframe, either via alperimeter, or via cutedge
    if alperimeter:
#	;get selected AL area
#        if flag.RM_differentViews > 0: #not implemented for now - 
#   		;special section Tilman
#    		;areaFileName = flag[stg_OdorMaskPath]+strmid(Flag[stg_ReportTag],0,14)+p1.viewLabel+' '+strmid(Flag[stg_ReportTag],14)+'.area'
#    		;print, 'CalcSigAll3000: special Tilman section for area file!!'
#    	;standard section
#            areafilename = flag.STG_OdormaskPath+flag.STG_ReportTag+str(p1.viewLabel)+'.Area'
#        else:
#         maskframe = IDL.restore_maskframe(flag) #restores maskframe from file
        try:
            area_filename = flag.get_existing_area_filepath()

        except FileNotFoundError as fnfe:
            maskframe = np.ones((p1.metadata.format_x, p1.metadata.format_y))
        else:
            maskframe = read_area_file(area_filename)

#	;now AL perimeter is in variable maskframe
        #apply shrinkfactor
        if (shrinkfactor not in [0,1]): #both 0 and 1 mean 'no shrink'
            # copy from ViewLoadData.loadTILL
            shrink = 1/shrinkfactor # flag of 2 means half the size in each dimension
            import scipy.ndimage as scind
        # the command used in IDL for shrink was REBIN
        #raw1(*,*,i,1) = rebin(image(0:p1.format_x*shrinkFactor-1, 0:p1.format_y*shrinkFactor-1) ,p1.format_x, p1.format_y) ;
        # the following shrinks in x and y, not in t, with polinomial order 1. 
        # "nearest" is for treatment at the borders
            maskframe = scind.zoom(maskframe,(shrink,shrink), mode='nearest')
          
        #check for consistent size,
#	;safety check for unequal size
#	;remove last row(s)/column(s) in case of original size incompatible with shrink factor
#	;e.g. shrinkfactor 2 with format_x 173, limit mask to 0..172
#	maskFrame = maskFrame(0:p1.format_x*shrinkfactor-1,0:p1.format_y*shrinkfactor-1 )
#	;resize maskFrame considering shrinkfactor
#	maskSize = size(maskFrame)
#	maskFrame = rebin(maskFrame,maskSize[1]/shrinkfactor,maskSize[2]/shrinkfactor)
#	maskSize = size(maskFrame)
        if (maskframe.shape != (p1.metadata.format_x,p1.metadata.format_y)): # not correct size
            print('ViewCalcData.Calcsigall3000: AREA file has wrong size - maybe make with binning unequal 1?')
            return #jump out of the program
    else: # there is no alPerimeter, i.e. no .Area file
#	;select central region of AL for correction
        maskframe = np.zeros((p1.metadata.format_x, p1.metadata.format_y), dtype=int)
        maskframe[round(p1.metadata.format_x*cutedge):round(p1.metadata.format_x*(1-cutedge)),round(p1.metadata.format_y*cutedge):round(p1.metadata.format_y*(1-cutedge))]=1
#	maskFrame[p1.format_x*CutEdge:p1.format_x*(1-CutEdge),p1.format_y*CutEdge:p1.format_y*(1-CutEdge)]=1
#	;now AL perimeter is in variable maskframe
        print('CalcSigAll3000 - reference area for F and for Bleach is centre with edges cut at ',cutedge)

#########  CoorPerimeter #################
# the following CoorPerimeter section appears not in use - not translated to python yet
# I only found the flag in AirBleach.
# The idea is: get the bleach function only from within the coordinates of .coor
# easy to add if needed
#;CoorPerimeter
#;If CoorPerimeter is set, select the area delimited by coordinates for bleach correction maskframe
#;section above becomes obsolete, because maskframe is overwritten
#IF CoorPerimeter THEN begin
#	print, 'Using coordinates for bleach control (calcsigall3000)'
#	;load coordinates
#	;get file name of coordinate file (.coor)
#	;Get Information about odours from external file
#	   	IF fix(flag[RM_differentViews]) THEN begin
#    			GlomeruliListFile =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.viewLabel+'.coor'
#    		endIF else begin
#    			GlomeruliListFile =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.coor'
#    	endELSE
#     		;reportFile = flag[stg_OdorReportPath]+flag[stg_ReportTag]+'.expGlo'
#	   	shiftMaskeX = p1.shiftX
#	   	shiftMaskeY = p1.shiftY
#	;empty maskframe
#	maskFrame = bytarr(p1.format_x, p1.format_y)
#   	;read coordinates
#    readListe, GlomeruliNum, liste, GlomeruliListFile, column4=separateLayers
#   	glomerulinum = fix(glomerulinum)
#   	;got the liste of coordinates & identities
#    ;shiftMaskeX, shiftMaskeY
#   	liste(0,*) = liste(0,*) + shiftMaskeX
#   	liste(1,*) = liste(1,*) + shiftMaskeY
#    ;consider shrinkfactor
#    IF (shrinkFactor gt 1) then begin
#			liste(0,*) = liste(0,*)/shrinkFactor
#			liste(1,*) = liste(1,*)/shrinkFactor
#    endIF
#    ;now get infos about each coordinate
#	for glo=0, GlomeruliNum-1 do begin
#					x = liste(0,glo)
#			    	y = liste(1,glo)
#			    	xborders = [x-radius,x+radius]
#			    	IF ((xborders(0) lt 0) OR (xborders(1) gt (p1.format_x-1))) THEN begin
#			    		xborders = (xborders > 0 ) < (p1.format_x-1)
#			    		print, 'x coordinates clipped: ',x, xborders,' in glo ',glo
#			    	ENDif
#			    	yborders = [y-radius,y+radius]
#			    	IF ((yborders(0) lt 0) OR (yborders(1) gt (p1.format_y-1))) THEN begin
#			    		yborders = (yborders > 0 ) < (p1.format_y-1)
#			    		print, 'y coordinates clipped: ',y, yborders,' in glo ',glo
#			    	ENDif
#			    ;now set this area to 1 in maskFrame
#				maskFrame(xborders(0):xborders(1),yborders(0):yborders(1))=1
#		endfor
#endIF ;CoorPerimeter

#positions = where(maskframe)
#;positions contains the pixels to be considered for bleach correction
# in python, do not use np.multiply(raw1,maskframe) 

#dividend   = endbackground-startbackground+1     ;find how many frames for F
#there are no multiple odors in Python, but there may be raw1 and raw2
#         
#;first run through data for light scattering correction, and setting mean to 10000
#for od = firstOdor, p1.odors  do begin
#
#	;calculate F (float)
#    backframe  = total(raw1(*,*,startbackground:endbackground,od),3,/DOUBLE) ;makes a sum of the third dimension (frames)
#	backframe  = float(backframe) / dividend
############### background frame, corresponds to F0

    p1.metadata.backframe = np.mean(p1.raw1[:,:,startbackground:endbackground], axis=2)
    print('ViewCalcData/CalcSigAll3000_raw: background start/stop is frame: ',startbackground, endbackground)
    #takes the average for selected time frames
    
#;calculate intensity correction, only within maskframe
#    backvalue = np.mean(np.multiply(p1.backframe,maskframe))
    backvalue = np.mean(p1.metadata.backframe[maskframe != 0])
#	backValue  = mean(backframe(positions), /double) ; average light values in the backframe area
    if (backvalue == 0): backvalue = 1 #safety net to avoid dividing by 0
    backfactor = lightmeanvalue/backvalue
# apply backFactor outside loop
    p1.sig1 = p1.raw1 * backfactor
########### now sig1 was created, as light intensity corrected copy of raw1
    #       so from now on work on sig1
    
#            buffer[:,:,i] = sci.gaussian_filter(buffer[:,:,i], filterSpaceSize)
#scipy.ndimage.filters.gaussian_filter(input, sigma, order=0, output=None, mode='reflect', cval=0.0, truncate=4.0)

#	; correct data for scattered light
    if unsharpmask: #light scatter correction
        smoothfactor	= flag["VIEW_ScatterLightFactor"]
        # adjust for pixel size - since smoothvalue is given in um
        smX 		= smoothvalue / p1.metadata.pixelsizex
        smY 		= smoothvalue / p1.metadata.pixelsizey
        smoothvalue = (smX+smY)/2.0
        if (smX != smY): print('unequal pixel size not implemented yet - averaging x and y value')
        print('Scattered light correction with ',smoothvalue, ' pixels for ',p1.metadata.pixelsizex*smoothvalue,' microns. Factor:', smoothfactor)
        print('CalcSigAll3000: a negative factor means scattered light correction, a positive factor a spatial high-pass filter')

        for i in range(0,p1.sig1.shape[2]): # go through frames
            # copy a frame, smooth it, copy back
            oneframe = p1.sig1[:,:,i]
#	for i= 0, p1.frames-1 do begin ;correct data first, write corrected data into final dest
#		;dark-frame correction # dark frame deprecated
#		oneFrame = float(raw1(*,*,i,od) - dark1)
#		;intensity correction # done outside the frame loop
#		oneFrame = oneFrame * backFactor
#		;light scatter correction
#		IF unsharpMask THEN begin
            if smoothfactor > 0:
#			IF (SmoothFactor gt 0) THEN begin
#				oneFrame = oneFrame + SmoothFactor*(oneFrame - smooth(oneFrame, smoothValue, /EDGE_TRUNCATE))
                #I use sci.gaussian_filter for the IDL smooth command
                #mode='nearest' extends the last value as a constant
                oneframe = oneframe + smoothfactor*(oneframe - sci.gaussian_filter(oneframe, smoothvalue, mode='nearest'))
#			endIF
            if smoothfactor < 0:
#			IF (SmoothFactor lt 0) THEN begin
#			;correction Jan 05: the upper line amplifies noise - in fact, rather than a scattered light correction
#			;it is a spatial high-pass filter!
#			;the next line smooths the unsharp image
#			;for backward compatibility, this has to be indicated by a NEGATIVE smoothFactor
#				oneFrame = oneFrame - SmoothFactor*smooth((oneFrame - smooth(oneFrame, smoothValue, /EDGE_TRUNCATE)),smoothvalue, /edge_truncate)
                oneframe = oneframe - smoothfactor*sci.gaussian_filter((oneframe - sci.gaussian_filter(oneframe, smoothvalue, mode='nearest')), smoothvalue, mode='nearest')
#			endIF
#		endIF
#		;write corrected data temp. into sig1
#		sig1(*,*,i, od) = oneFrame
            p1.sig1[:,:,i] = oneframe
#	endFOR
#endfor   ; odornr

#;sig1 now contains the scatter-light corrected raw data, with mean at lightmeanvalue
            # copy into raw1, or delete raw1
    if rawdatadelete:
        p1.raw1 = 0 #save memory space
    else:
        p1.raw1 = p1.sig1.copy() # raw now contains scatter corrected "raw" data
#IF rawDataDelete then begin
#	Raw1 = 0
#	print, 'CalcSigAll3000: raw data deleted'
#endIF else begin
#	;copy back into raw
#	raw1 = sig1  #why back into raw?
#endELSE
    

#;make a copy of this corrected data into the experimental foto
#;only if the foto does not yet exist or is empty
    if not hasattr(p1, "foto1"):
        p1.foto1 = np.mean(p1.sig1[:, :, startbackground :endbackground], axis=2)
    elif np.all(p1.foto1 == 0):
        p1.foto1 = np.mean(p1.sig1[:, :, startbackground :endbackground], axis=2)


## lightThresholdFlag apparently was not implemented yet well
#IF (lightThresholdFlag eq 1) then begin
#	;apply light threshold to data
#	;that is: where there is no dye, there cannot be a signal
#	;threshold calculated from foto
#	lightThreshold = 800
#	sig1 = sig1 > lightThreshold
#endIF ;flag



#;calculate deltaF for each buffer
    p1.sig1 = calc_deltaF(p1.sig1, refRange=[startbackground, endbackground])


#;run through deltaF data, bleach and noise correction for each 'odour', i.e. wavelength separately
    if nobleach:
        print('No logarighmic bleach correction in CalcSigAll3000')
    else:
#$
#	;bleach correction!
#	;necessary data structures
#	;excluded frames at the beginning are defined in fitlogdecay
#	correctArray    = fltarr(p1.frames)
#	AllcorrectArray = fltarr(p1.odors+1,p1.frames)
#	AllOdourArray   = fltarr(p1.odors+1,p1.frames)

#calculate correctarray as mean or median
    #convert flag
# - limit this to the mask
#        if bleachmean == 1:
#            correctarray = np.mean(p1.sig1, axis=(0,1))
#        else:
#            correctarray = np.median(p1.sig1, axis=(0,1))
        #not good in terms of syntax
        correctarray = np.zeros(p1.metadata.frames)
        positions = maskframe != 0
        if bleachmean == 1:
            for i in range(p1.metadata.frames):
                correctarray[i] = np.mean(p1.sig1[:,:,i][positions])
        else:
            for i in range(p1.metadata.frames):
                correctarray[i] = np.median(p1.sig1[:,:,i][positions])



##############NOW WORK ON THE BLEACH CORRECTION; that is: calculate the weight array.

        weights = get_bleach_weights(flags=flag, p1_metadata=p1_metadata, exclude_stimulus=excludestimulus)
############
        print(weights)
        print(prestim_endbackground, logexcludeseconds, p1.metadata.frequency, stimulus_on, loginitialfactor, bleachstartframe)
        if airbleach:
            print('CalcSigAll3000: ********* AirBleach not implemented in Python yet')
#				;calculate log function only for AIR
#				IF (od eq 0) THEN fitlogdecay, correctArray, Airdetract, weights
#				detract = Airdetract
#				print, 'LogBleach done on reference measurement!'
        else:
            measurement_label = flag.get_default_measurement_label()
            (detract, opt_parms) = fitlogdecay(correctarray, weights, not flag["VIEW_batchmode"], measurement_label)
            p1.metadata.bleachpar = opt_parms
            print('CalcSigAll3000: Logbleach correction done')
#IDL: pro FitLogDecay, lineIn, fittedOut, weights, verbose ;, noConverge

        if addnoise:
#			;now add high frequency noise (lamp noise) to the fitted exponential
#            dummy = detract[0:BleachStartFrame] #;do not smooth before bleachStartFrame
# $$ implement smooth in the next line, defined above
#            detract = detract + correctarray - smooth(correctarray, p1.frequency*noiseSeconds)
#$$ or gaussian filter buffer[:,:,i] = sci.gaussian_filter(buffer[:,:,i], filterSpaceSize)
            detract = detract + correctarray - sci.gaussian_filter(correctarray, p1.metadata.frequency*noiseseconds)
            print('CalcSigAll3000: addnoise done')
#            detract[0:BleachStartFrame] = dummy[:]

#		;subtract these values
        for i in range(p1.metadata.frames):
            p1.sig1[:,:,i] -= detract[i]

#		;MONITOR the action taken
#		allcorrectArray(od,*)=detract(*) ;this is just for plotting the monitor
#		allOdourArray(od,*)  =correctArray(*) ;this is just for plotting the monitor

##;calculate bleach corrected raw data and put it into raw
            # discontinued, because implemented in 5000 family with returnrawdata
#        if (rawdatacopy == 2):
#            for i in range(p1.frames-1):
##		raw1(*,*,i,*) = (sig1(*,*,i,*) * backFrame(*,*,*))/multiplyfactor ;raw data
#                p1.raw1[:,:,i] = (p1.sig1[:,:,i] * p1.backframe[:,:])/multiplyfactor #
#                # this inverts the deltaF/F ;raw data
##	endFor
        print('CalcSigAll3000: bleach corrected deltaF data in sig1')
#;calculate bleach corrected raw data and put it into sig
        if returnrawdata:# setting is 5000
            for i in range(p1.metadata.frames): # do begin
                # do the inverse of deltaF/F
                p1.raw1[:,:,i] = ((p1.sig1[:,:,i]+1) * p1.metadata.backframe) # /multiplyfactor# ;raw data
            #this only works because backframe uses the same frames as deltaF/F
            print('CalcSigAll3000: bleach corrected raw data calculated')
#        else: #endIF ELSE begin
#  ;shift back to mean value of MultiplyFactor
#  ;'temporary' saves memory space
#            p1.sig1 += multiplyfactor
#            print('CalcSigAll3000: check this line - why would MultiplyFactor be added??')

# in python, plot the curves not implemented (yet?)
#  ;plot the curves used in log-correction
#
#	window, 16, xsize=512, ysize=512
#	minplot = floor(min([allcorrectarray(firstodor:p1.odors,*),allodourarray(firstodor:p1.odors,*)]))
#	maxplot = ceil(max([allcorrectarray(firstodor:p1.odors,*),allodourarray(firstodor:p1.odors,*)]))
#	;minplot = 98.0
#	;maxplot = 102.0
#	plot, correctarray(*), yrange=[minplot,maxplot], color=245, thick=3, ystyle=1, /nodata
#	;plot weight values as curve and bottom line
#	oplot, minplot+weights(*), thick=2, color=255 & correctarray(*)=minplot & oplot, correctarray(*), thick=1, color=255
#	;plot log fits
#	for od = firstOdor, p1.odors  do begin
#		oplot, allcorrectArray(od,*), thick=3, color=240-30*od
#		oplot, allOdourArray(od,*), thick=1,  color=240-30*od
#	end
#	;plot stimulus bar
#	xaxis     = FINDgen(p1.frames)
#	stimlow   = fltarr(p1.frames)
#	stimlow(*)= minplot
#	oplot, xaxis(p1.stimulus_on:p1.stimulus_end), stimlow, thick=5, color = 245
#	;second stimulus; if no second stimulus is given, this should be from 0 to 0
#	IF ((p1.stim2on gt 0) AND (p1.stim2off gt 0) AND (p1.stim2on lt p1.frames-1) AND (p1.stim2on  lt p1.frames-1)) THEN begin
#		oplot, xaxis(p1.stim2on:p1.stim2off), stimlow, thick=5, color = 245
#	endIF

#endELSE;nobleach
    return p1, flag #  no return, p1 is modified already. Try return instead now (8/19)


def calc_deltaF(imgData, refRange):
    '''    
    Input: 3D matrix x,y,t, refRange
    calculates a crude deltaF.
    F0 is the entire movie (default), or the interval refRange (e.g. [14,21])
    :param refRange: list of length 2, frame numbers (indices) of the starting and ending frame of the range to use for
    baseline fluorescence calculation. Note that the ending frame is included in baseline calculation.
    '''

    referenceF = np.mean(imgData[:, :, refRange[0]: refRange[1] + 1], axis=2)

    dead_mask = referenceF == 0
    if np.any(dead_mask):
        # keep pixels that averages 0 over the reference range unmodified. these are most likely pixels dead at 0.
        referenceF[dead_mask] = 1

        logging.getLogger("VIEW").warning("F0 for some pixels were 0, not normalizing these pixels!")

    # convert to txy because framewise division is easier
    imgData_txy = np.moveaxis(imgData, source=-1, destination=0)

    deltaFdata_txy = (imgData_txy / referenceF) - 1

    # convert back
    deltaFdata = np.moveaxis(deltaFdata_txy, source=0, destination=-1)

    logging.getLogger("VIEW").info(
        f"Baseline fluorescence was calculated by averaging frames numbered {refRange[0]}-{refRange[1]}")

    return deltaFdata


def CalcSigAll0(p1, flag):
#pro CalcSigAll3, raw, dark, p, absolute_values
#; Procedure not to calculate any signals
#; Author: Giovanni, Jasdan
#;parameters: (from loadexp.pro)
#; raw        : 4 dimensional array (x,y,frames,odors)
#;              odor=0:   background/air
#;              odor=1... odors from experiment
#; dark       : darkframe of ccd camera
#; p          : parameterset
#;results:
#;relative_changes : 4 dimensional float array with signals for all odor and background
#absolute_values  = fltarr(p.format_x, p.format_y, p.frames, p.odors+1)
#backframe        = fltarr(p.format_x, p.format_y)
#for odor = 0, p.odors  do begin
#	backframe(*) = float(dark)
#	for i= 0, p.frames-1 do begin
#   	  absolute_values(*,*,i, odor) = raw(*,*,i,odor) - backframe(*,*)
#	endfor
#endfor   ; odornr
#absolute_values = absolute_values  / 1000
    
    p1.sig1 = p1.raw1.astype(float) / 1000
    print('ViewCalcData/CalcSigAll0: Signals calculated (method 0). sig1 = raw1/1000')
#end ; of program
    return p1


def CalcSigAll1(p1, flag):
    # pro CalcSigAll3, raw, dark, p, absolute_values
    # ; Procedure not to calculate any signals
    # ; Author: Giovanni, Jasdan
    # ;parameters: (from loadexp.pro)
    # ; raw        : 4 dimensional array (x,y,frames,odors)
    # ;              odor=0:   background/air
    # ;              odor=1... odors from experiment
    # ; dark       : darkframe of ccd camera
    # ; p          : parameterset
    # ;results:
    # ;relative_changes : 4 dimensional float array with signals for all odor and background
    # absolute_values  = fltarr(p.format_x, p.format_y, p.frames, p.odors+1)
    # backframe        = fltarr(p.format_x, p.format_y)
    # for odor = 0, p.odors  do begin
    #	backframe(*) = float(dark)
    #	for i= 0, p.frames-1 do begin
    #   	  absolute_values(*,*,i, odor) = raw(*,*,i,odor) - backframe(*,*)
    #	endfor
    # endfor   ; odornr
    # absolute_values = absolute_values  / 1000

    p1.sig1 = p1.raw2.astype(float) / 1000
    print('ViewCalcData/CalcSigAll1: Signals calculated (method 0). sig1 = raw2/1000')
    # end ; of program
    return p1


def CalcSigAll3(p1, flag):
    '''
    Calculate deltaF, with no thrills at all
    in IDL, this was ???
    '''

    p1.sig1 = calc_deltaF(p1.raw1, refRange=p1.metadata.background_frames)

    logging.getLogger("VIEW").info(
        f'CalcSigAll3: delta F with background: {p1.metadata.background_frames}')
    return p1


def CalcSigAll4(p1, flag):
    '''
    Calculate the ratio, with no thrills at all
    in IDL, this was CalcSigAll15
    '''
#pro CalcSigAll15, raw, relative_changes
#deleteRaw = 1
#multiplyFactor = 100 ; factor to multiply data with when making ratio
#relative_changes = raw
#IF deleteRAW then raw = 0
#relative_changes = float(relative_changes)
#;calculate RATIOS
#relative_changes(*,*,*, 1) = (multiplyFactor*relative_changes(*,*,*, 0)) / relative_changes(*,*,*, 1)
#relative_changes(*,*,*, 0) = 0 ;delete buffer 0
#print, 'plain ratios in buffer 1'
#end ; of program
    p1.sig1 = p1.raw1 / p1.raw2
    print('ViewCalcData/CalcSigAll4: Signals calculated (method 4). Fura, no thrills')
    return p1


