# -*- coding: utf-8 -*-
"""
Created on Fri Sep 14 15:55:02 2018

@author: Giovanni Galizia

collects all IDL programs that were in the folder ViewOverview

"""

# solution from https://stackoverflow.com/a/49480246
if __package__ is None or __package__ == '':  # if Master_Hannah2018.py is importing this file
    import IDL, View_gr_reports, ImageALlocal, View
else:  # if we are importing this file from a package, e.g., using view.idl_translation_core.ViewOverview
    from . import IDL, View_gr_reports, ImageALlocal, View

import matplotlib as mpl
mpl.use("Qt5Agg")

import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage as sci
import os
import pandas as pd

from moviepy.editor import VideoClip
from moviepy.video.io.bindings import mplfig_to_npimage


#from PIL import Image
#from PIL import ImageDraw
import PIL as PIL


from inspect import currentframe

def get_linenumber():
    cf = currentframe()
    return cf.f_back.f_lineno
# I use this because singleOverviews is so convoluted, that the user should know where a message is from
# print "This is line 7, python says line ", get_linenumber()

def save_movie_file_xyt(dataMtrx, fps=24, bitrate="256k", movie_filename=''):
    # dataMtrx has shape x,y,t
    #start = log("save_movie_file_test2")
    zlen = dataMtrx.shape[2]
    # scale matrix to min, max
    scaleMin = dataMtrx.min()
    scaleMax = dataMtrx.max()
    duration = (zlen-1)/fps #frames/fps
    fig = plt.figure()
    ax = fig.add_subplot(111)
    fig.tight_layout(pad=1.0)
    dataMtrx_corrected = dataMtrx.swapaxes(0, 1)
    def make_frame(t):
        #gives frame at time t
        ax.clear() #without this, it is very slow
        ax.axis('off')
        ax.set_title("Frame " + str(int(zlen/duration*t)) + "/" + str(zlen))
        ax.imshow(dataMtrx_corrected[:,:,int(zlen/duration*t)], clim=(scaleMin, scaleMax))
        #fig.colorbar()
        return mplfig_to_npimage(fig)
    animation = VideoClip(make_frame, duration=duration)
    # export as a video file
    # animation.write_gif(movie_filename+'.gif', fps=fps) #gif is larger
    animation.write_videofile(movie_filename, fps=fps, bitrate=bitrate)
    plt.close()
#    endlog(start, "save_movie_file_xyt")



def singleoverviews(flags_input,p1):
    '''
    try to translate singleoverviews from IDL in a litteral way
    one major change: IDL data format has multiple odors, python version uses only p1.sig1
    I'll try and keep the 8-bit graphic logic of IDL, 
    and will write a separate, new graphic output routine later, once I know python better
    for readability, some IDL commands are kept, but not all, check file singleoverviews.pro
    '''    
#  common localSingleOverviews, NextPosition ; local variable to remember last position
#;Settings
#PY: translate variables only if I use them - or translate them all, this need to be rewritten anyway
#;CAREFUL - some settings are external flags
#;some are hardwired in this program
#
    print('ViewOverview.singleoverviews starting now')
    
    #test this:
# there was a flag for flag.RM_NextPosition that is used to keep the position across iterations
# does it work if I just define the variable outside, here?
# bypassing the flag system?
    
#singleoverviews is written for flags as series
    if  isinstance(flags_input, pd.Series):
        flag = flags_input
    else:
        flag = flags_input.to_series()

    flag_RM_nextposition = flag.RM_NextPosition # (0,0)
#    answer: no, it does not work 
    
    localVIEW_batchmode   = flag.VIEW_batchmode # ? I keep it to translate literally, as fixed variable for now
    withinarea       = flag.SO_withinArea#  limit false-color output to within mask defined in .area file
    method           = flag.SO_Method #
    submethod        = flag.CTV_Method
    individualscale     = flag.SO_individualScale
#IF not localBatchMode THEN print,'indiScale ', individualscale, ', method: ', method, ', CTV: ',subMethod
    centerimage2zero   = individualscale // 10 #all values up to 9 do not center scale image
    individualscale       = individualscale % 10
    percentilescale     = 0
    indiscale3factor    = 0.2 #; set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
    if ((individualscale > 100) and (individualscale < 200)):# then begin
        indiscale3factor = (individualscale-100)/100.0 #; set to 0.2 (i.e. 120 for individualscale) for 20 % border to be ignored when scaling usind idividualscale eq 3
        individualscale = 3
#endIF
    if ((individualscale > 1000) and (individualscale < 2000)):# then begin
        percentilevalue = (individualscale % 100)/100.0
        percentilescale = 1
        individualscale = (individualscale % 1000) // 100 
        #; 1xyy, x gives individualscale
        indiscale3factor= 0.2 #; set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
#endIF
    newcolumn          = flag.RM_NewColumn # temporary: standard to 1 for old setup
#setup           = fix(flag[LE_loadExp])
    markcoordinates     = flag.RM_FotoOk  #]) ;if set, includes a black square at the glomeruli chosen
#                              ;if set to 2, includes the TIFF file xxx.tiff
#                              ;3 for both 1 and 2
#                              ;4 for 1 filled with glomerulus value
#                              ;5 for show perimeter
    shrinkfactor      = flag.LE_ShrinkFaktor
    #separateLayers      = fix(flag[RM_separateLayers])  ;if set, gives the coordinates only in the correct layer specified in the list
#
    annotatefactor      = 100 #; factor to multiply minimum and maximum with when annotating
#markBorder         = 1 ; marks the border of each overview in fixed color, set to 0 for 13
#flipSides          = fix(flag[RM_differentViews])
#           ; if 0 then no flipSides, if above 0 gives the position within p1.viewLabel which shows the side
#          ; for example, if p1.viewLable is 'BR' and flipSides is '2', 'R' is extracted and the image is flipped
#          ; (R indicating right AL, and therefore the need to swap sides)
#          ; In these instances, the frame around the images is colour coding the sides too.
#          ; swapping up/down for sideway ALs, use 'D' (derecha) as a code
    border           = 10    #       ; border to leave in exportTIFFcanvas
    drawscalebar      = flag.CTV_scalebar#])
    unsharpmaskfilter   = flag.RM_unsharpmask #
    unsharpmasksize     = 20   #;fix(flag[RM_PrintAscii])
    unsharpmasksize2    = 10
#
#;morphoThreshold Flags now in its own routine
    #default: everything off
    
    
#
#;controls for FlipSide:
    flipframe        = 0 #; default value
#PY: flipSides not implemented
#IF flipSides gt 0 then begin
#    IF ((strmid(p1.viewLabel,flipSides-1,1) eq 'R') or (strmid(p1.viewLabel,flipSides-1,1) eq 'r')) THEN begin ;rignt side, flip sides
#       flipFrame = 1
#    endIF
#    IF ((strmid(p1.viewLabel,flipSides-1,1) eq 'D') or (strmid(p1.viewLabel,flipSides-1,1) eq 'd')) THEN begin ;rignt side, flip sides
#       flipFrame = 2
#    endIF
#endIF
#
    
##PY: font control not set
#;font control
#!P.FONT=1
#DEVICE, SET_FONT='Helvetica', /TT_FONT, SET_CHARACTER_SIZE=[8,8]
#
    exportTIFFcanvas = 0
    markborder       = 0
    flipsides        = 0
    exportTIFFframe  = 0

    if localVIEW_batchmode:# THEN begin
        if flag.VIEW_ReportMethod == 10: 
            exportTIFFcanvas = 1
#       exportTIFFcanvas = 1
#    endIF
        elif (flag.VIEW_ReportMethod in [13,20]): 
            exportTIFFcanvas = 2
            markborder       = 0
#    IF ((fix(flag[VIEW_ReportMethod]) eq 13) or (fix(flag[VIEW_ReportMethod]) eq 20)) THEN begin
#       exportTIFFcanvas = 2
#       markBorder = 0
#    endIF
        elif (flag.VIEW_ReportMethod in [14]): 
            exportTIFFcanvas = 3
            markborder       = 0
            flipsides        = 0
#    IF fix(flag[VIEW_ReportMethod]) eq 14 THEN begin
#       exportTIFFcanvas = 3
#       markBorder = 0
#       flipsides = 0
#    endIF
        elif (flag.VIEW_ReportMethod in [15]): 
            exportTIFFcanvas = 0
            markborder       = 0
            flipsides        = 0
            exportTIFFframe  = 1
#    IF fix(flag[VIEW_ReportMethod]) eq 15 THEN begin
#       exportTIFFcanvas = 0
#       markBorder = 0
#       flipsides = 0
#       exportTIFFframe  = 1
#    endIF
        elif (flag.VIEW_ReportMethod in [21]): 
            exportTIFFcanvas = 4
############# this is treated as exportTIFFcanvas 1 for now. check singleoverviews.pro if this turns out to be a problem
#    IF fix(flag[VIEW_ReportMethod]) eq 21 THEN begin
#       exportTIFFcanvas = 4
#    endIF
#endIF
#
#
#
    if unsharpmaskfilter: 
        print('*********  Using unsharp mask in SingleOverviews!! ***********************************************')
        print('not advised - I need to check the maths, because high frequency noise is deleterious')
#
    radius = flag.RM_Radius
#
#
#IF fix(flag[trueColour]) THEN begin
#    if fix(flag[macSystem]) THEN device, /true_color
#    device, decomposed=0
#endIF
#
#; use values from control window
    startframe  = flag.CTV_firstframe #in IDL, this was flag.CTV_firstframe only (without CTV)
    endframe    = flag.CTV_lastframe  #in IDL, this was flag.flastframe only (without CTV)
    maximum     = flag.SO_MV_scalemax
    minimum     = flag.SO_MV_scalemin
#
    zoomfactor  = 1
#
    ############# maybe here variables are over ############   
#    frame = np.zeros([p1.format_x, p1.format_y])
#frame(*,*) = -1000  ; borders are black; find other solution in python
#
    ###PY: there is only one buffer. 
#lastbuffer  = p1.odors
#;display 'first buffer' or not?
#firstBuffer = fix(flag[LE_UseFirstBuffer])
#IF (firstBuffer lt 0) THEN begin ; guess whether to use the first buffer on the basis of the setup
#    ;IF correctFlag eq 0 THEN firstbuffer = 1 ELSE firstBuffer = 0
#    IF setup eq 0 THEN firstBuffer = 0 ; for old setup, show also air control
#    IF setup eq 3 THEN firstBuffer = 1 ; for TILL, do not show AIR control
#    IF setup eq 4 THEN firstBuffer = 1 ; for TILL, do not show AIR control
#    IF (fix(flag[VIEW_ReportMethod]) eq 20) THEN firstBuffer = 1
#    IF (fix(flag[VIEW_ReportMethod]) eq 20) THEN lastBuffer = 1
#    ; if air was subtracted for correction then leave air overview away - it is 0 !
#    ;this is not really appropriate when using corrected dataset - just used for backwards compatibility
#    if (max(sig1(*,*,0,0)) eq 0) and (min(sig1(*,*,0,0)) eq 0) then firstbuffer = 1
#endIF
#numOdours =  lastbuffer - firstBuffer + 1
#
#min1 = fltARR(2)
#max1 = fltARR(2)
#;minimum =  10000
#;maximum = -10000
# PY I skip individualscale 2, since that is for several odors
#if (individualScale eq 2) then begin ;scale to min/max of all frames, takes more time
#    for odor = firstbuffer, lastbuffer do begin
#        overviewframe = overview( odor, method )
#        min1(0) = min(overviewframe)
#        max1(0) = max(overviewframe)
#        minimum = min(min1)
#        maximum = max(max1)
#        min1(1) = minimum
#        max1(1) = maximum
#    endFor
#endif
#
    if (individualscale == 0):  scalestring = ' ' + str(flag.SO_MV_scalemin) + '/' + str(flag.SO_MV_scalemax) +' '
    elif individualscale == 1: scalestring = ' indSc '
    elif individualscale == 2: scalestring = ' ' + str(minimum) + '/' + str(maximum) +' '
    elif individualscale == 3: scalestring = ' SindSc '
    elif individualscale == 5: scalestring = ' P5Sc '
    elif individualscale == 6: scalestring = ' P6Sc '
    elif individualscale == 7: scalestring = ' P7Sc '
    else: scalestring = ' P'+str(centerimage2zero)+str(individualscale)+'Sc '

    if (method == 2):  borderstring = ': start=' + str(startframe+1) + ', end=' + str(endframe+1)  
    else: borderstring = ': '
#
#    fenstertitel = p1.experiment + borderstring+scalestring + ', M=' +  str(method) +'/'+str(submethod)
#    fenstertitel = p1.ex_name + borderstring+scalestring + ', M=' +  str(method) +'/'+str(submethod)
#
#IF not localBatchMode Then window, /free, xsize = ( (p1.format_x) * zoomfactor),  $
#           ysize = p1.format_y * zoomfactor, title = Fenstertitel
#
    if exportTIFFframe:
        if localVIEW_batchmode:
            outfile = flag.STG_OdorReportPath # this is not the file, but the folder
        else:
            outCanvasFile = IDL.dialog_pickfile(flag.STG_OdorReportPath,'TIF_'+p1.metadata.ex_name,write=True,defaultextension='tif')

#          ELSE outFile = dialog_pickfile(/WRITE, path=flag[stg_odorReportPath],file='TIF_'+p1.experiment)
#    tvlct, r, g, b, /get
#end
#
#;write TIFF canvas
    if (exportTIFFcanvas >= 1):# THEN begin
#    ;get filename of file to write canvas to
        if localVIEW_batchmode: 
            outCanvasFile = os.path.join(flag.STG_OdorReportPath, flag.STG_ReportTag)#] $
        else: 
            outCanvasFile = IDL.dialog_pickfile(flag.STG_OdorReportPath,'',write=True,defaultextension='tif')
            #outCanvasFile = dialog_pickfile(/write, path=flag[stg_odorReportPath])
        #return

 


#    tvlct, r, g, b, /get
#ENDIF
    if   (exportTIFFcanvas == 1): outCanvasFile = outCanvasFile +'.tif'
    elif (exportTIFFcanvas == 2): outCanvasFile = outCanvasFile +'_3D.tif'
    elif (exportTIFFcanvas == 3): outCanvasFile = outCanvasFile +'_3D.raw'
    elif (exportTIFFcanvas == 4): outCanvasFile = outCanvasFile +'.tif'

    if (exportTIFFcanvas in [1,4]):
# 4 is multilayered, with odors side by side, but in python there is only one odor, therefore
        # combine exportTIFFcanvas 1 and 4 here        
        #    ;check if preexisting file: YES read file, NO create array
#    openR, 1, outCanvasFile, ERROR = err; err eq 0 if file exists
#    IF ( err eq 0 ) THEN begin ; file exists already
#       close, 1 ; reclose file
        if os.path.isfile(outCanvasFile):
            TIFFcanvas, (R,G,B) = IDL.read_tiff(outCanvasFile) #use plt.imsave to save            
            print('read file and palette: ', outCanvasFile)
#       TIFFcanvas = read_tiff(outCanvasFile, R, G, B)
            xySizeCanvas = TIFFcanvas.shape
#       xySizeCanvas = size(TIFFcanvas, /dimensions) ;xySize(0) contains x, (1) the y dimension
            if not localVIEW_batchmode:
#            if  localVIEW_batchmode:
                print(__file__,': testing color map plasma')
                plt.imshow(TIFFcanvas, cmap='plasma') 
    #       IF not localBatchMode THEN begin
    #         tvlct, r, g, b
    #         tv, TiffCanvas
    #       endIF
            if newcolumn:
    #         ;add a column to the TIFF canvas, and allow for more rows if necessary
                dummy_row_size =  max([xySizeCanvas[0],(p1.metadata.format_x+2*border)]) # x values
                dummy_col_size =  xySizeCanvas[1]+p1.metadata.format_y+border
                # byte type in python/numpy is 'uint8'
                dummy = IDL.bytarr(dummy_row_size,dummy_col_size)
                dummy[0:xySizeCanvas[0],0:xySizeCanvas[1]] = TIFFcanvas
                TIFFcanvas = dummy
                flag_RM_nextposition = (border, xySizeCanvas[1]) #tuple with rows,columns values
                print('ViewOverview.singleoverviews: Next frame (new column) to be placed at: ',flag_RM_nextposition)
                print('...TIFFcanvas size is: ',TIFFcanvas.shape)
                flag.RM_NewColumn = 0 #switch off newcolumn
            else: #ENDif ELSE begin; not newColumn
    #         ;not a new column, but a new frame at the bottom of the old column, so chech whether canvas is long enough
    #         ;therefore, either the length (xySizeCanvas(1) is sufficient,
    #         ;or take Nextposition + p1.formaty (multiplied by the frames necessary)
    ####NextPosition is a global variable!!! put into flags: flag_RM_nextposition
    # therefore position needs not to change here yet
                dummy_row_size =  max([xySizeCanvas[0],flag_RM_nextposition[0]+p1.metadata.format_x+border])
                dummy_col_size =  max([xySizeCanvas[1],flag_RM_nextposition[1]+p1.metadata.format_y+border]) #rows
                dummy = IDL.bytarr(dummy_row_size,dummy_col_size)
                dummy[0:xySizeCanvas[0],0:xySizeCanvas[1]] = TIFFcanvas
                TIFFcanvas = dummy
                print('ViewOverview.singleoverviews: Next frame (not new column) to be placed at: ',flag_RM_nextposition)
                print('...TIFFcanvas size is: ',TIFFcanvas.shape)
    #       ENDELSE ; newColumn
        else: #new file#    ENDIF else BEGIN ;create new canvas, add frame of border on each side
            TIFFcanvas = IDL.bytarr(p1.metadata.format_x+(2*border), p1.metadata.format_y+2*border)
            flag_RM_nextposition = [border,border] #;for right positioning of new data, see below
#    END
#endIF
#
#    if (exportTIFFcanvas == 4): ##############merged with exportTIFFcanvas == 1
#IF (exportTiffCanvas eq 4) THEN begin
#    ;check if preexisting file: YES read file, NO create array
#    IF existfile(outCanvasFile) THEN begin
#        if os.path.isfile(outCanvasFile):
#       TIFFcanvas = read_tiff(outCanvasFile, R, G, B)
#       xySizeCanvas = size(TIFFcanvas, /dimensions) ;xySize(0) contains x, (1) the y dimension
#       IF not localBatchMode THEN begin
#         tvlct, r, g, b
#         tv, TiffCanvas
#       endIF
#       IF newColumn THEN begin
#         ;add a column to the TIFF canvas, and allow for more rows if necessary
#         ;since with wxportTiffCanvas multiple odours are given sidewise, y is only increased by one frame
#         ;but x is increased by the number of odours
#         dummyYsize =  MAX([xySizeCanvas(1),(p1.metadata.format_y+border)+border])
#         dummy = bytARR((xySizeCanvas(0)+numodours*(p1.metadata.format_x+border)),dummyysize)
#         dummy(0:xySizeCanvas(0)-1,0:xySizeCanvas(1)-1) = TIFFcanvas
#         TIFFcanvas = dummy
#         NextPosition = xySizeCanvas ;to make sure the definition of NextPosition is correct copy both values
#         NextPosition(1) = border ; start the new column from the top
#       ENDif ELSE begin; not newColumn
#         ;not a new column, but a new frame at the bottom of the old column, so chech whether canvas is long enough
#         ;therefore, either the length (xySizeCanvas(1) is sufficient,
#         ;or take Nextposition + p1.formaty (multiplied by the frames necessary)
#         dummyYsize =  MAX([xySizeCanvas(1),Nextposition(1)+(p1.format_y+border)])
#         dummyXsize = MAX([xySizeCanvas(0),Nextposition(0)+numodours*(p1.format_x+border)])
#         dummy = bytARR(dummyXsize,dummyysize)
#         dummy(0:xySizeCanvas(0)-1,0:xySizeCanvas(1)-1) = TIFFcanvas
#         TIFFcanvas = dummy
#       ENDELSE ; newColumn
#    ENDIF else BEGIN ;create new canvas, add frame of border on each side
#       TIFFcanvas = bytARR(p1.format_x*numodours+((numodours+1)*border), (p1.format_y+border)+border)
#       nextPosition = [border,border] ;for right positioning of new data, see below
#    END
#endIF
#
#;****
    if (exportTIFFcanvas in [1,4]):
#    ;annotate canvas
        newsizecanvas = TIFFcanvas.shape
        windowSize = (newsizecanvas[1],newsizecanvas[0])
        #IDL window: Create graphics window number 10 with a size of x by y pixels and a title that reads TITLE:
        ### python: create PIL window
        mode = 'P' #(8-bit pixels, mapped to any other mode using a color palette
        window10 = PIL.Image.new(mode, windowSize) #creates an image into object window10

#    window, 10, xsize=newSizeCanvas(0), ysize=newSizeCanvas(1), TITLE='TextForTiffCanvas', /PIXMAP, RETAIN=2 ;pixmap makes the window invisible
#    ;window, 10, xsize=newSizeCanvas(0), ysize=newSizeCanvas(1), TITLE='TextForTiffCanvas', RETAIN=2 ;pixmap makes the window invisible
#endIF
#
#;correct the radius value if shrinkfactor is ste
    if shrinkfactor not in [0,1]:
        radius = radius / shrinkfactor
#endIF
#
#
#;go through all odours and calculate the overview frame
#for odor = firstbuffer, lastbuffer do begin
        ##in python, there is only one odor
#
#;*********************THIS is where the false-color picture is calculated************
    overviewframe = overview(p1, flag, method)
    # axes swapped to compensate for axis swapping by imshow
    # but swapping is not working in IDLoff mode, removed 27.7.19
    # overviewframe = overviewframe.swapaxes(0, 1)
    # without swapping, overviewframe has the right shape. 
#;*********************all that follows is additional information************
#
    if unsharpmaskfilter: # THEN begin
        print('ViewOverview.singleoverviews: unsharpmaskfilter with fixed settings - check' )
        print('does not work, because smooth creates values that are too small - needs a smooth or median on the original data')
        overviewframe = 2 * overviewframe - IDL.smooth(overviewframe, unsharpmasksize)
#           overviewFrame = 2*overviewframe - smooth(overviewframe, unsharpmasksize, /edge_truncate)
        if (unsharpmasksize2 > 0): overviewframe = 2*overviewframe - IDL.smooth(overviewframe, unsharpmasksize2)
#    endIF
#
#
    if (individualscale == 1):
        if percentilescale:
            minimum = np.percentile(overviewframe, 100*percentilevalue)
            maximum = np.percentile(overviewframe, 100-100*percentilevalue)
        else:
            minimum = np.min(overviewframe)
            maximum = np.max(overviewframe)        

    elif (individualscale == 3): # then begin ;take min and max only from central region
        if percentilescale:
            minimum = np.percentile(overviewframe[round(indiscale3factor*p1.metadata.format_x):round((1-indiscale3factor)*p1.metadata.format_x) ,
                                           round(indiscale3factor*p1.metadata.format_y):round((1-indiscale3factor)*p1.metadata.format_y)], 100*percentilevalue)
            maximum = np.percentile(overviewframe[round(indiscale3factor*p1.metadata.format_x):round((1-indiscale3factor)*p1.metadata.format_x) ,
                                           round(indiscale3factor*p1.metadata.format_y):round((1-indiscale3factor)*p1.metadata.format_y)], 100-100*percentilevalue)
#           maximum = percentile(overviewframe((indiScale3factor*p1.format_x):((1-indiScale3factor)*p1.format_x),(indiScale3factor*p1.format_y):((1-indiScale3factor)*p1.format_y)),1-percentileValue)
        else:
            minimum = np.min(overviewframe[round(indiscale3factor*p1.metadata.format_x):round((1-indiscale3factor)*p1.metadata.format_x) ,
                                           round(indiscale3factor*p1.metadata.format_y):round((1-indiscale3factor)*p1.metadata.format_y)])
            maximum = np.max(overviewframe[round(indiscale3factor*p1.metadata.format_x):round((1-indiscale3factor)*p1.metadata.format_x) ,
                                           round(indiscale3factor*p1.metadata.format_y):round((1-indiscale3factor)*p1.metadata.format_y)])
#           minimum = min(overviewframe((indiScale3factor*p1.format_x):((1-indiScale3factor)*p1.format_x),(indiScale3factor*p1.format_y):((1-indiScale3factor)*p1.format_y)))
#           maximum = max(overviewframe((indiScale3factor*p1.format_x):((1-indiScale3factor)*p1.format_x),(indiScale3factor*p1.format_y):((1-indiScale3factor)*p1.format_y)))
#        endELSE
#    endif

    elif (individualscale in [5,6,7]): 
#    if ((individualScale ge 5) and (individualScale le 7)) then begin
#        ;scale with min and max of selected region
#        ;restore the selected region
#        ;5: min max from region
#        ;6 and 7, identical: min fixed, max from region (6 and 7 differ in exportmovie)
#        ;get selected AL area
#       IF (fix(flag[RM_differentViews]) gt 0) THEN begin
#              ;special section Tilman
#             ;areaFileName = flag[stg_OdorMaskPath]+strmid(Flag[stg_ReportTag],0,14)+p1.viewLabel+' '+strmid(Flag[stg_ReportTag],14)+'.area'
#             ;standard section
#             areaFileName = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.viewLabel+'.Area'
#        endIF else begin
#             areaFileName =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.Area'
#        endELSE
#       OPENR, 1, areafilename, ERROR = err   ;Try to open the file demo.dat.
#       IF (err NE 0) then begin
#         print, 'Looking for file: ',areafilename
#         areaFileName = Dialog_Pickfile(Path=flag[stg_OdorMaskPath], get_Path = inPath, Filter='*.Area', title='Choose perimeter file (or cancel and correct program)!')
#         flag[stg_OdorMaskPath] = inpath
#       endIF else begin
#         close, 1 ; file exists, all ok
#       endELSE
#       restore, areaFileName
        maskframe = IDL.restore_maskframe(flag) #restores maskframe from file

        #       ;now AL perimeter is in variable 'maskframe'
#       ;correct for unequal size array ######## removed, since dummy is not used later
#        dummy = overviewframe # ; get same size array
#        dummy[:]=0
#        xtop    = min( maskframe.shape[0], dummy.shape[0] ) 
#        ytop    = min( maskframe.shape[1], dummy.shape[1] ) 
##       ytop    = min([(size(maskframe))(2),(size(dummy))(2)] ) -1
#        dummy[0:xtop,0:ytop] = maskframe[0:xtop,0:ytop]
#       ;shift maskframe
        maskframe = np.roll(maskframe, (p1.shiftX/shrinkfactor, p1.shiftY/shrinkfactor), axis=(1,0)) #in numpy, vertical is first
#       maskframe = shift(maskframe, p1.shiftX/shrinkFactor, p1.shiftY/shrinkFactor)
#       ;now AL perimeter is in variable maskframe
        positions = maskframe > 0 # where(maskframe)
        if percentilescale: #THEN begin
            if (individualscale == 5): 
                minimum = np.percentile(overviewframe[positions],100*percentilevalue)
            maximum = np.percentile(overviewframe[positions],100-100*percentilevalue)
#           maximum = percentile(overviewframe(positions),1-percentileValue)
#        endIF else begin
        else:
            if (individualscale == 5): 
                minimum = np.min(overviewframe[positions])
            maximum = np.max(overviewframe[positions])
#           if (individualScale eq 5)  then minimum = min(overviewframe(positions))
#           maximum = max(overviewframe(positions))
#        endELSE
#    endIF ;indiscale 5
#    ;******************************
#    ********* end individual scale

#    ;adjust min/max if centerImage is selected to be symmetrical around 0, irrespective of indiscl
    if (centerimage2zero == 2): # then begin ;center the image at 0, simmetrically
        maximum = max([abs(minimum),abs(maximum)])
        minimum = -maximum
#    endIF
#       ;cut image above maximum and below minimum
    overviewframe = np.clip(overviewframe, minimum, maximum)
#       overviewframe = overviewframe < maximum
#       overviewframe = overviewframe > minimum
#        ;redefine maximum and minimum in order to avoid black and white in the false-color image
    setmaximum = (maximum + (maximum - minimum)/253.0)
    setminimum = (minimum - (maximum - minimum)/253.0)
#
#;       IF ((exportTIFFcanvas eq 1) or (exportTIFFcanvas eq 4)) then BEGIN ;annotate min and max on the canvas
#;           xyouts, NextPosition(0)+p1.format_x+border-2, NewSizeCanvas(1)-NextPosition(1)-p1.format_y, strTrim(string(fix(minimum*annotateFactor)),2), /device, ALIGNMENT=0, ORIENTATION=90
#### analysis#;           xyouts, 
#                               x coordinate: NextPosition(0)+p1.format_x+border-2, 
#                               y coordinate: NewSizeCanvas(1)-NextPosition(1)-p1.format_y, 
#                               text2write:   strTrim(string(fix(minimum*annotateFactor)),2), 
#                               where to write: /device, 
#                               ALIGNMENT=0, #0 means left alignment
#                               ORIENTATION=90 #90 means vertical going up
#;           xyouts, NextPosition(0)+p1.format_x+border-2, NewSizeCanvas(1)-NextPosition(1), strTrim(string(fix(maximum*annotateFactor)),2), /device, ALIGNMENT=1, ORIENTATION=90
#;           print, 'min max in singleoverviews is ',minimum, maximum
#;       ENDif
#    endif

#    ;annotate the used minimum and maximum on the canvas
    if (exportTIFFcanvas in [1,4]):
#    IF ((exportTIFFcanvas eq 1) or (exportTIFFcanvas eq 4)) then BEGIN ;annotate min and max on the canvas
#        window10 = IDL.xyouts(flag_RM_nextposition[0]+p1.format_x, newsizecanvas[1]-flag_RM_nextposition[1]-p1.format_y,
#                   str(int(round(minimum*annotatefactor))), 
#                   window10, orientation=90, fill=255, align='left')
        odortext = ImageALlocal.localodortext(flag, p1)
        mintext  = str(int(round(minimum*annotatefactor)))
        maxtext  = str(int(round(maximum*annotatefactor)))
        window10 = IDL.xyouts(flag_RM_nextposition[1]+p1.metadata.format_y,
                              flag_RM_nextposition[0]+p1.metadata.format_x+border,
                   odortext, 
                   window10, orientation=0, fill=255, align='right')
        window10 = IDL.xyouts(flag_RM_nextposition[1]+p1.metadata.format_y, #place in the image to the right
                   flag_RM_nextposition[0],                        #place in the image down
                   mintext, 
                   window10, orientation=90, fill=255, align='left')
#             xyouts, NextPosition(0)+p1.format_x+border-2, NewSizeCanvas(1)-NextPosition(1)-p1.format_y,     strTrim(string(fix(minimum*annotateFactor)),2), /device, ALIGNMENT=0, ORIENTATION=90, color=254
        window10 = IDL.xyouts(flag_RM_nextposition[1]+p1.metadata.format_y,
                              flag_RM_nextposition[0]+p1.metadata.format_x,
                   maxtext, 
                   window10, orientation=90, fill=255, align='right')
#             xyouts, NextPosition(0)+p1.metadata.format_x+border-2, NewSizeCanvas(1)-NextPosition(1),
#                   strTrim(string(fix(maximum*annotateFactor)),2), /device, ALIGNMENT=1, ORIENTATION=90, color=254
        print('ViewOverview.singleoverviews line ',get_linenumber(),': canvas annotated with min max ',minimum, maximum)
        print(' as: ',mintext, maxtext)
        if (centerimage2zero > 0): 
            window10 = IDL.xyouts(flag_RM_nextposition[1]+p1.metadata.format_y,
                                  flag_RM_nextposition[0]+round(0.5 * p1.metadata.format_x),
                       '0', 
                       window10, orientation=90, fill=255, align='center')
            #THEN xyouts, NextPosition(0)+p1.format_x+border-2, NewSizeCanvas(1)-NextPosition(1)-fix(0.5*p1.format_y),    strTrim('0',2), /device, ALIGNMENT=0, ORIENTATION=90, color=254
        if newcolumn: #only if new column there is space to write something
            window10 = IDL.xyouts(flag_RM_nextposition[1], flag_RM_nextposition[0],
                                  p1.experiment[0:10], 
                                  window10, orientation = 0, fill=255, align='left') #IDL orientation was 1
#    ENDif
#
#
#
#;remove data outside mask if so wanted
    if withinarea: # then begin
#    IF (fix(flag[RM_differentViews]) gt 0) THEN begin
#           areaFileName = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.viewLabel+'.Area'
#        endIF else begin
#           areaFileName =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.Area'
#        endELSE
#       OPENR, 1, areafilename, ERROR = err   ;Try to open the file demo.dat.
#       IF (err NE 0) then begin
#         print, 'Looking for file: ',areaFileName
#         areaFileName = Dialog_Pickfile(Path=flag[stg_OdorMaskPath], get_Path = inPath, Filter='*.Area', title='Choose perimeter file (or cancel and correct program)!')
#         flag[stg_OdorMaskPath] = inpath
#       endIF else begin
#         close, 1 ; file exists, all ok
#       endELSE
#       restore, areaFileName
        maskframe = IDL.restore_maskframe(flag) #restores maskframe from file
#       ;now AL perimeter is in variable 'maskframe'
#       ;correct for unequal size array
#       dummy = overviewframe ; get same size array
#       dummy(*)=0
#       xtop    = min([(size(maskframe))(1),(size(dummy))(1)] ) -1
#       ytop    = min([(size(maskframe))(2),(size(dummy))(2)] ) -1
#       dummy(0:xtop,0:ytop) = maskframe(0:xtop,0:ytop)
#       ;shift maskframe
#       maskframe = shift(maskframe, p1.shiftX/shrinkFactor, p1.shiftY/shrinkFactor)
#           AreaPositions = where(maskframe eq 0) ;remember Area Positions for MorphoBackground
#           overviewFrame(Areapositions) = setminimum
#        endIF
#        dummy = overviewframe # ; get same size array  ########## removed since dummy is not used later
#        dummy[:]=0
#        xtop    = min( maskframe.shape[0], dummy.shape[0] ) 
#        ytop    = min( maskframe.shape[1], dummy.shape[1] ) 
##       ytop    = min([(size(maskframe))(2),(size(dummy))(2)] ) -1
#        dummy[0:xtop,0:ytop] = maskframe[0:xtop,0:ytop]
#       ;shift maskframe
        maskframe = np.roll(maskframe, (p1.shiftX/shrinkfactor, p1.shiftY/shrinkfactor), axis=(1,0)) #in numpy, vertical is first
        overviewframe[maskframe == 0] = setminimum
#
#
#    ;odorText enthlt Text, der unterhalb des Bildes ist
#    ;odorText = p1.ex_name + '_' + p1.treatment + '_' + strtrim(string(fix(p1.treat_conc *10)),2) ; neue Listen
#    odortext = ImageALlocal.localodortext(flag, p1)
#    ;odorText = p1.odor(odor) + '_' +strTrim(string(p1.odor_nr(1)),2)
#    ;odorText = p1.odor(odor) + '_' +strTrim(p1.viewLabel,2)
#    ;odorText  = p1.ex_name + '_' + strmid(p1.treatment,0,1);vom treatment nur der erste buchstabe
#   if (exportTIFFcanvas in [1,4]):
#    IF ((exportTIFFcanvas eq 1) or (exportTIFFcanvas eq 4)) then BEGIN ;annotate odortext on the canvas
#       xyouts, Nextposition(0)+p1.format_x, NewSizeCanvas(1)-NextPosition(1)-p1.format_y-border,odorText, /device, ALIGNMENT=1, color=254
#        window10 = IDL.xyouts(flag_RM_nextposition[1]+p1.format_y, 
#                              flag_RM_nextposition[0]+p1.format_x+border,
#                   odortext, 
#                   window10, orientation=0, fill=254, align='right')
#    ENDIF
#
#
#
#    ;mark the chosen glomeruli in the frame
    if markcoordinates in [1,3,4]:
        print('ViewOverview.singleoverviews: marking coordinates')
#        IF fix(flag[RM_differentViews]) THEN begin
#           readListe, GlomeruliNum, liste, flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.viewLabel+'.coor' , column4=separateLayers
#        endIF else begin
#           readListe, GlomeruliNum, liste, flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.coor', column4=separateLayers
#        endELSE
        liste = View_gr_reports.read_glo_liste(flag, p1)
#        liste = View_gr_reports.readListe(flag,p1)
        # go through glomeruli. That is not the computationally fastest way, but easier to read
#     ;delete overviewframe for markcoordinates eq 4
        if markcoordinates == 4:
            overviewframe[:] = 0
            setminimum = 0
            setmaximum = 255
#     IF (markcoordinates eq 4) THEN begin
#        overviewframe(*)=0
#        Setminimum = 0
#        Setmaximum = 255
#     endIF
#    IF (markCoordinates eq 1 ) THEN markValue = Setmaximum ELSE markValue = Setminimum
            #changed logic to 3, because in the case of 4 we need maximum
        if markcoordinates == 3:
            markvalue = setminimum
        else:
            markvalue = setmaximum

######the following (shift and shrink) is in readliste now
#        for index, row in liste.iterrows():
#            print('Now glomerulus ',index, row)
#            row.x_glo = row.x_glo + p1.shiftX
#            row.y_glo = row.y_glo + p1.shiftY
##     ;shiftMaskeX, shiftMaske
##     liste(0,*) = liste(0,*) + p1.shiftX
##     liste(1,*) = liste(1,*) + p1.shiftY
##     ;consider shrinkfactor
##     IF (shrinkFactor gt 1) then begin
#            if (flag.LE_ShrinkFaktor > 1): #no shrinking below 1?
#                row.x_glo = row.x_glo / flag.LE_ShrinkFaktor
#                row.y_glo = row.y_glo / flag.LE_ShrinkFaktor
##       liste(0,*) = liste(0,*)/shrinkFactor
##       liste(1,*) = liste(1,*)/shrinkFactor
#    endIF
#     ;now mark the relative positions
        for index, row in liste.iterrows():
#        for i=0,GlomeruliNum-1 do begin
#         ;only draw the right layer if separateLayers is checked
#         if separateLayers THEN begin
#           IF (odor eq liste(3,i)) THEN drawCoordinate = 1 ELSE drawCoordinate = 0
#         endIF else drawCoordinate = 1
#
#         IF drawCoordinate then begin
#           ;mark position liste(0),liste(1), would be frame2(liste(0),liste(1))
            leftborder  = max(row.x_glo-radius,0)
            rightborder = min(row.x_glo+radius,p1.metadata.format_x-1)
            topborder   = max(row.y_glo-radius,0)
            bottomborder= min(row.y_glo+radius,p1.metadata.format_y-1)
#           leftborder   = MAX([liste(0,i)-radius,0])
#           rightborder  = MIN([liste(0,i)+radius,p1.format_x-1])
#           topborder    = MAX([liste(1,i)-radius,0])
#           bottomborder = MIN([liste(1,i)+radius,p1.format_y-1])
#           ;wenn er hier aussteigt, dann ist eine Koordinate mitsamt Rahmen total aus dem Bild verschwunden!
            overviewframe[leftborder : rightborder, topborder    ]=markvalue
            overviewframe[leftborder : rightborder, bottomborder ]=markvalue
            overviewframe[leftborder , topborder  : bottomborder ]=markvalue
            overviewframe[rightborder, topborder  : bottomborder ]=markvalue
#           IF (markCoordinates eq 4) THEN begin ;color fill the glomeruli squares
#             fillvalue = liste(2,i) < 244 ; only byte values allowed
            if markcoordinates == 4:
                overviewframe[leftborder+1:rightborder,topborder+1:bottomborder] = row.num_glo
#           endIF
#          endIF
#        endfor
#    ENDIF ; markCoordinates
        
#    ;overlay an external TIFF file
#    ;this 'maske' file needs to be a greyscale tiff, only values of 0 (black) are taken
    elif markcoordinates in [2,3]:
        print('ViewOverview.singleoverviews ',get_linenumber(),': overlay external tiff file not yet implemented *******************  ')
#    IF ((markCoordinates eq 2) OR (markCoordinates eq 3 ) ) THEN begin
#        IF fix(flag[RM_differentViews]) THEN begin
#           maske = read_tiff(flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.viewLabel+'.tif');
#        endIF else begin
#           maske = read_tiff(flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.tif');
#        endELSE
#       maske = shift(maske, p1.shiftX, p1.shiftY)
#       xsizemaske = fix((size(maske))(1)/shrinkFactor)
#       ysizemaske = fix((size(maske))(2)/shrinkFactor)
#        IF (shrinkFactor gt 1) then begin
#         maske = rebin( maske(0:xsizemaske*shrinkFactor-1, 0:ysizemaske*shrinkFactor-1), xsizemaske,ysizemaske)
#         maske = (maske > 200) - 200
#         print, 'Maske rescaled in singleoverviews.pro after shrinkFactor correction'
#        endIF
#        for xi=0, min([xsizemaske,p1.format_x])-1 do begin
#          for yi=0, min([ysizemaske,p1.format_y])-1 do begin
#           IF (maske(xi,yi) eq 0) THEN overviewframe(xi,yi) = Setmaximum
#          endFOR
#        endFOR
#    endIF
    elif markcoordinates in [5]:
        print('ViewOverview.singleoverviews ',get_linenumber(),': overlay markCoordinates 5 not implemented yet *******************  ')
#    IF ((markCoordinates eq 5 )) THEN begin
#        IF fix(flag[RM_differentViews]) THEN begin
#           areaFile = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1.viewLabel+'.area'
#        endIF else begin
#           areaFile = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.area'
#        endELSE
#       restore, areafile ;restores variable maskframe
#       maske = shift(maskframe, p1.shiftX, p1.shiftY)
#       xsizemaske = fix((size(maske))(1)/shrinkFactor)
#       ysizemaske = fix((size(maske))(2)/shrinkFactor)
#        IF (shrinkFactor gt 1) then begin
#         maske = rebin( maske(0:xsizemaske*shrinkFactor-1, 0:ysizemaske*shrinkFactor-1), xsizemaske,ysizemaske)
#         print, 'Maske rescaled in singleoverviews.pro after shrinkFactor correction'
#        endIF
#        maske = roberts(maske) ; edge-detection
#       maske = dilate(maske,REPLICATE(1, 2,2))
#       maske = bytscl(maske)
#
#        for xi=0, min([xsizemaske,p1.format_x])-1 do begin
#          for yi=0, min([ysizemaske,p1.format_y])-1 do begin
#           IF (maske(xi,yi) gt 200) THEN overviewframe(xi,yi) = Setmaximum
#          endFOR
#        endFOR
#    endIF
#
#
#    ;mark the border of the whole frame
    if markborder: 
        markvalue = setmaximum #;default value
        if (flipsides > 0): # THEN begin
            if flipframe: # THEN begin ; right side, green color is about a third of the colour scale
                markvalue = setminimum + ((setmaximum - setminimum)/3.0)
            else: # begin ;left side
                markvalue = setmaximum - ((setmaximum - setminimum) / 250.0)
        overviewframe[0 ,:]  = markvalue
        overviewframe[-1,:]  = markvalue
        overviewframe[: ,0]  = markvalue
        overviewframe[: ,-1] = markvalue
#           overviewframe(*,0)=markValue
#           overviewframe(p1.format_x-1,*)=markValue
#           overviewframe(*,p1.format_y-1)=markValue
#    ENDIF ; markBorder
#    ;mark the border of the whole frame if unsharp mask is on
    if unsharpmaskfilter: # THEN begin
        markvalue = setmaximum -  ((setmaximum - setminimum)/3.0)
        overviewframe[0 ,:]  = markvalue
        overviewframe[-1,:]  = markvalue
        overviewframe[: ,0]  = markvalue
        overviewframe[: ,-1] = markvalue
        overviewframe[0 , int(p1.metadata.format_y/3):int(2*p1.metadata.format_y/3)]    = setminimum
        overviewframe[int(p1.metadata.format_x/3):int(2*p1.metadata.format_x/3) , 0]    = setmaximum
        overviewframe[-1 , int(p1.metadata.format_y/3) : int(2*p1.metadata.format_y/3)] = setminimum
        overviewframe[int(p1.metadata.format_x/3):int(2*p1.metadata.format_x/3),-1]     = setmaximum
#    endIF
#
###################
        # copy overviewframe to frame2, scale to bytes
###################
#    ;scale image to byte range
    if ((centerimage2zero == 0) or (centerimage2zero == 2)): #THEN begin
#       ;scale image to byte
        frame2 = IDL.bytscl(overviewframe, MIN=setminimum, MAX=setmaximum)#, TOP=!d.table_size)
        print('SingleOverviews  ',get_linenumber(),', Image scaled to min, max: ', setminimum, setmaximum)
#    endIF
    elif (centerimage2zero == 1): # THEN begin
#       ;if centerImage2zero is 1, range from 0 to max and from 0 to min are scaled independently!
#       ;if centerImage2zero is 2, scaling is equal for top and bottom range, below
        frameup   = IDL.bytscl(overviewframe, MIN=0,          MAX=setmaximum)#,   TOP=!d.table_size)
        framedown = IDL.bytscl(overviewframe, MIN=setminimum,    MAX=0     )#   TOP=!d.table_size)
        if (setminimum >= 0): framedown[:] = 255
        frame2    = (framedown/2 + frameup/2).astype('uint8')
#       ;frame2      = frame2 < 254
        frame2      = np.clip(frame2,1,255)
        print('SingleOverviews  ',get_linenumber(),', Image scaled to min, ctr, max: ', setminimum, '; 0; ', setmaximum)
#    endIF
    elif (centerimage2zero == 3):
#       ;if centerImage2zero is 1, range from 0 to max and from 0 to min are scaled independently!
#       ;if centerImage2zero is 2, scaling is equal for top and bottom range, below
#       ;if centerImage2zero is 3, range from 0 to max and from 0 to min are scaled independently! 0 is at 1/4 of the scale ()
        frameup   = IDL.bytscl(overviewframe, MIN=0,          MAX=setmaximum)#,   TOP=!d.table_size)
        framedown = IDL.bytscl(overviewframe, MIN=setminimum,    MAX=0)#,        TOP=!d.table_size)
        if (setminimum >= 0): 
            framedown[:] = 255
        frame2      = (framedown/4.0 + 3*frameup/4.0).astype('uint8')
#       ;because of the rescaling, some pixels can get the value 0 now, and appear black in a colorscale with black bottom
#       ;just put these pixels to 1
#       ;frame2      = frame2 < 254
        frame2      = np.clip(frame2,1,255)
        print('SingleOverviews  ',get_linenumber(),', Image scaled to min, ctr, max: ', setminimum, '; 0; ', setmaximum)
#    endIF
    else:
        print('Singleoverviews  ',get_linenumber(),': centerimage2zero with unexpected value')
#else
#    ;morphoThreshold
    print('SingleOverviews: Morphothreshold not implemented yet')
#    MorphoThreshold256, frame2, withinMask, Areapositions, r, g, b
#
#
#    ;zoom image
    if zoomfactor != 1:
        frame2 = IDL.rebin(frame2, (p1.metadata.format_x) * zoomfactor, p1.metadata.format_y * zoomfactor, sample = 1)
        #this rebin destroyed the image in my test run - but I don't know why
#
#    ;flip sides if right AL
#    IF (flipFrame eq 1) THEN frame2 = rotate(frame2,5) #flip on the vertical axis
    if (flipframe == 1): frame2 = np.fliplr(frame2)
    if (flipframe == 2): frame2 = np.flipud(frame2) #rotate 7
#
    if not localVIEW_batchmode: 
        ## show image in VIEWgui
        #img = PIL.Image.fromarray(frame2) #, 'RGB')
        
#im = Image.fromarray(np.uint8(cm.gist_earth(myarray)*255)) from https://stackoverflow.com/questions/10965417/how-to-convert-numpy-array-to-pil-image-applying-matplotlib-colormap
        #img = PIL.Image.fromarray(cm.gist_earth(frame2).set_clim(0,255)))

        ct_IDLpalette = IDL.createPalette(flag.SO_MV_colortable)
        #print('ViewOverview - loaded palette ',flag.SO_MV_colortable)

        #img.show()
        # in view-gui use plt, not PIL - 
        if not plt.isinteractive():
            plt.ion()
        plt.figure()    
        #plt.imshow(frame2.T, cmap=ct_IDLpalette, vmin=100, vmax=200, origin='bottom')
        print('ViewOverview.singleovervies line ',get_linenumber(),': frame2 has values ranging from ',
              np.min(frame2), np.max(frame2))
        plt.imshow(frame2.T, cmap=ct_IDLpalette, origin='bottom', vmin=0, vmax=255)
        #I scale 0-255, since bytscl has done the scaling to bytes before
        plt.title('Better not save from VIEWgui - run VIEWoff')
        plt.draw()
        # plt.show(block=False)
        
        #https://matplotlib.org/3.1.0/tutorials/colors/colormap-manipulation.html
        #TODO add color map here
    if exportTIFFframe:
        tifffilename = os.path.join(outfile,ImageALlocal.localodortext(flag, p1) + '.tif')
#img has not been created yet!
#def write_tiff(outfile, MyArray, red, green, blue, xresol=100, yresol=100):
        IDL.write_tiff(tifffilename, frame2, R, G, B)
#           write_tiff, outFile+LocalOdorText(p1,odor)+'.tif', frame2, red=r, blue=b, green=g
        print('Singleoverviews: Written tiff to ',tifffilename)
#    endIF
#
    if exportTIFFcanvas in [1,4]:
#    IF (exportTIFFcanvas eq 1) THEN begin
#           ;copy frame2 to the right position of the canvas
#           ;TIFFcanvas(nextPosition(0):nextPosition(0)+p1.format_x-1, NextPosition(1)+(odor-firstbuffer)*(p1.format_y+border): NextPosition(1)-border+(odor-firstbuffer+1)*(p1.format_y+border)-1)=frame2
#       ;die obere Zeile mit der nächsten ersetzt, als bei der Alten Anlage die berechnung mehrerer Bilder untereinander f¸r einen 4er Block nicht ging, Nov 1999
#       TIFFcanvas(nextPosition(0):nextPosition(0)+p1.format_x-1, NextPosition(1): NextPosition(1)+p1.format_y-1)=frame2
        TIFFcanvas[flag_RM_nextposition[0]:flag_RM_nextposition[0]+p1.metadata.format_x,
                   flag_RM_nextposition[1]:flag_RM_nextposition[1]+p1.metadata.format_y] = frame2
        flag_RM_nextposition = (flag_RM_nextposition[0]+p1.metadata.format_x+border,flag_RM_nextposition[1])
#       NextPosition(1) = NextPosition(1) + border + p1.format_y
        print('Remember and write to flags: New Nextposition is ',flag_RM_nextposition)
        flags_input.update_flags({'RM_NextPosition': flag_RM_nextposition})
        #flag.RM_NextPosition = flag_RM_nextposition 

#    ENDif ; exportTIFFcanvas
#    IF (exportTIFFcanvas eq 2) THEN begin
    elif (exportTIFFcanvas == 2): # THEN begin
#       tvlct, r, g, b ##this gives the color table to the display. 
        # if I understand this correctly, IDL tv is like PIL imshow
#       tv, frame2
        plt.imshow(frame2)
#        write_tiff, outCanvasFile, frame2, red=r, blue=b, green=g, /append
#       ;NextPosition(1) = NextPosition(1) + border + p1.format_y
        print('not implemented yet: frame written to multilayered TIFF ',outCanvasFile)
              #TODO
        #return NotImplemented
#    ENDif ; exportTIFFcanvas
    elif (exportTIFFcanvas == 3):
        print('ViewOverview.Singleoverviews:  exportTIFFcanvas 3 not implemented yet')
#    IF (exportTIFFcanvas eq 3) THEN begin
#        ;write_raw_frame, outCanvasFile, frame2
#       write_raw_frame, outCanvasFile, overviewframe, p1, odor ;export raw and not scaled data
#       ;NextPosition(1) = NextPosition(1) + border + p1.format_y
#       print, 'frame written to multilayered raw file ',outCanvasFile
#    ENDif ; exportTIFFcanvas
#endfor ;odor
#
#; draw scalebar
#IF drawScalebar THEN begin
    if (drawscalebar):
        print('ViewOverview.Singleoverviews:  drawscalebar')
        scalebar = np.tile(np.arange(p1.metadata.format_x*zoomfactor),(31,1)) #create array with repeated elements, 31 pixels wide
#    scaleBar = INTARR(31,p1.format_y*zoomfactor)
#    scale    = reverse(indgen(p1.format_y*zoomfactor))
#    for i=0,30 do scaleBar(i,*) = scale(*)
#    IF ((setminimum lt 0) and (setmaximum gt 0)) THEN begin ;mark 0 position
        if (setminimum < 0) & (setmaximum > 0):
            if centerimage2zero == 3:
#       IF (centerImage2zero eq 3) THEN begin
#         ;level = (3*p1.format_y*zoomfactor/4)
                level = 0.75 * p1.metadata.format_x*zoomfactor
#         level = 0.75*p1.format_y*zoomfactor
#       endIF else BEGIN
            else:
#                level = p1.format_x*zoomfactor - p1.format_x*zoomfactor*setminimum / (setminimum - setmaximum)
                level = p1.metadata.format_x*zoomfactor*setminimum / (setminimum - setmaximum)
#         level = p1.format_y*zoomfactor-p1.format_y*zoomfactor*(setminimum/(setminimum - setmaximum))
#       endELSE
#       scaleBar(*,fix(level))=0
            scalebar[:,int(level)] = 0
#    endIF
        scalebar = IDL.bytscl(scalebar, MIN=np.min(scalebar), MAX=np.max(scalebar))
#    scaleBar = bytscl(scaleBar)
        #################output moved down
#    IF not localBatchMode Then tv, bytscl(scaleBar, MIN=0, MAX=p1.format_y*zoomfactor, TOP=!d.table_size), 0
#    IF exportTIFFframe THEN write_tiff, outFile+'ScaleBar', scalebar, red=r, blue=b, green=g
            
#    IF (exportTIFFcanvas eq 1) THEN write_tiff, outCanvasFile+'ScaleBar', scalebar, red=r, blue=b, green=g
#    print, 'written scalebar'
#    ;or do a scale bar by hand:
#    ;loadct, SO_MV_colortable
#    ;tvlct, r, g, b, /get
#    ;scale = BINDGEN(256)
#    ;scalebar = intArr(31,256)
#    ;for i=0,30 do scalebar(i,*) = scale(*)
#    ;filename = dialog_pickfile(/write)
#    ;write_tiff, filename, scalebar, red=r, blue=b, green=g
#ENDif
#
#
#
#
#;save CANVAS
    if exportTIFFcanvas in [1, 4]: # THEN begin
#    ;annotate canvas
#    ;write title
#        if newcolumn: #only if new column there is space to write something
#            window10 = IDL.xyouts(newsizecanvas[0]-border, newsizecanvas[1], 
#                                  p1.experiment[0:10], 
#                                  window10, orientation = 0, fill=254, align='right') #IDL orientation was 1
#    ;write names for single odours
#    for odor = firstbuffer, lastbuffer do begin
#       ;xyouts, newsizeCanvas(0)-border, newSizeCanvas(1)-border+1-(((odor-firstbuffer)+1)*(p1.format_y+border)), p1.odor(odor), /device, ALIGNMENT=1
#    endfor
#    ;now get annotated image from screen
#    ;************here we have a frequent graphics problem - call Giovanni if that happens again
#    ;NewText = tvRD(/true)
#    ;NewText = tvRD()
#
#    ;the next two lines for 8 bit screen
#    ;NewText = tvRD(channel=3) ;set at KN:Picasso because of 24bit screen - may not work on other computers
#    ;NewTextIndices = where(NewText lt 128, count)
#
#    ;also: in IDL -> FILE -> PREFERENCES -> Graphics set backing store to bitmap buffered.
#
#    ;alternatively, the next two lines for 24 bit screen
#    ;NewText = tvRD(channel=1) ;set at KN:set to 1 for 8 bit screen
#    ;NewTextIndices = where(NewText gt 128, count)
#
#    ;new, hopefully automatic version, october 2010
#    device, get_visual_depth=depth ;ask for bit depth of screen
#    IF (depth eq 24) THEN begin
#        NewText = tvRD(channel=1) ;
#        NewTextIndices = where(NewText gt 128, count)
#    endif else begin
#        NewText = tvRD(channel=3) ;
#        NewTextIndices = where(NewText lt 128, count)
#    endelse
#
        newText = np.asarray(window10) #get array with all text
#        newText = np.swapaxes(newText, 0, 1)
        TIFFcanvas[newText>128] = 255  # copy this into canvas
#    ;therefore the next line
#    print, '**** IF TIFF FILES ARE BLANK, then!  '
#    print, 'overviews/Singleoverviews.pro: tvRD set to channel=1 or not; if there is no image change the line before here'
#    ; 'If it does not work, try retain keyword to 2 in preferences-graphics-backing store; see ?tvrd'
#    ; it may also be that the next line should be gt 128 instead of lt 128
#
#    if (count gt 0) then TiffCanvas(NewTextIndices) = 255
#    ;get necessary resolution for A4
        longSide  = max(newsizecanvas[0:1]) #;11.693 inches is 29.7 cm, 10,118 is 25.7 cm
        shortSide = min(newsizecanvas[0:1]) #;8.268 inches is 21 cm, 6.695 inches is 17 cm
        A4resolution = max([longSide/10.118,shortSide/6.695])
        # create palette
        ct_IDLpalette = IDL.createPalette(flag.SO_MV_colortable)#flag.SO_MV_colortable)
        #because of the way I have written IDL.write_tiff, for now I need to extract R,G,B
        #because I have written IDL.createPalette twice, with different logic. Too bad...
        #R, G, B = IDL.createPalette(flag.SO_MV_colortable)
        R, G, B = IDL.palette_pyplot2PIL(ct_IDLpalette)
        print('ViewOverview: created palette using: ',flag.SO_MV_colortable)
#        ctP = ct_IDLpalette(np.linspace(0,1,256))
#        #R is in ctP[:,0]
#        R = ctP[:,0]*255
#        G = ctP[:,1]*255
#        B = ctP[:,2]*255
        #IDL.write_tiff(outCanvasFile, TIFFcanvas, R, G, B, A4resolution, A4resolution)
        IDL.write_tiff(outCanvasFile, TIFFcanvas, R,G,B, A4resolution, A4resolution)
        if drawscalebar:
            IDL.write_tiff(outCanvasFile+'_scb.tif', scalebar, R, G, B)#, A4resolution, A4resolution)
#question: what happened to window10? Why did I need that?        
#        window10.save(outCanvasFile)
#    write_tiff, outCanvasFile, TIFFCanvas, red=r, blue=b, green=g, xresol=A4resolution, yresol=A4resolution
#    ;IF not localBatchMode THEN begin
#         window, 11, xsize=newSizeCanvas(0), ysize=newSizeCanvas(1), TITLE='TIFFcanvas'
#         tvlct, r, g, b
#         tv, TiffCanvas
#         print, 'Canvas written to file ',outCanvasFile
#    ;endIF
#endIF
#
#;reset color table
#loadct, SO_MV_colortable
#
#odor=1
#
#end
    #remember 
    
#    flags_input.update_flags({'RM_NextPosition': flag_RM_nextposition})
    print('ViewOverview.singleoverviews done')
    # returns the flags object whenever possible
    return flags_input
#; of program singleoverviews
    
def overview(p1, flag, method):
    if method == 0:
        overviewframe = overview0ctv(p1, flag)
    elif method == 10:
        overviewframe = overview10ctv(p1, flag)
    else:
        print('ViewOverview.overview: method not yet considered in python (19.9.2018)')
#
#IF correctFlag eq 0 THEN signals = sig1  ELSE signals = sig1corr
#filter     =  1
#filtersize =  5
#startframe = firstframe
#endframe   = lastframe
#method = fix(method) ;this line is needed because flags are defined as strings
#CASE method OF
#  0: BEGIN
#       OverviewFrame = Overview0CTV(odorNum)
#  END
#  1: BEGIN
#       OverviewFrame = Overview1Sum(signals, odorNum, filter, filtersize, startframe, endframe, p1)
#  END
#  2: BEGIN
#       OverviewFrame = Overview2Diff(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  3: BEGIN
#       OverviewFrame = Overview3Max(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  4: BEGIN
#       OverviewFrame = Overview4Contrast(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  5: BEGIN
#       OverviewFrame = Overview5Silke(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  6: BEGIN
#       OverviewFrame = Overview6VisiAM(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  7: BEGIN
#       OverviewFrame = Overview7max9_19(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  8: BEGIN
#       OverviewFrame = Overview8mean(signals, odorNum, filter, filtersize, startframe, endframe,p1)
#  END
#  10: BEGIN
#       OverviewFrame = Overview10CTV(odorNum)
#  END
#  11: BEGIN
#       OverviewFrame = Overview11correlate(signals,odorNum)
#  END
#  12: BEGIN
#       OverviewFrame = Overview12long_correlate(signals,p1.odors)
#  END
#  ELSE: text = dialog_message('WARNING: wrong method in Overview.pro, set flag[so_method]')
#ENDCASE
    return overviewframe

def overview0ctv(p1, flag):
    '''
    apply curve2value to every single pixel in the frame - slow
    '''
    print('ViewOverview.overview0ctv not implemented yet in python (19.9.2018)')
    overviewframe = 0
    return overviewframe

def overview10ctv(p1, flag):
    '''
    calculate overview frame from a calculation on frames, rather than time traces
    therefore, functions in curve2value have to be repeated here, with some delicacy
    faster than overview0ctv.
    
    Not all cases were implemented in python - when needed, work on ViewOverview.overview10ctv
    '''
    CTVmethod = flag.CTV_Method
#;externalized CTVs are:
#;values below 0 go to personal Overview10CTVLocal in ImageALLocal folder
#IF (CTVmethod lt 0) THEN OverviewFrame=Overview10CTVLocal(odorNum)
    if CTVmethod < 0: 
        print('ViewOverview.overview10ctv does not implement flag.CTV_Method < 0, i.e. Overview10CTVLocal')
        return
#;values above 1000 go to Overview10CTVMathias in ImageALMathias folder
#IF (CTVmethod gt 1000) THEN OverviewFrame=CurveToValueMathias(odorNum)
    if CTVmethod > 1000: 
        print('ViewOverview.overview10ctv does not implement flag.CTV_Method > 0, i.e. CurveToValueMathias')
        return
#;poor old Giovanni only has values between 0 and 999 (1000 is lost in ...)
#IF (CTVmethod ge 0) AND (CTVmethod le 1000) THEN begin
    TIMEfilter = flag.Signal_FilterTimeFlag #;aus common vars
    SPACEfilter = flag.Signal_FilterSpaceFlag
    overviewFrame = IDL.fltarr(p1.metadata.format_x,p1.metadata.format_y)
#;INPUT IS SIG1corr(x,y,*,odorNum) or sig1(x,y,*,odornum)
#IF  correctFlag then begin
#	dummy = sig1corr(*,*,*,odorNUM)
#end ELSE BEGIN
    dummy = p1.sig1.copy()
#end
#;remove spurious dimension
#dummy = reform(dummy)
#;apply time filter - makes no sense
    if TIMEfilter: #dummy = smooth(dummy, Signal_FilterTimeSize)
        print('ViewOverview.overview10ctv timefilter implemented differently from IDL version')
        # in IDL, the filter was applied to all three dimension - but a time filter should only work on time
        dummy = IDL.smooth(dummy, [0,0,flag.Signal_FilterTimeSize])
#;define masks for influence of each frame onto the final image
    maskFactor = np.zeros(p1.metadata.frames, dtype=np.float32)
    firstframe = flag.CTV_firstframe #this was just firstframe in IDL
    lastframe  = flag.CTV_lastframe
#CASE fix(flag[ctv_method]) OF $  ;calculate with same values as CTV
    if CTVmethod == 12:        
#	12  :  begin
#    			; from CurveToValue result = TOTAL(curve(firstFrame:lastFrame))  ;total between values in control window
        maskFactor[firstframe:lastframe+1]= 1.0/(lastframe+1-firstframe)
#    		end
    elif CTVmethod == 20: #  begin
        maskFactor[lastframe]=1.0
        maskFactor[firstframe]=-1.0
#    		end
#    21  :  begin
#    		    maskFactor(p1.stimulus_on+2:p1.stimulus_on+4)=1.0/3
#    			maskFactor(p1.stimulus_on-3:p1.stimulus_on-1)=-1.0/3
#    		end
#	;22: mean of 3 frames around lastframe - mean of 3 frames around firstframe
#	;22  :  overviewFrame(*,*) = total((dummy(*,*,lastframe-1:lastframe+1) - dummy(*,*,firstframe-1:firstframe+1)),3)/3
    elif CTVmethod == 22  :  
        maskFactor[lastframe-1:lastframe+2]   = 1.0/3
        maskFactor[firstframe-1:firstframe+2] =-1.0/3
#    		end
#	23  : begin
#				maskFactor(p1.stimulus_on+2:p1.stimulus_on+3*p1.frequency) = +1/(3*p1.frequency)
#				maskFactor(p1.stimulus_on-3*p1.frequency:p1.stimulus_on-1) = -1/(3*p1.frequency)
#		  end
#    ;24: mean of 3 frames 1 sec after stimOnset, - mean of 3 frames before stimOnset
#	;24  :  overviewFrame(*,*) = (TOTAL(dummy(*,*,p1.stimulus_on+p1.frequency-1:p1.stimulus_on+p1.frequency+1),3) - TOTAL(dummy(*,*,p1.stimulus_on-3:p1.stimulus_on-1),3))/3
#	24  :  begin
#				maskFactor(p1.stimulus_on+p1.frequency-1:p1.stimulus_on+p1.frequency+1)=1.0/3
#				maskFactor(p1.stimulus_on-3:p1.stimulus_on-1)= -1.0/3
#		   end
#	25  :  begin
#    			maskFactor(lastframe-1:lastframe+1)=1.0/3
#    			maskFactor(firstframe-7:firstframe+1)=-1.0/9
#		   end
#	26  :  begin                     ; Paul 11.12.01
#    			maskFactor(lastframe:lastframe+14)=1.0/15
#    			maskFactor(firstframe:firstframe+4)=-1.0/5
#    	   end
#	27  :  begin                     ; Paul 11.12.01
#    			maskFactor(lastframe:lastframe+2)=1.0/3
#    			maskFactor(firstframe:firstframe+4)=-1.0/5
#    	   end
#	;35 first find max of the overall average response within the 3 seconds after the stimulus
#	;then take mean around this max (3frames) - mean of 3 frames before stimulus
#	;this is similar, BUT NOT IDENTICAL to method 35 in CTV, because there the maximum is in each pixel position separatedly
    elif CTVmethod == 35 : 
        singleCurve = np.mean(dummy, axis = (0,1)) # total(total(dummy,1),1)
        position = p1.metadata.stimulus_on + np.argmax(singleCurve[p1.metadata.stimulus_on:p1.metadata.stimulus_on+int(3*p1.frequency)])
###this returns the FIRST maximum
#				position = p1.stimulus_on + position
        print('ViewOverview.Overview10CTV: Maximum frame in this measurement was ',position)
        maskFactor[position-1:position+2]=1.0/3
        maskFactor[p1.metadata.stimulus_on-3:p1.metadata.stimulus_on]=-1.0/3
#		end;35
#	38  :  begin ;daniela, get GLOBAL maximum between 2 and 5, subtract mean of 0-1 from that frame
#				singleCurve = total(total(dummy,1),1)
#				maxPos = max(singleCurve(2:5), position)
#				position = position+2
#				print, 'Maximum frame in this measurement was ',position
#				maskfactor(position)=1.0
#				maskfactor(0:1)=-1.0/2
#    	   end
#    50  :  begin   ;einstellungen fr Andre, ândern sich noch
#    			maskFactor(p1.stimulus_on+2:p1.stimulus_on+4)=1.0/3
#    			maskFactor(p1.stimulus_on-3:p1.stimulus_on-1)=-1.0/6
#    			maskFactor(p1.stimulus_on-3+p1.frequency*6:p1.stimulus_on-1+p1.frequency*6)=-1.0/6
#    		end
#    51  :  begin   ;einstellungen fr Andre, ândern sich noch
#    			maskFactor(11:13)		= 1.0/3
#    			maskFactor(6:8)		=-1.0/6
#    			maskFactor(24:26)	=-1.0/6
#    		end
#    100  :  begin
#    			maskFactor(0:2)=-1.0/3
#    			maskFactor(4:8)=1.0/5
#    		end
#    151  :  begin
#    			maskFactor(0)= -1.0/3
#    			maskFactor(3)= -1.0/3
#    			maskFactor(6)= -1.0/3
#    			maskFactor(9)=  1.0/3
#    			maskFactor(12)= 1.0/3
#    			maskFactor(15)= 1.0/3
#    		end
#    152  :  begin
#    			maskFactor(1)= -1.0/3
#    			maskFactor(4)= -1.0/3
#    			maskFactor(7)= -1.0/3
#    			maskFactor(10)= 1.0/3
#    			maskFactor(13)= 1.0/3
#    			maskFactor(16)= 1.0/3
#    		end
#    153  :  begin
#    			maskFactor(2)= -1.0/3
#    			maskFactor(5)= -1.0/3
#    			maskFactor(8)= -1.0/3
#    			maskFactor(11)= 1.0/3
#    			maskFactor(14)= 1.0/3
#    			maskFactor(17)= 1.0/3
#    		end
#	161  :  begin
#				maskFactor(0:1)=-1.0/2
#				maskFactor(2)  =1.0
#			end
#	162  :  begin
#				maskFactor(0:1)=-1.0/2
#				maskFactor(3)  =1.0
#			end
#	163  :  begin
#				maskFactor(0:1)=-1.0/2
#				maskFactor(4)  =1.0
#			end
#	164  :  begin
#				maskFactor(0:1)=-1.0/2
#				maskFactor(5)  =1.0
#			end
#	165  :  begin
#				maskFactor(0:2)=-1.0/3
#				maskFactor(3)  =1.0
#			end
#	166  :  begin
#				maskFactor(0:2)=-1.0/3
#				maskFactor(4)  =1.0
#			end
#	167  :  begin
#				maskFactor(0:2)=-1.0/3
#				maskFactor(5)  =1.0
#			end
#	300 : maskfactor(*) = 1.0/p1.frames
#	301: maskfactor(5:10)=1.0/6
#	302: maskfactor(p1.stimulus_on:p1.stimulus_on+2)=1.0/3
#	303: maskfactor(p1.stimulus_on-3:p1.stimulus_on)=1.0/4
#
#    322  :  begin
#    			maskFactor(lastframe-1:lastframe+1)=1.0/3
#    		end
#	335 : begin
#				singleCurve = total(total(dummy,1),1)
#				maxPos = max(singleCurve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency), position)
#				position = p1.stimulus_on + position
#				print, 'Maximum frame in this measurement was ',position
#				maskfactor(position-1:position+1)=1.0/3
#		end;35
#
#
#	;values above 500 now used for analyzing repetitive stimulation
#	524 : begin
#				;takes the three frames around one second after each stimulus as extimated max
#				;then sums activity after each next stimulus, and subtracts activity before each next stimulus
#				;the first stimulus is excluded from the analysis
#				;find place of first maximum
#				maxShift = p1.frequency-1
#				;interstimulus interval is p1.stimulus_isi, skip first response
#				position = p1.stimulus_on + p1.stimulus_isi ;next stimulus position
#				IF (p1.stimulus_isi gt 0) then begin
#					while ((position+Maxshift+1) lt (p1.frames-1)) do begin
#						maskfactor(position+Maxshift-1:position+Maxshift+1)=1.0/3
#						maskfactor(position-3:position-1)=-1.0/3
#						position = position + p1.stimulus_isi ; move to the next stimulus
#					endWhile
#				endIF
#		  end
#	535 : begin
#				;first calculates the delay between stimulus onset and response maximum using the first response
#				;then sums activity after each next stimulus, and subtracts activity before each next stimulus
#				;the first stimulus is excluded from the analysis
#				;find place of first maximum
#				singleCurve = total(total(dummy,1),1)
#				maxPos = max(singleCurve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency), MaxShift)
#				print, 'Maximum frame in this measurement was ',p1.stimulus_on + MaxShift
#				;interstimulus interval is p1.stimulus_isi
#				position = p1.stimulus_on + p1.stimulus_isi ;next stimulus position
#				IF (p1.stimulus_isi gt 0) then begin
#					while ((position+Maxshift+1) lt (p1.frames-1)) do begin
#						maskfactor(position+Maxshift-1:position+Maxshift+1)=1.0/3
#						maskfactor(position-3:position-1)=-1.0/3
#						position = position + p1.stimulus_isi ; move to the next stimulus
#					endWhile
#				endIF
#		  end
    else:   
        print('ViewOverview.Overview10CTV: WARNING: wrong method in Overview10ctv, set flag[ctv_method]')
#ENDCASE
#;Now calculate the overview frame
    for i in range(p1.metadata.frames): # do begin
#	OverviewFrame(*,*) = OverviewFrame(*,*) + dummy(*,*,i) * maskFactor(i)
        overviewFrame = overviewFrame + dummy[:,:,i]*maskFactor[i]
    print('ViewOverview/overview10ctv: created frame with maskFactor, sum is :',np.sum(maskFactor))



    if SPACEfilter: #dummy = smooth(dummy, Signal_FilterTimeSize)
        print('ViewOverview.overview10ctv spacefilter: neg value for GAUSSIAN filter. Set filter to: ',flag.Signal_FilterSpaceSize)
        # in IDL, the filter was applied to all three dimension - but a time filter should only work on time
        overviewFrame = View.SpaceFilter(overviewFrame,flag.Signal_FilterSpaceSize)

#endFOR
#;apply space filter
#if  (Signal_FilterSpaceSize gt 1) then OverviewFrame = SpaceFilter(OverviewFrame, Signal_FilterSpaceSize)
#ENDIF
#return, OverviewFrame
#end ; of program    
    
    
    
    
    
    return overviewFrame



def CurveToValue(curve, flag, p1):
    '''
    copy of CurveToValue
    uses flag 
    translate only what is used - the rest, when needed
    '''
#    function curveToValue, input
#;Author  Giovanni 1998
    CTVmethod = flag.CTV_Method
#;externalized CTVs are:
#;values below 0 go to personal CurvetoValueLocal in ImageALLocal folder
#IF (CTVmethod lt 0) THEN result=CurveToValueLocal(curve)
    if CTVmethod < 0:
        print('ViewOverview.CurveToValue: values below 0 not implemented yet (local)')
#;values above 1000 go to CurveToValueMathias in ImageALMathias folder
#IF (CTVmethod gt 1000) THEN result=CurveToValueMathias(curve)
    elif CTVmethod > 1000:
        print('ViewOverview.CurveToValue: values above 1000 not implemented yet (Mathias)')
#;poor old Giovanni only has values between 0 and 999 (1000 is lost in ...)
#IF (CTVmethod ge 0) AND (CTVmethod le 1000) THEN begin
#CASE CTVmethod OF $
    elif (CTVmethod == 1):
        result = np.mean(curve[10:19]) #  ;corresponds to A&S, Overview8Mean
#    2  :   result = TOTAL(curve(10:19))  ;corresponds to A&S best, integral über Zeit
#    3  :   begin ;gets the maximum between 10 and 19, then integral of MAX-2 to MAX+8
#         s = size(curve)
#         IF s(0) eq 1 THEN begin
#          dummy = curve
#          dummy = smooth(dummy(*),3)
#          maxVal = MAX(dummy(10:19))
#          index = WHERE(dummy(10:19) eq maxVal)
#          result = TOTAL(curve(index(0)+8:index(0)+17))  ; ARNOs best, set frames accordingly
#         endif else begin
#          dummy = curve(0,0,*)
#          dummy = smooth(dummy(*),3)
#          maxVal = MAX(dummy(10:19))
#          index = WHERE(dummy(10:19) eq maxVal)
#          result = TOTAL(curve(0,0,index(0)+8:index(0)+17))  ; ARNOs best, set frames accordingly
#         endelse
#       end
#    4  : begin ;gets the maximum between firstFrame and lastFrame (control window), then integral of MAX-2 to MAX+8
#         s = size(curve)
#         if firstframe lt 2 then firstframe = 2
#         IF s(0) eq 1 THEN begin
#          dummy = curve
#          dummy = smooth(dummy(*),3)
#          maxVal = MAX(dummy(firstFrame:lastFrame))
#          index = WHERE(dummy(firstFrame:lastFrame) eq maxVal)
#          result = TOTAL(curve(index(0)+firstFrame-2:index(0)+firstFrame+7))  ; ARNOs best, set frames accordingly
#         endif else begin
#          dummy = curve(0,0,*)
#          dummy = smooth(dummy(*),3)
#          maxVal = MAX(dummy(firstFrame:lastFrame))
#          index = WHERE(dummy(firstFrame:lastFrame) eq maxVal)
#          result = TOTAL(curve(0,0,index(0)+firstFrame-2:index(0)+firstFrame+7))  ; ARNOs best, set frames accordingly
#         endelse
#       end
#    5  : begin ;gets the maximum between p1.stimulus_on and p1.stimulus_on+10 (control window), then integral of MAX-2 to MAX+8
#         s = size(curve)
#         IF s(0) eq 1 THEN begin
#          dummy = curve
#          dummy = smooth(dummy(*),3)
#          maxVal = MAX(dummy( p1.stimulus_on: p1.stimulus_on+10))
#          index = WHERE(dummy( p1.stimulus_on: p1.stimulus_on+10) eq maxVal)
#          result = TOTAL(curve(index(0)+ p1.stimulus_on-2:index(0)+ p1.stimulus_on+7))  ; ARNOs best, set frames accordingly
#         endif else begin
#          dummy = curve(0,0,*)
#          dummy = smooth(dummy(*),3)
#          maxVal = MAX(dummy( p1.stimulus_on: p1.stimulus_on+10))
#          index = WHERE(dummy( p1.stimulus_on: p1.stimulus_on+10) eq maxVal)
#          result = TOTAL(curve(0,0,index(0)+ p1.stimulus_on-2:index(0)+ p1.stimulus_on+7))  ; ARNOs best, set frames accordingly
#         endelse
#       end
#    10  :   result = MIN(curve(28:45))
#    11  :   result = MAX(curve(10:19))
#    12  :         result = TOTAL(curve(firstFrame:lastFrame))  ;total between values in control window
#    13  :      result = TOTAL(curve(p1.stimulus_on+1:p1.stimulus_on+10))
#    14  :      result = (TOTAL(curve(p1.stimulus_on+1:p1.stimulus_on+6)))-(TOTAL(curve(p1.stimulus_on-3:p1.stimulus_on-1)))-(TOTAL(curve(p1.stimulus_on+8:p1.stimulus_on+10)))
#       ;14: contrast of 6 frames right after stimulus against 3 frames before and 3 frames after
#    15 :      result =  MAX(curve(firstFrame:lastFrame))
#    16 :     result =     MAX(curve(firstFrame:lastFrame)) - MEAN(curve(firstframe-3:firstframe))
#    17 :     result =     MAX(median(curve(firstFrame:lastFrame),3)) - MEAN(curve(firstframe-3:firstframe))
#    20  :      result = (curve(lastframe)) - (curve(firstframe))
#    21  :      result = (TOTAL(curve(p1.stimulus_on+2:p1.stimulus_on+4)) - TOTAL(curve(p1.stimulus_on-3:p1.stimulus_on-1)))/3
    elif (CTVmethod == 22):
        result = np.sum(curve[flag.CTV_lastframe-1:flag.CTV_lastframe+2]) - np.sum(curve[flag.CTV_firstframe-1:flag.CTV_firstframe+2])#  lastframe - firstframe
#    22  :      result = (TOTAL(curve(lastframe-1:lastframe+1)) - TOTAL(curve(firstframe-1:firstframe+1)))/3
    elif (CTVmethod == 23):
        result = np.sum(curve[p1.metadata.stimulus_on+2:round(p1.metadata.stimulus_on+3*p1.frequency)]) - np.sum(curve[round(p1.metadata.stimulus_on-3*p1.frequency):p1.metadata.stimulus_on-1])#  lastframe - firstframe
#    23  :      result = (TOTAL(curve(p1.stimulus_on+2:p1.stimulus_on+3*p1.frequency)) - TOTAL(curve(p1.stimulus_on-3*p1.frequency:p1.stimulus_on-1)))/(3*p1.frequency)
#;24: mean of 3 frames 1 sec after stimOnset, - mean of 3 frames before stimOnset
#    24  :      result = (TOTAL(curve(p1.stimulus_on+p1.frequency-1:p1.stimulus_on+p1.frequency+1)) - TOTAL(curve(p1.stimulus_on-3:p1.stimulus_on-1)))/3
#    25  :      result = TOTAL(curve(lastframe-1:lastframe+1))/3 - TOTAL(curve(firstframe-7:firstframe+1))/9;paul, Mai 2001
#    26  :      result = TOTAL(curve(lastframe:lastframe+14))/15 - TOTAL(curve(firstframe:firstframe+4))/5;paul, 11.12.01
#    27  :      result = TOTAL(curve(lastframe:lastframe+2))/3 - TOTAL(curve(firstframe:firstframe+4))/5;paul, 11.12.01
#
#
#
#
#    30 :       result = MAX(curve(10:30))- MIN(curve(5:15))  ;
#    31 :       result = MAX(curve(12:32))- MIN(curve(7:17))  ;
#    32 :       result = MAX(curve(20:30))- MIN(curve(10:25))  ;
#    33 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+10))- MIN(curve(p1.stimulus_on-5:p1.stimulus_on))  ;
#    ;34: max of 3 secs after stimulus - min of 2 secs before stimulus.
#    34 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency))- MIN(curve(p1.stimulus_on-2*p1.frequency:p1.stimulus_on))  ;
#    ;35: max of 3 secs after stimulus - mean of 3 frames before stimulus.
#    ;35 with t-test for significance, see 135/136
#    35 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency))- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
    elif (CTVmethod == 35):
        result = np.max(curve[p1.stimulus_on:round(p1.stimulus_on+3*p1.frequency)]) - np.mean(curve[p1.stimulus_on-2:p1.stimulus_on-1])#  lastframe - firstframe
#    62 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+2*p1.frequency))- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
#    64 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+4*p1.frequency))- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
#    66 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+6*p1.frequency))- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
#    68 :       result = MAX(curve(p1.stimulus_on:p1.stimulus_on+8*p1.frequency))- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
#
#
#    36 :      begin
#          print,'Method 36 uses global maximum - use Overview Method 10 for it please or change to 35'
#          result = 0
#            end
#    ;37: max of frames 2-5, minus mean 0-1, Daniela 2002.
#    37 :       result = MAX(curve(2:5))- Mean(curve(0:1))  ;
#    38 :      begin
#          print,'Method 38 uses global maximum - use Overview Method 10 for it please or change to CTV=37'
#          result = 0
#            end
#
#    45 : begin ;gets the maximum between p1.stimulus_on and p1.stimulus_on+10 (control window), then integral of MAX-2 to MAX+8
#         ;but resets curve to 0 in the interval p1.stimulus_on-2 to p1.stimulus_on-1
#         s = size(curve)
#         IF s(0) eq 1 THEN begin
#          dummy = curve
#          dummy = smooth(dummy(*),3)
#          shiftZero = 5 * total(dummy[p1.stimulus_on-2:p1.stimulus_on-1])
#          maxVal = MAX(dummy( p1.stimulus_on: p1.stimulus_on+10))
#          index = WHERE(dummy( p1.stimulus_on: p1.stimulus_on+10) eq maxVal)
#          result = TOTAL(curve(index(0)+ p1.stimulus_on-2:index(0)+ p1.stimulus_on+7))  - shiftZero
#         endif else begin
#          dummy = curve(0,0,*)
#          dummy = smooth(dummy(*),3)
#          shiftZero = 5 * total(dummy[p1.stimulus_on-2:p1.stimulus_on-1])
#          maxVal = MAX(dummy( p1.stimulus_on: p1.stimulus_on+10))
#          index = WHERE(dummy( p1.stimulus_on: p1.stimulus_on+10) eq maxVal)
#          result = TOTAL(curve(0,0,index(0)+ p1.stimulus_on-2:index(0)+ p1.stimulus_on+7)) - shiftZero  ; ARNOs best, set frames accordingly
#         endelse
#       end
#
#    51 :     result = MAX(deriv(curve(5:20)))  ;maximum of derivative
#    52 :     result = MAX(deriv(curve(p1.stimulus_on:p1.stimulus_end+p1.frequency)))  ;maximum of derivative
#
#    ;calculation using the timing
#    61  :      begin ;take the stimulus time, - the same time before stimulus
#          result = (TOTAL(curve(p1.stimulus_on:p1.stimulus_end)) - TOTAL(curve(2*p1.stimulus_on-p1.stimulus_end:p1.stimulus_on-1)))$
#                 /(p1.stimulus_end - p1.stimulus_on)
#         end
#
#    100 :      result  = (total(curve(4:8))/5)-(total(curve(0:2))/3)
#
#    101 : begin
#       ;calculate maximum during stimulus
#       ;then calculate half-maximum width after stimulus onset (Silke, 11/2001)
#       noise = 4* stddev(curve((p1.stimulus_on)-7:(p1.stimulus_on)-1))
#       cutoff = max(curve(p1.stimulus_on:p1.stimulus_end))
#       if (cutoff gt noise) THEN begin
#
#         posMax = where(curve(p1.stimulus_on:p1.stimulus_end) eq cutoff) + p1.stimulus_on
#          posMax = posMax(0)
#          aboveThreshold = (curve gt (0.5*cutoff))
#          keep = 1
#          for i=posMax,(n_elements(curve)-1) do begin
#              if (aboveThreshold(i) eq 0) THEN keep = 0
#              if keep THEN aboveThreshold(0) = 1 ELSE aboveThreshold(i) = 0
#          endFOR
#          keep = 1
#          for j=0, posMax do begin
#              i = posMax - j
#              if (aboveThreshold(i) eq 0) THEN keep = 0
#              if keep THEN aboveThreshold(0) = 1 ELSE aboveThreshold(i) = 0
#          endFOR
#       result = total(aboveThreshold) / p1.frequency
#
#       endif ELSE begin
#         result=0
#       endelse
#       end
#
#    103 : begin
#       ;calculate time to half height of maximum
#       noise = 4* stddev(curve((p1.stimulus_on)-7:(p1.stimulus_on)-1))
#       cutoff = max(curve(p1.stimulus_on:p1.stimulus_end+p1.frequency*2))
#       if (cutoff gt noise) THEN begin
#         posHalfHeight = where(curve(p1.stimulus_on:p1.stimulus_end+p1.frequency*2) ge cutoff/2.0)
#         result = posHalfHeight(0)/p1.frequency
#       endif ELSE begin
#         result=0
#       endelse
#    end
#
#    ;gets the 3 seconds after stimulus, and the 3 seconds before stimulus, makes a rank-sum-test (Mann-Whitney U test)
#    ;if the test is positive, returns CTV35, else 0
#    ;ignore first frame
#    135 : begin
#         significancelevel = 0.05
#         after       = curve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency)
#         before      = curve(MAX([p1.stimulus_on-3*p1.frequency,1]):p1.stimulus_on)
#         equalMean     = tm_test(after,before) ; equalMean is a two element array, with z-statistic and p-value
#         IF (equalMean(1) gt significancelevel) THEN begin
#           result = 0
#         endIF else begin
#               result = MAX(after)- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
#            endelse
#            ;print, result, equalMean
#            ;plot, after
#            ;oplot, before
#            ;oplot, before
#        end
#    136 : begin
#         significancelevel = 0.01
#         after       = curve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency)
#         before      = curve(MAX([p1.stimulus_on-3*p1.frequency,1]):p1.stimulus_on)
#         equalMean     = tm_test(after,before) ; equalMean is a two element array, with z-statistic and p-value
#         IF (equalMean(1) gt significancelevel) THEN begin
#           result = 0
#         endIF else begin
#               result = MAX(after)- Mean(curve(p1.stimulus_on-2:p1.stimulus_on))  ;
#            endelse
#            ;print, result, equalMean
#            ;plot, after
#            ;oplot, before
#            ;oplot, before
#        end
#
#    145 : begin ;gets the maximum between p1.stimulus_on and p1.stimulus_on+10 (control window), then integral of MAX-2 to MAX+8
#         ;but resets curve to 0 in the interval p1.stimulus_on-2 to p1.stimulus_on-1
#         ;only values above 0
#         s = size(curve)
#         IF s(0) eq 1 THEN begin
#          dummy = curve
#          dummy = smooth(dummy(*),3)
#          shiftZero = 5 * total(dummy[p1.stimulus_on-2:p1.stimulus_on-1])
#          maxVal = MAX(dummy( p1.stimulus_on: p1.stimulus_on+10))
#          index = WHERE(dummy( p1.stimulus_on: p1.stimulus_on+10) eq maxVal)
#          result = (TOTAL(curve(index(0)+ p1.stimulus_on-2:index(0)+ p1.stimulus_on+7))  - shiftZero)>0
#         endif else begin
#          dummy = curve(0,0,*)
#          dummy = smooth(dummy(*),3)
#          shiftZero = 5 * total(dummy[p1.stimulus_on-2:p1.stimulus_on-1])
#          maxVal = MAX(dummy( p1.stimulus_on: p1.stimulus_on+10))
#          index = WHERE(dummy( p1.stimulus_on: p1.stimulus_on+10) eq maxVal)
#          result = (TOTAL(curve(0,0,index(0)+ p1.stimulus_on-2:index(0)+ p1.stimulus_on+7)) - shiftZero)>0
#         endelse
#       end
#
#        161  :          result = curve(2) - 0.5 * total(curve(0:1)) ;short, Daniela, 2002
#    162  :          result = curve(3) - 0.5 * total(curve(0:1))
#    163  :       result = curve(4) - 0.5 * total(curve(0:1))
#    164  :       result = curve(5) - 0.5 * total(curve(0:1))
#    165  :      result = curve(3) - total(curve(0:2))/3.0   ;short, Ana, 2002
#    166  :      result = curve(4) - total(curve(0:2))/3.0
#    167  :      result = curve(5) - total(curve(0:2))/3.0
#
#
#
#    ;values of 200+ for processing of raw data
#    240 : begin ;gets the maximum between p1.stimulus_on and p1.stimulus_on+10 (control window), then integral of MAX-2 to MAX+8
#         ;maximum after stimulus is MAX(curve(p1.stimulus_on:p1.stimulus_on+10))
#         ;minimum at stimulus is    MIN(curve(p1.stimulus_on-2:p1.stimulus_on+2))
#         ;total before stimulus   TOTAL(curve(p1.stimulus_on-6:p1.stimulus_on))
#         ;(TOTAL-MIN) is an estimate for the ongoing bleaching 3 frames long
#         ;(MAX - MIN) is the deltaF
#         ;deltaF/F is therefore ((TOTAL-MIN)+(MAX-MIN))/MIN, simplify, get
#         result = (TOTAL(curve(p1.stimulus_on-6:p1.stimulus_on)) + MAX(curve(p1.stimulus_on:p1.stimulus_on+10))) $
#                   /MIN(curve(p1.stimulus_on-2:p1.stimulus_on+2))
#       end
#    300: result = mean(curve) ;useful for simulated photographs
#    301: result = total(curve(5:10)) ; useful for simulated photographs, less susceptible to movement
#    302: result = mean(curve(5:10)) ; useful for simulated photographs, less susceptible to movement
#    322: result = TOTAL(curve(lastframe-1:lastframe+1)) /3
#    335 : result = MAX(curve(p1.stimulus_on:p1.stimulus_on+3*p1.frequency))
#
#
#;the family of 500 is for function fitting, e.g. stetter_curve fit
#
#
#
#    900: result = MAX(curve[p1.stimulus_on:p1.stimulus_on+10])- (TOTAL(curve[firstframe-1:firstframe+1])/3)
#    901: begin
#       pos=where(curve[p1.stimulus_on:p1.stimulus_on+10] eq MAX(curve[p1.stimulus_on:p1.stimulus_on+10]))
#       result = (TOTAL(curve[pos[0]+p1.stimulus_on-1:pos[0]+p1.stimulus_on+1])/3) - (TOTAL(curve[firstframe-1:firstframe+1])/3)
#       end
    else:
        print('VieOverview.CurveToValue method not implemented yet')
    return result
#end ; curvetovalue


def ShowOverviews(p1, flag):
    '''
    Translation of IDL program ShowOverview, which is called in the interactive view window 
    to show a false color coded image of the data.
    All settings are taking from flag - unlike the IDL original, which was more protected.
    
    The overview shown here is NOT the same as the one calculated in the tapestry.
    for that one, call singleoverviews with localVIEW_batchmode = False.
    '''
#pro ShowOverviews, signals, firstframe, lastframe, SO_MV_scalemin, SO_MV_scalemax, filter, FilterSize, experiment, p
#;this procedure displays overview pictures for all buffers
#;Author: Jasdan 1995 / Giovanni 1997, 1998
#;common globalVars
#  common CFD ;Defined in CFD_Define
#  common CFDConst
#; Parameters:
### translate python flags into the local variables, i.e. the command line parameters in IDL
#; firstframe  beginning and end of calculation of overview
#; lastframe
#; signals:    4 dimensional array of float with calculated signals
#; SO_MV_scalemin:   minimum and maximum of y-scale
#; SO_MV_scalemax
#; filter:     filter on/off
#; filtersize
#; experiment  string with name of experiment
#; Parameterset
#    firstframe = flag.CTV_firstframe
#    lastframe = flag.CTV_lastframe
#    signals = p1.sig1
    SO_MV_scalemin = flag.SO_MV_scalemin
    SO_MV_scalemax = flag.SO_MV_scalemax
#    filter_space = 0 #
#    #TODO filter_space (which was "filter" in IDL not implemented yet,
#    #because I don't know the flag)
#    filtersize = 0
#    experiment = 'test_image'
#############end of variables in command line##
##method = fix(flag[so_method])
#    method = flag.so_Method
##subMethod = fix( flag[ctv_method])
#    subMethod = flag.CTV_Method
##setup 				= fix(flag[LE_loadExp])
#    setup = flag.LE_loadExp
##individualScale = fix(flag[so_indiScale]) MOD 10 ; more complex individual scalings not included here
#    individualScale = flag.SO_indiScale % 10
##IF (fix(flag[so_indiScale]) ge 10) THEN print, 'ShowOverviews: complex individual scaling ignored, use ',individualScale
#    if flag.SO_indiScale >= 10:
#        print('ShowOverviews: complex individual scaling ignored, use ',individualScale)
#            
#    indiScale3factor = 0.2 #; set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
#    if individualScale > 100: # then begin
#    	indiScale3factor = (individualScale-100)/100.0 #; set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
#    	individualScale = 3
##    endIF
#

    maximum = SO_MV_scalemax
    minimum = SO_MV_scalemin


##################################
# here there are many options, related to
# multiple measurements (implement then when sig1 becomes 4-dimensional!
# and to add a border (not necessary in our first, easy implementation
## and zoomfactor (since we can zoom python windows, this might not be necessary)
#############################))    
#    xgap = 10   	#	; gaps between frames, only even numbers!
#    xgap2 = xgap/2
#
#frame = fltarr(p.format_x + xgap, p.format_y)
#frame(*,*) = -1000  ; borders are black
#
#IF (p.format_x lt 100) THEN zoomfactor = 2 ELSE zoomfactor=1
#
#
#;display 'first buffer' or not?
#firstBuffer = fix(flag[LE_UseFirstBuffer])
#IF (firstBuffer lt 0) THEN begin ; guess whether to use the first buffer on the basis of the setup
#	IF setup eq 0 THEN firstBuffer = 0 ; for old setup, show also air control
#	IF setup eq 3 THEN firstBuffer = 1 ; for TILL, do not show AIR control
#	IF setup eq 4 THEN firstBuffer = 1 ; for TILL, do not show AIR control
#	IF (fix(flag[VIEW_ReportMethod]) eq 20) THEN firstBuffer = 1
#	IF (fix(flag[VIEW_ReportMethod]) eq 20) THEN lastBuffer = 1
#	; if air was subtracted for correction then leave air overview away - it is 0 !
#	;this is not really appropriate when using corrected dataset - just used for backwards compatibility
#	if (max(signals(*,*,0,0)) eq 0) and (min(signals(*,*,0,0)) eq 0) then firstbuffer = 1
#endIF
#
#
#
#
#min1 = fltARR(2)
#max1 = fltARR(2)
#;minimum =  10000
#;maximum = -10000
#
#if (individualScale eq 2) then begin ;scale to min/max of all frames, takes more time
#	for odor = firstbuffer, p.odors do begin
#	    ;overviewframe = overview( signals, odor, filter, filtersize, startframe, endframe, p, method )
#	    overviewframe = overview( odor, method)
#	    min1(0) = min(overviewframe)
#	    max1(0) = max(overviewframe)
#	    minimum = min(min1)
#	    maximum = max(max1)
#	    min1(1) = minimum
#	    max1(1) = maximum
#	endFor
#endif
#
#IF individualScale eq 0 THEN scaleString = ' ' + strcompress(string(SO_MV_scalemin)) + '/' + strcompress(string(SO_MV_scalemax)) +' '
#IF individualScale eq 1 THEN scaleString = ' i1 '
#IF individualScale eq 2 THEN scaleString = ' ' + strcompress(string(minimum)) + '/' + strcompress(string(maximum)) +' '
#IF individualScale eq 3 THEN scaleString = ' i3 '
#IF individualScale eq 4 THEN scaleString = ' i4 '
#IF individualScale eq 5 THEN scaleString = ' i5 '
#IF individualScale eq 6 THEN scaleString = ' i6 '
#IF individualScale eq 7 THEN scaleString = ' i7 '
#
#IF method eq 2 THEN borderString = ': start=' + strcompress(string(startframe+1)) + ', end=' + strcompress(string(endframe+1))  $
#			ELSE borderString = ': '
#
#Fenstertitel = localOdorText(p,1) +  borderString+scalestring + ', M=' +  strcompress(string(method)) +'/'+strcompress(subMethod)
#
#window, /free, xsize = ( (p.format_x+xgap) * zoomfactor * (p.odors+1-firstbuffer)+xgap ),  $
#	       ysize = p.format_y * zoomfactor, title = Fenstertitel

#
#;****
#for odor = firstbuffer, p.odors do begin

#python: create overview frame for this particular one
    overviewframe = overview(p1, flag, flag.SO_Method)
#    overviewframe = overview(  odor,  method )
#    ;overviewframe = overview( signals, odor, filter, filtersize, startframe, endframe, p, method )
#
#    frame(xgap2+xgap2:p.format_x+xgap2+xgap2-1, 0:p.format_y-1) = overviewframe(*,*)
#
#    frame2 = rebin(frame, (p.format_x+xgap) * zoomfactor, p.format_y * zoomfactor, sample = 1)
#
#    if (individualScale eq 1) then begin
#	    minimum = min(overviewframe)
#	    maximum = max(overviewframe)
#;	    minimum = maximum - ((maximum - minimum) / 2)	; show only top 50% of each frame
#    endif
#    if (individualScale eq 3) then begin
#	    minimum = min(overviewframe(indiScale3factor*p.format_x:p.format_x*(1-indiScale3factor),indiScale3factor*p.format_y:p.format_y*(1-indiScale3factor)))
#	    maximum = max(overviewframe(indiScale3factor*p.format_x:p.format_x*(1-indiScale3factor),indiScale3factor*p.format_y:p.format_y*(1-indiScale3factor)))
#    endif
#    if (individualScale eq 4) then begin
#    	;scale with min and max of selected region
#    	;restore the selected region
#    	restore, flag[stg_OdorMaskPath]+flag[stg_reporttag]+'.alArea'
#    	;now AL perimeter is in variable maskframe
#    	positions = where(maskframe)
#    	minimum = min(overviewframe(positions))
#    	maximum = max(overviewframe(positions))
#    endIF

    plt.imshow(overviewframe, vmin=minimum, vmax=maximum)
#
#    tv, bytscl(frame2, MIN=minimum, MAX=maximum, TOP=!d.table_size), (odor - firstbuffer)
#endfor

#; draw scalebar
#scalebarsize = p.format_y*zoomfactor
#scaleBar = INTARR(xgap2+1,scalebarsize)
#scale    = reverse(indgen(scalebarsize))
#for i=1,xgap2 do scaleBar(i,*) = scale(*)
#	IF ((minimum lt 0) and (maximum gt 0)) THEN begin ;mark 0 position
#		level = fix(scalebarsize - scalebarsize*(float(minimum)/(minimum - maximum)))
#		IF (level eq scalebarsize-1) THEN begin
#			scaleBar(*,level-1:level)=0
#		endiF ELSE begin
#			scaleBar(*,level:level+1)=0
#		endELSE
#endIF
#print, 'Showoverviews: indiscale is ',individualscale,' Method is ',method, ' Minimum&Maximum are: ',minimum, maximum
#
#tv, bytscl(scaleBar, MIN=0, MAX=p.format_y*zoomfactor, TOP=!d.table_size), 0


#end ; of program ShowOverviews


def Depracated_ExportMovie(flag, p1):
    #gio June 2019: adapted IDL program in a temporary fashion, not elegant at all
    #buffer: is what the movie should contain
    buffer = p1.sig1
# original IDL file is ExportMovie.pro in VIEWoverview
# look at that file to understand what happened - I'll be deleting most of that here soon    
# at the beginning I translated verbatim, then I started simplifying

# other variables in IDL were: bufferIN, Pixmin1, Pixmax1, filter, filtersize, p , FileText
# procedure to export movie frame by frame in PICT format , for Adobe Premiere for example
# adapted from a previous version by jasdan
# Giovanni 1999, 2000, 2001.
# export to AVI added, 2003
# conversion to Python May/june 2019

## block of common variables containing flags and data    
#common cfd
#common cfdconst
#common vars
#common data

##the common block ExporMovieFlags is defined in VIEW!
#common ExportMovieFlags
    mv_xgap = flag.mv_xgap # border of frame, total (i.e. half of this on each side)
    mv_ygap = flag.mv_ygap
#    mv_sdSignificanceCut = flag.mv_sdSignificanceCut # 0 # #NOT IMPLEMENTED#cut pixels below certain significance value, set to 0 for no significance cut

    mv_exportFormat = flag.mv_exportFormat #'mpg4' # insert codec for FFM
    mv_realTime = flag.mv_realTime # 24 # ,		NOT IMPLEMENTED	$  ; insert frames per second of the movie, 0 for no realTime, 24 for MPEG, 15 for GIF->QuickTime
#    mv_SpeedFactor = flag.mv_SpeedFactor # ,	NOT IMPLEMENTED		$ ; for exportFormat 6, increase or decrease speed of movie
    mv_reverseIt = flag.mv_reverseIt # False #,			$; turn it upside down
    mv_rotateImage = flag.mv_rotateImage #0 #,        $ ; rotate only image,  ; 0 for no action, 2 for 180 degrees
    mv_cutborder = flag.mv_cutborder# 1 #,	  		$ ; die Pixelgröße von Filtersize wird ringsherum vom Bild abgeschnitten
    mv_morphoThreshold = flag.mv_morphoThreshold # False #,	$;;1; substitutes lower range with morphological image to be taken from file
    mv_withinMask = flag.mv_withinMask # False #,#NOT IMPLEMENTED#			$;   = 0   ; limits output to within the mask in xxx.area
#    mv_sdSignificanceCut = 0 #,	$;2.0 ; cuts everything below that significance level. Stimulus is included in calculation, ignored if below 0.1. Not implemented yet
    mv_markStimulus = flag.mv_markStimulus # True #,		$ ; marks stimulus application with a red box
    mv_percentileScale = flag.mv_percentileScale # False #,	$; = 0 !!!!!!discontinued
    mv_indiScale3factor = flag.mv_indiScale3factor # 0.2 # set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
    mv_individualScale = flag.mv_individualScale # 3 # 3 and 4 implemented;,	$; = fix(flag[so_indiScale])
#mv_individualScale = fix(flag[so_indiScale])
#IF ((mv_individualScale gt 100) AND (mv_individualScale lt 200)) then begin
#	mv_indiScale3factor = (mv_individualScale-100)/100.0 ; set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
#	mv_individualScale = 3
#endIF
    mv_percentileValue = flag.mv_percentileValue # 0#NOT IMPLEMENTED# ,	$; = float(individualScale MOD 100)/100.0
    mv_correctStimulusOnset = flag.mv_correctStimulusOnset #  0 #value to be added to stimulus onset
    mv_displayTime = flag.mv_displayTime # False # #NOT IMPLEMENTED#time in ss:ms as figures
    mv_minimumBrightness = flag.mv_minimumBrightness # 0 ##NOT IMPLEMENTED# 0.4 #; creates a mask that depends on the brightnes of the foto


#;0, 1: Pixmin and Pixmax are taken
#;2 : min and maximum of sequence is taken
#;3 : min and max of central region is taken
#;4 : max of sequence is taken, min is Pixmin
#;5 : min and max from area region
#;6 : min from pixmin, max from area
#;7 : min from pixmin, max from area but only stimulus + 2*stimulus length
#
#IF ((mv_individualScale gt 1000) AND (mv_individualScale lt 2000)) then begin
#	mv_percentileValue = float(mv_individualScale MOD 100)/100.0
#	mv_percentileScale = 1
#	mv_individualScale = (mv_individualScale MOD 1000) / 100 ; 1xyy, x gives individualscale
#	mv_indiScale3factor = 0.2 ; set to 0.2 for 20 % border to be ignored when scaling usind idividualscale eq 3
#endIF
##all settings for export movie are now in the file
##SetExportMovieFlags in the ImageALLocal path
##call stored values only in interactive mode
#IF (flag[BatchMode] eq 0) THEN SetExportMovieFlags

# I assume the data was read by something like FID_in.read_pst
# format is (rows, columns, frames)    
    
    
#local flags: I collect everything here, and repeat everything later for the translation
    # later the program can be made tidy
    suppressMilliseconds = 0 #if 1 does not show milliseconds, but always shows minutes (for slow measurements)
# variables in p1
# TODO replace these temporary values with the real ones.
    print('In ViewOverview-ExportMovie: mv_individualScale not implemented yet, taking min/max of movie')
    scaleMin = np.min(buffer)
    scaleMax = np.max(buffer)

    filterSpaceFlag = flag.Signal_FilterSpaceFlag
    filterSpaceSize = flag.Signal_FilterSpaceSize 
    # in python, I use gaussian filter, therefore filterSpaceSize is sigma, not number of pixels as in my IDL code


# which file to write the movie to: 
# the filename is given in imageALlocal/localodortext
    if flag.VIEW_batchmode:
        filetext = ImageALlocal.localodortext(flag, p1)
    else: 
        filetext = 'movie' #in interactive mode movies do not have an informative name
    # not add the right directory
    outfilename = os.path.join(flag.STG_OdorReportPath, filetext)
    outfilename = outfilename + '.mp4'
    
    
    p1_stimulus_on  = p1.stimulus_on
    p1_stimulus_end = p1.stimulus_end
    p1_format_x = buffer.shape[0]
    p1_format_y = buffer.shape[1]
    p1_stimulus_ISI = p1.stimulus_ISI
    p1_frequency = p1.frequency # frames per second
    
    
    p1_frame_time = 1000.0/p1_frequency

#flags are defined in View/View.pro

#which part to show is defined by flags
#MvFirstframe = fix(flag[ft_firstframe])
#MvLastframe  = fix(flag[ft_lastframe])
#IF (MvFirstFrame eq -1) 		THEN MvFirstFrame 	= 0
#IF (MvLastFrame  eq -1)  		THEN MvLastFrame  	= p1_frames-1
#if (Mvlastframe  gt p1_frames-1)then Mvlastframe 	= p1_frames-1
    mv_FirstFrame = 0 #starting with first frame
    mv_LastFrame  = buffer.shape[2]-1 # up to last frame
    print('Exportmovie. Exporting frames ',mv_FirstFrame,' to ', mv_LastFrame,' of the original data')

    mv_drawScalebar = False
    foto1 = buffer[:,:,0] # take first frame as back foto

##get name for movie
#IF fix(flag[VIEW_batchmode]) THEN begin
#	fileText = localOdorText(p1, odor)
#endIF else begin
    fileText = 'movie'
#endELSE
#IF (VIEW_CorrSignals eq 0) THEN begin
#	buffer = sig1(*,*,Mvfirstframe:Mvlastframe,odor)
#	fileText = filetext
#endIF ELSE begin
#	buffer = sig1corr(*,*,Mvfirstframe:Mvlastframe,odor)
#	fileText = filetext + 'corr'
#endELSE

    pixMIN = scaleMin
    pixMAX = scaleMax
    filterFlag = filterSpaceFlag
    filterSize = filterSpaceSize

    temp  =  np.zeros((p1_format_x , p1_format_y ))
    #frame = fltarr(p1_format_x  + xgap, p1_format_y  + ygap)
    frame_Xsize = p1_format_x + mv_xgap + ((p1_format_x + mv_xgap) % 2)
    frame_Ysize = p1_format_y + mv_ygap + ((p1_format_y + mv_ygap) % 2)
    frame = np.zeros((frame_Xsize, frame_Ysize)) #no odd numbers for mpeg
#triple frame for mpeg
#triFrame = bytarr(3,p1_format_x +mv_xgap+(p1_format_x  MOD 2), p1_format_y +mv_ygap+(p1_format_y  MOD 2))
#get color information for tiff output
#IF fix(flag[macSystem]) THEN device, true_color = 0
#device, decomposed=0
#loadct, SO_MV_colortable
#TVLCT, R, G, B, /GET
#make values 0 and 1 black for background
#r(0) = 0
#g(0) = 0
#b(0) = 0
#set these colours also to the screen
#tvlct, r, g, b
#IF (mv_exportformat eq 3) THEN begin
#	outfilename = flag[stg_odorreportpath]  + FileText +'.mpeg'
#	myMPEG = OBJ_NEW('IDLgrMPEG', FILENAME=outfilename, scale=[2.0,2.0], FRAME_RATE=2)
#endIF
#IF (mv_exportformat eq 4) THEN outfilename = flag[stg_odorreportpath] + FileText +'.gif'
#IF (mv_exportformat eq 5) THEN outfilename = flag[stg_odorreportpath] + FileText +'.tif'
#IF (mv_exportformat eq 6) THEN outfilename = flag[stg_odorreportpath] + FileText +'.avi'


    xgap2 = int(mv_xgap/2)
    ygap2 = int(mv_ygap/2)

    noFrames = mv_LastFrame - mv_FirstFrame +1 #number of frames
    stimStart = p1_stimulus_on  - mv_FirstFrame + mv_correctStimulusOnset
    stimEnd   = p1_stimulus_end - mv_FirstFrame + mv_correctStimulusOnset


#make array of stimulus information, for repeated stimulation, values of 1 for frames with stimulus
    stimArray = np.full((noFrames), False)
    #mark first stimulus
    stimArray[stimStart:stimEnd] = True
#if it crashes here, maybe the stimulus is not part of the movie - remove label stimulus option
#mark successive stimuli
    NextEnd   = stimEnd   + p1_stimulus_ISI
    NextStart = stimStart + p1_stimulus_ISI
    if (p1_stimulus_ISI > 0):
        while (NextEnd < noFrames-1):
            stimArray[NextStart:NextEnd] = True
            NextEnd   = NextEnd   + p1_stimulus_ISI
            NextStart = NextStart + p1_stimulus_ISI
#recalculate time base
    filmFrequency = p1_frequency
    if (mv_realTime > 1):
        filmFrequency = mv_realTime
        time = (noFrames) / p1_frequency # seconds of film duration
        print('Calculated frame length in ExportMovie: ',time*1000/(noFrames),'. Reported frame length: ',p1_frame_time,'. Check consistency!')
        oldFrames = noFrames
        noFrames = int(time * mv_realTime)
#        # the following resamples using fft along the time axis
#        from scipy.signal import resample
#        buffer1 = resample(buffer, noFrames, t=None, axis=2, window=None)
        buffer = sci.zoom(buffer, (1,1,noFrames/oldFrames), mode='nearest')
        #also for stimulus
        stimArray = sci.zoom(stimArray, noFrames/oldFrames, mode='nearest')
        stimStart = int(stimStart * noFrames/oldFrames)
        stimEnd   = int(stimEnd   * noFrames/oldFrames)

        print('Saving ',noFrames,' frames for ',time,' seconds of film. Stimulus is between frames ',stimStart, stimEnd)
    if mv_displayTime:
    	timeArray = np.arange(noFrames) # findgen(noFrames)
    	timeArray = timeArray / filmFrequency
    	timeArray = timeArray - timeArray[stimStart]

##define window size. Must be even for MPEG
#window, 10, xsize=p1_format_x +mv_xgap+(p1_format_x  MOD 2), ysize=p1_format_y +mv_ygap+(p1_format_y  MOD 2)

    #go through frames to filter
    if filterSpaceFlag:
        for i in np.arange(noFrames-1):
            buffer[:,:,i] = sci.gaussian_filter(buffer[:,:,i], filterSpaceSize)
            #IDL: buffer(*,*,i) = smooth( buffer(*,*,i), filterSpaceSize, /edge)

    
    
#    #get the limit values for the false color assignment
#    if (mv_individualScale == 2): #scale to min/max of all frames
#    	if mv_percentileScale:
#    		pixMIN = percentile(buffer, mv_percentileValue)
#        	pixMAX = percentile(buffer, 1-mv_percentileValue)
#     	else:
#    		pixMin = MIN(buffer)
#    		pixMAX = MAX(buffer)


    if (mv_individualScale == 3): #scale to min/max of all frames, central region only
    		pixMIN = np.min(buffer[int(p1_format_x *mv_indiScale3factor):int(p1_format_x *(1-mv_indiScale3factor)),int(p1_format_y *mv_indiScale3factor):int(p1_format_y *(1-mv_indiScale3factor)),:])
    		pixMAX = np.max(buffer[int(p1_format_x *mv_indiScale3factor):int(p1_format_x *(1-mv_indiScale3factor)),int(p1_format_y *mv_indiScale3factor):int(p1_format_y *(1-mv_indiScale3factor)),:])    

    if (mv_individualScale == 4): #scale to max of all frames
    		pixMAX = np.max(buffer)



#if ((mv_individualScale ge 5)and(mv_individualScale le 7))  then begin
#    	#scale with min and max of selected region
#    	#restore the selected region
#    	#5: min max in region
#    	#6: min fixed, max in region
#    	#7: min fixed, max in region during and immediately after stimulus
#    	restore, flag[stg_OdorMaskPath]+flag[stg_reporttag]+'.Area'
#		#correct for unequal size array
#		dummy = bytarr(p1_format_x ,p1_format_y ) # get same size array
#		dummy(*)=0
#		xtop    = min([(size(maskframe))(1),(size(dummy))(1)] ) -1
#		ytop    = min([(size(maskframe))(2),(size(dummy))(2)] ) -1
#		dummy(0:xtop,0:ytop) = maskframe(0:xtop,0:ytop)
#		#shift maskframe
#		maskframe = shift(maskframe, p1_shiftX, p1_shiftY)
#		#now AL perimeter is in variable maskframe
#		#create 3D mask
#		dummy = buffer
#		dummy(*) = 0
#		IF (mv_individualscale eq 7) THEN begin
#			#consider time during stimulus
#			#and again the length of the stimulus
#			#i.e. with 1 sec stimulus, consider 3 secs after stimulus onset
#			length  = 2 * (stimend - stimstart)
#			countdown = 0
#			for i=0,noFrames-1  do begin
#				IF stimarray(i) THEN begin
#					dummy(*,*,i)=maskframe(*,*)
#					countDown = length
#				endIF
#				IF countDown gt 0 THEN dummy(*,*,i)=maskframe(*,*)
#				countDown = countDown - 1
#			endFOR
#		endIF else begin
#			for i=0, noFrames-1 do dummy(*,*,i)=maskframe(*,*)
#		endELSE
#    	positions = where(dummy)
#    	IF mv_percentileScale THEN begin
#    		if (mv_individualScale eq 5)  then pixmin = percentile(buffer(positions),mv_percentileValue)
#    		pixmax = percentile(buffer(positions),1-mv_percentileValue)
#    	endIF else begin
#    		if (mv_individualScale eq 5)  then pixmin = min(buffer(positions))
#    		pixmax = max(buffer(positions))
#    	endELSE
#    	#save space, free memory
#    	dummy = 0
#    	positions = 0
#endIF #indiscale 5


#get colors for border and stimulus bar
#Pixmax = float(pixMax)
#pixMin = float(pixMin) #don't ask me why IDL interprets these as integers sometime
#buffer = temporary(buffer) > PixMin
#buffer = temporary(buffer) < PixMax
    buffer = np.clip(buffer, pixMIN, pixMAX)
    valueRange = pixMAX - pixMIN
    valueStep  = valueRange/255
    redcolor   = pixMAX - valueRange/253 #
    print('Exportmovie: MAX: ', pixMAX, ' MIN: ', pixMIN)
#shift max and min so that values 0 and 255 can be set to black and white
    pixMAX = pixMAX + valueStep*2
    pixMIN = pixMIN - valueStep*2

#
##take only pixels that in the photo have reached threshold
#    if (mv_minimumBrightness > 0):
#		#get Photo
##        if RM_differentViews:
##            fotoFileName = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1_viewLabel+'.morpho.tif'
##        else:
##            fotoFileName = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.morpho.tif'
##        if existfile(fotoFileName): 
##            backfoto = read_tiff(fotoFileName) 
##        else: 
##            backfoto=foto1
#            
#        backfoto = foto1
#
#
#
#		#get positions that match criterium
#		criterium = mv_minimumBrightness*MAX(backfoto)
#  		Maskpositions = where(backfoto lt criterium) #take outside
#
#
##morphoThreshold load foto
#IF mv_morphoThreshold then begin
#    	IF fix(flag[RM_differentViews]) THEN begin
#    		fotoFileName = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+p1_viewLabel+'.morpho.tif'
#    	endIF else begin
#    		fotoFileName = flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.morpho.tif'
#    	endELSE
#    	IF existfile(fotoFileName) THEN backfoto = read_tiff(fotoFileName) ELSE backfoto=foto1
#    	backfoto = bytscl(backFoto)/2 #take only positions 0 to 127
#	#redifine color table
#	line=bindgen(128)
#	r(0:127)=line(*)*2+1
#	g(0:127)=line(*)*2+1
#	b(0:127)=line(*)*2+1
#	tvlct, r, g, b
#endIF
#
##within mask: load perimeter
#  IF mv_withinMask THEN begin
#  		#get mask into maskframe
#    	restore, flag[stg_OdorMaskPath]+flag[stg_reporttag]+'.Area'
#		#correct for unequal size array
#		dummy = bytarr(p1_format_x ,p1_format_y ) # get same size array
#		xtop    = min([(size(maskframe))(1),(size(dummy))(1)] ) -1
#		ytop    = min([(size(maskframe))(2),(size(dummy))(2)] ) -1
#		dummy(0:xtop,0:ytop) = maskframe(0:xtop,0:ytop)
#		#shift maskframe
#		maskframe = shift(maskframe, p1_shiftX, p1_shiftY)
#		#now AL perimeter is in variable maskframe
#  		Maskpositions = where(maskframe eq 0) #take outside
#  endIF


##############################################
    # from now on, I depart from IDL in this python translation
    # but, for the time being, I remain in the frame-by-frame architecture
    # but, frames are RGB and not bytes

    #save_movie_file_xyt in FID_out is this:
    #def save_movie_file_xyt(dataMtrx, lcl_flags='', fps=24, bitrate="256k", movie_filename=''):
    # so all I need is a dataMtrx, float is ok





#define 3D structure
    MovieArray3D = np.zeros((frame_Xsize, frame_Ysize, noFrames))

#now go through the individal frames of the film
#***********************************************
    for i in np.arange(noFrames):
        #delete frame, set to black
        frame = np.full((frame_Xsize, frame_Ysize), pixMIN, dtype=float)  # borders are black

#mv_cutborder now is the numbers of pixels to cut
        #copy image into frame
        if (mv_cutborder > 0):
         		frame[xgap2+mv_cutborder:p1_format_x+xgap2-mv_cutborder, ygap2+mv_cutborder:p1_format_y +ygap2-mv_cutborder] = buffer[mv_cutborder:p1_format_x -mv_cutborder, mv_cutborder:p1_format_y -mv_cutborder,i]
        else:
         		frame[xgap2:p1_format_x +xgap2, ygap2:p1_format_y +ygap2] = buffer[:,:,i]

        #f = bytscl(frame, min = Pixmin, max = Pixmax, top = !d.table_size)

#  #add background photo
#  IF mv_morphoThreshold then begin
#  		dummy = f(xgap2:p1_format_x +xgap2-1,ygap2:p1_format_y +ygap2-1)
#		index = where(dummy lt 128)
#		dummy(index) = backFoto(index)
#		f(xgap2:p1_format_x +xgap2-1,ygap2:p1_format_y +ygap2-1) = dummy(*,*)
#  endIF
#  #remove everything outside the mask
#  IF (mv_withinMask OR (mv_minimumBrightness gt 0)) THEN begin
#		dummy = f(xgap2:p1_format_x +xgap2-1,ygap2:p1_format_y +ygap2-1) # get same size array
#		IF mv_morphoThreshold THEN begin
#			dummy(Maskpositions) = backFoto(Maskpositions)
#		endIF else begin
#			dummy(Maskpositions) = 0
#		endELSE
#		f(xgap2:p1_format_x +xgap2-1,ygap2:p1_format_y +ygap2-1) = dummy(*,*)
#  endIF

#so far, its just the image without stimulus mark and time, rotate if necessary
#rotateImage = 2
#f = rotate(f,mv_rotateImage) # 0 for no action, 2 for 180 degrees

  #mark stimulus time
        if mv_markStimulus:
            border = int(mv_xgap/10)
            if stimArray[i]:
    	    #frame(0:p1_format_x +xgap-1, p1_format_y gap2-xgy+ygap2+3:p1_format_y +ygap-1) = redcolor   # duftbalken rot
    	    #frame(border:xgap2-border, (p1_format_y +ygap2-1)-(xgap2-2*border):p1_format_y +ygap2-1) = redcolor   # duftQuadrat rot
                frame[border:xgap2-border, ygap2:ygap2+xgap2-border-border+2] = pixMAX + valueStep   # duftQuadrat rot

  #mark time
#  IF (mv_displayTime) then begin #
#  IF (ygap2 lt 5) THEN begin
#  	print, '**************************** no space to display time, please increase ygap'
#  endIF else begin
#  IF i gt 0 then begin #don't display time on the first frame
#  	#timevalue for this frame
#  	timeValue = timeArray(i)
#	lessThanZero = 0
#  	IF (timeValue lt 0) then begin
#  		lessThanZero = 1
#  		timeValue = timeValue * (-1)
#  	endIF
#	numSeconds = floor(timevalue)
#	numMinutes = fix(numSeconds / 60)
#	numSeconds = numSeconds MOD 60 # seconds
#  	stringSeconds = stringZero(2,numSeconds)
#  	stringMinutes = stringZero(2,numMinutes)
#  	stringMilliSeconds = stringZero(2,floor((timevalue-floor(timevalue))*100) )
#  	IF (numMinutes ge 1) THEN begin
#		timeString = stringMinutes + ':'+ stringSeconds + ':' + stringMilliSeconds
#  	endIF else begin
#		timeString =  stringSeconds + ':' + stringMilliSeconds
#  	endElse
#  	#for slow movies, no milliseconds but always minutes
#  	IF suppressMilliseconds THEN timeString = stringMinutes + ':'+ stringSeconds
#	#now output this string to the frame
#	#IF necessary because '-' is wider than ' '
#	IF lessThanZero THEN begin
#		Text2Array, 1, p1_format_x , 1, ygap2-1, '-'+timeString, f
#	endIF else begin
#		Text2Array, 5, p1_format_x , 1, ygap2-1, ' '+timeString, f
#	endElse
#  endIF#not first frame
#  endELSE# ygap
#  endIF#displaytime



        if mv_reverseIt:
            frame = frame[:,::-1]  # reverse(f,2)			# turn it upside down
      #IF (NOT fix(flag[batchMode])) THEN tv, f
        MovieArray3D[:,:,i] = frame

    print('Saving file.... ', outfilename)
    # now use ffmpeg routine 
    save_movie_file_xyt(MovieArray3D,  fps=24, bitrate="256k", movie_filename=outfilename)


def ExportMovie(flag, p1):
    # gio June 2019: adapted IDL program in a temporary fashion, not elegant at all
    # original IDL file is ExportMovie.pro in VIEWoverview
    # streamlined version with less IDL clutter
    # refer to Deprecated_ExportMovie for a cluttered version that would explain the history
    
    
    # filename to write to
    # the filename is given in imageALlocal/localodortext
    if flag.VIEW_batchmode:
        filetext = ImageALlocal.localodortext(flag, p1)
    else: 
        filetext = 'movie' #in interactive mode movies do not have an informative name
    # now add the right directory
    outfilename = os.path.join(flag.STG_OdorReportPath, filetext)
    outfilename = outfilename + '.mp4'

    #Aug 2019: we have removed flag.FT_FirstFrame, replaced by flag.mv_FirstFrame
    #so, new yml files will not have FT_FirstFrame, and we have to check for it
    if "FT_FirstFrame" not in flag:
        flag.FT_FirstFrame = flag.mv_FirstFrame
    if "FT_LastFrame" not in flag:
        flag.FT_LastFrame = flag.mv_LastFrame  
    
    # select movie range
    # TODO implement the possibility of a subselection of frames
    # needs new flag values mv_firstframe and mv_lastframe
    # defined ad hoc here
    
    mv_FirstFrame = np.min((flag.FT_FirstFrame, p1.metadata.frames)) #avoid first frames after last movie frame
    if flag.FT_FirstFrame == -1:
        mv_FirstFrame = 0 #starting with first frame
    mv_LastFrame = np.max((flag.FT_LastFrame, 0)) #avoid negative last frames
    if flag.FT_LastFrame == -1:
        mv_LastFrame = p1.metadata.frames #ending with last frame
        print('Exportmovie. Exporting frames ',mv_FirstFrame,' to ', mv_LastFrame,' of the original data')
    noFrames = mv_LastFrame-mv_FirstFrame #number of frames

# select 3D array x,y,z for movie
#TODO include cutborder here
    buffer_center = p1.sig1.copy()[:,:,mv_FirstFrame:mv_FirstFrame+noFrames]

#TODO flag.mv_realtime
            # this is necessary if display time changes
            # may need recalculation of frames
            # and as a consequence also of time axis (values)
            # and of stimulus array

#apply filter
    if flag.Signal_FilterSpaceFlag:
        for i in np.arange(noFrames-1):
            buffer_center[:,:,i] = sci.gaussian_filter(buffer_center[:,:,i], flag.Signal_FilterSpaceSize)
#TODO apply time filter

# SCALING
    #if flag.mv_individualScale == 0: 
        #manually set scale - default
    PIXmin = flag.SO_MV_scalemin
    PIXmax = flag.SO_MV_scalemax
    if flag.mv_individualScale == 2:
        #min/max of entire movie (only the frames to be displayed)
        PIXmin = np.min(p1.sig1[:,:,mv_FirstFrame:mv_FirstFrame+noFrames])
        PIXmax = np.max(p1.sig1[:,:,mv_FirstFrame:mv_FirstFrame+noFrames])
    if flag.mv_individualScale == 3:
        #min/max of central area of movie (only the frames to be displayed). 'center' defined by mv_indiScale3factor
        xborder = int(p1.metadata.format_x * flag.mv_indiScale3factor)
        yborder = int(p1.metadata.format_y * flag.mv_indiScale3factor)
        PIXmin = np.min(p1.sig1[xborder:-xborder, yborder:-yborder, mv_FirstFrame:mv_FirstFrame+noFrames])
        PIXmax = np.max(p1.sig1[xborder:-xborder, yborder:-yborder, mv_FirstFrame:mv_FirstFrame+noFrames])
#TODO implement other scaling options, in particular within .area file    

# apply scaling, creating new buffer
    buffer_center = np.clip(buffer_center, PIXmin, PIXmax)
        
# in a 8 bit world, I need a value one step below, and one step above, for labels/borders/writings etc.
# if python does not 8bit mapping, this needs to be changed        
    bottomValue = PIXmin - (PIXmax-PIXmin)/256
    topValue    = PIXmax + (PIXmax-PIXmin)/256




    # create movie array
    # size of x/y, plus the border defined by mv_xgap and mv_ygap
    frame_Xsize = p1.metadata.format_x + flag.mv_xgap + ((p1.metadata.format_x + flag.mv_xgap) % 2)
    frame_Ysize = p1.metadata.format_y + flag.mv_ygap + ((p1.metadata.format_y + flag.mv_ygap) % 2)
# the border is filled woth bottomValue in order to have a black border (with the appropriate color scale)
    buffer = np.full((frame_Xsize, frame_Ysize, noFrames),bottomValue) #no odd numbers for mpeg
    # dependent variables
    xgap2 = int(flag.mv_xgap/2) #border is half size on each side
    ygap2 = int(flag.mv_ygap/2)
    #buffer: is what the data for the movie, format x,y,t
    buffer[xgap2:xgap2+p1.metadata.format_x, ygap2:ygap2+p1.metadata.format_y, :] = buffer_center
    del(buffer_center) #free memory space


# buffer now contains the movie WITH border,
# so now comes the part that uses the border, such as adding time and stimulus
    



### Mark stimulus frames
#make array of stimulus information, True for time points with stimulus
    stimArray = np.full((noFrames), False)
# second stimulus, if present
    stimStart = p1.stim2ON  - mv_FirstFrame + flag.mv_correctStimulusOnset
    stimEnd   = p1.stim2OFF - mv_FirstFrame + flag.mv_correctStimulusOnset
    stimArray[stimStart:stimEnd] = True
# mark first stimulus. I treat this second, because it is the reference for stimulus_ISI below
    stimStart = p1.stimulus_on  - mv_FirstFrame + flag.mv_correctStimulusOnset
    stimEnd   = p1.stimulus_end - mv_FirstFrame + flag.mv_correctStimulusOnset
    stimArray[stimStart:stimEnd] = True
#if it crashes here, maybe the stimulus is not part of the movie - remove label stimulus option
#mark successive stimuli, for repeated stimuli
    if (p1.stimulus_ISI > 0): # repetitive stimuli. Limited number not implemented yet
        NextStart = stimStart + p1.stimulus_ISI
        NextEnd   = stimEnd   + p1.stimulus_ISI
        while (NextEnd < noFrames-1):
            stimArray[NextStart:NextEnd] = True
            NextStart = NextStart + p1.stimulus_ISI
            NextEnd   = NextEnd   + p1.stimulus_ISI
# now stimArray contains all frames with stimulus
    if flag.mv_markStimulus:
        border = int(flag.mv_xgap/10)
        for i in np.arange(noFrames-1):
            if stimArray[i]:
                buffer[border:xgap2-border, ygap2:(2 * ygap2 - 2 * border), i] = topValue

#TODO display time values (minutes:seconds:milliseconds)
    # with the option to drop minutes, or to drop milliseconds
    # I had a local flag 'suppressmilliseconds'
    if flag.mv_displayTime: #calculate array for time values
    	timeArray = np.arange(noFrames) # findgen(noFrames)
    	timeArray = timeArray / p1.frequency
    	timeArray = timeArray - timeArray[stimStart] 
        # time is always 0 at the start of the first stimulus
#        for i in np.arange(noFrames-1):
            #draw time letters into frame

    print('Saving file.... ', outfilename)
    # now use ffmpeg routine 
    save_movie_file_xyt(buffer,  fps=24, bitrate="1024k", movie_filename=outfilename)

