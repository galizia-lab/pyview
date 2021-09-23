# -*- coding: utf-8 -*-
"""
Created on Thu May 31 17:34:29 2018

@author: Giovanni Galizia
"""

import pandas as pd
import scipy  as sp
from scipy import ndimage
import numpy  as np
import matplotlib.pyplot as plt
import os

from view.python_core.p1_class.filters import apply_filter
from view.python_core.paths import get_existing_raw_data_filename
from view.python_core.io import read_tif_2Dor3D
import tifffile
import pathlib as pl
import logging


def load_pst(filename):
    """ 
    read tillvision based .pst files as uint16. 
    """
    # filename can have an extension (e.g. .pst), or not
    # reading stack size from inf
    #inf_path = os.path.splitext(filename)[0] + '.inf'
    #this does not work for /data/030725bR.pst\\dbb10F, remove extension by hand, 
    #assuming it is exactly 3 elements
    if filename[-4] == '.':
        filename = filename[:-4] #reomove extension
    meta = {}
    with open(filename+'.inf','r') as fh:
    #    fh.next()
        for line in fh.readlines():
            try:
                k,v = line.strip().split('=')
                meta[k] = v
            except:
                pass  
    # reading stack from pst
    shape = sp.int32((meta['Width'],meta['Height'],meta['Frames']))

    expected_units = np.prod(shape)

    assert pl.Path(f"{filename}.pst").stat().st_size >= 2 * expected_units, \
        f"Expected atleast {2 * expected_units} bytes in {filename}.pst. Found {pl.Path(filename).stat().st_size}"

    raw   = sp.fromfile(filename+'.pst', dtype='int16', count=expected_units)
    data  = sp.reshape(raw,shape,order='F')

    # was swapping x, y axes; commented out to retain original order
    # data  = data.swapaxes(0,1)

    # data is upside down as compared to what we see in TillVision
    data  = np.flip(data, axis=1)
    data  = data.astype('uint16')
    return data


def read_lsm(path):

   """ takes a path to a lsm file, reads the file with the tifffile lib and
   returns a np array
   """
   data = tifffile.imread(path)
   Data_cut = data[0,0,:,:,:] # empirical ...
   Data_cut_rot = sp.swapaxes(Data_cut,0,2)
   Data_cut_rot_flip = sp.flip(Data_cut_rot, axis=1)

   return Data_cut_rot_flip


def loadTILL(flag, p1):
    filename = get_existing_raw_data_filename(flags=flag, p1_metadata=p1, extension=".pst")
    #if not exist try FID format version oct18
    # if still not exist try FID format old
    print('ViewLoadData.loadTILL. Loading data :',filename)
    # write data directly into p1 structure: p1.Raw1
    p1["raw1"] = load_pst(filename.rstrip(".pst"))

    # saving the complete filename of raw data for reference
    p1["full_raw_data_path"] = filename

    # use shrinkfactor to shrink
    if (flag["LE_ShrinkFaktor"] not in [0,1]): #both 0 and 1 mean 'no shrink'
        shrink = 1/flag["LE_ShrinkFaktor"] # flag of 2 means half the size in each dimension
        import scipy.ndimage as scind
        # the command used in IDL for shrink was REBIN
        #raw1(*,*,i,1) = rebin(image(0:p1.format_x*shrinkFactor-1, 0:p1.format_y*shrinkFactor-1) ,p1.format_x, p1.format_y) ;
        # the following shrinks in x and y, not in t, with polinomial order 1.
        # "nearest" is for treatment at the borders
        p1.raw1 = scind.zoom(p1.raw1,(shrink,shrink,1), order=1, mode='nearest')
    # put shape into p structure
    datasize = p1.raw1.shape
    p1.format_x = datasize[0]
    p1.format_y = datasize[1]
    p1.frames   = datasize[2]

    # IDL:	MedianCorrection, oneOdour, fix(flag(csm_median)); mean filter added in pyVIEW
    # apply median filter first, then mean filter, depending on flags
    p1.raw1 = apply_filter(matrix_in=p1.raw1, view_flags=flag, filter_type="median")
    p1.raw1 = apply_filter(matrix_in=p1.raw1, view_flags=flag, filter_type="mean")

    # calculate foto
    p1.foto1 = p1.raw1[:,:,1:6].mean(axis = 2) #average of frames 1:6 p1.raw1[:,:,1:6]
    # IDL: 			foto1(i,j) = mean(raw1(i,j,1:5,0))
    #
    # calculate darkfoto: deprecated
    #

    if (flag["LE_AskForAir"] != 0):
        print('ViewLoadData.loadTILL. Loading Air not implemented yet')
        # use gettillloginfo to get the info for p1.control
        # load that measurement p_air["raw1"] = load_pst(filename)
        # check that shape is equal
    #
    return p1 #p1 contains all data for this measurement


def loadFURA(flag, p1):
    # loads FURA measurements
    # here I deviate from IDL. I just call loadTILL two times (in IDL, that code was effectively duplicated)
    # but I play around with the p1 structure.
    p2 = p1.copy() # use p2 for the second wavelength.
    p2.dbb1 = p2.dbb2 # BUT loadTILL does not know, so swap the dbb info
    # load wavelength 1
    p1 = loadTILL(flag, p1)
    # load wavelength 2
    p2 = loadTILL(flag, p2)
    # copy data of wavelength 2 into 1, since they belong together
    p1["raw2"]  = p2.raw1
    p1["foto2"] = p2.foto1
    if (flag["LE_AskForAir"] != 0):
        print('ViewLoadData.loadFURA. Loading Air not implemented yet')
        # in fact, it was never implemented in IDL either
    return p1 #p1 contains all data for this measurement


def loadZeiss(flag, p1):
    filename = get_existing_raw_data_filename(flags=flag, p1_metadata=p1, extension=".lsm")
    print('ViewLoadData.loadZeiss: Loading data :',filename)

    #;load zeiss data set
    print('loadZeiss: loading Zeiss dataset ', filename)
    dataIn = read_lsm(filename)

    #;define data sets for IDL-View
    p1.raw1 = dataIn #;for old empty air format

    # saving the complete filename of raw data for reference
    p1["full_raw_data_path"] = filename

    datasize = p1.raw1.shape
    p1.format_x = datasize[0]
    p1.format_y = datasize[1]
    p1.frames = datasize[2]

    #;median correction
    p1.raw1 = MedianCorrection(p1.raw1, flag)

    # ;define foto as the mean of the first six frames
    p1.foto1 = p1.raw1[:, :, 1:6].mean(axis=2)

    print('loadZeiss: data loaded')
    return p1 #loadZeiss


def load_VIEW_tif(flag, p1):

    filename = get_existing_raw_data_filename(flags=flag, p1_metadata=p1, extension=".tif")
    logging.getLogger("VIEW").info(f"Loading VIEW-tif from: {filename}")

    try:
        p1.raw1 = read_tif_2Dor3D(filename)
    except Exception as e:
        raise IOError(f"Error reading {filename}")

    # saving the complete filename of raw data for reference
    p1["full_raw_data_path"] = filename

    datasize = p1.raw1.shape
    assert len(datasize) == 3, \
        f"{filename} cannot be loaded as a VIEW-tif as it has {len(datasize)} dimensions (3 expected)"
    p1.format_x = datasize[0]
    p1.format_y = datasize[1]
    p1.frames = datasize[2]

    # ;median correction
    p1.raw1 = MedianCorrection(p1.raw1, flag)

    # ;define foto as the mean of the first six frames
    p1.foto1 = p1.raw1[:, :, 1:6].mean(axis=2)

    return p1


def create_raw_data667(p1_metadata, peaksignal):
    '''
    'this is the backup copy of the old create_raw_data666, that contained only square glomeruli
    '''
    print('ViewLoadData/LoadRaw667: generating test data with many fixed settings!')
    stimonset = p1_metadata.stimulus_on
    stimoffset = p1_metadata.stimulus_end
    ### for playing around start after #:
    # peaksignal, stimonset, stimoffset = 10, 25, 35 # - is in command line now
    # local flags
    lightlevel = 1000  # baseline value of each pixel.
    # at the setup, you would set exposure time and light level accordingly
    randomseed = 0  # set to None for irreproducible random numbers
    # add chipnoise
    darknoise = True
    darknoise_mean = 100  # mean of background values in the chip
    darknoise_amplitude = 20  # max amplitude of background chip noise
    # I assume chip noise to be random over time
    #
    xSize, ySize, tSize = 172, 130, 80  # 120, 99, 80
    rampwidth = 10  # width of the ramp, left 3x, right 2x
    stepsize = 13  # must be a divisor of ySze

    # glomerular locations are (make sure to exclude rampwidth)
    glo1 = (50, 70, 50, 70)  # x,x - y,y
    glo2 = (60, 80, 60, 80)  # x,x - y,y
    glo3 = (65, 75, 45, 55)
    glo4 = (70, 90, 30, 50)
    glo5 = (50, 65, 30, 45)
    glo6 = (70, 90, 50, 70)  # off response
    glo7 = (50, 70, 90, 110)  # biphasic response
    glo8 = (75, 95, 90, 110)  # negative response

    shotnoise = True  # add photon noise

    # add bad pixels on the CCD chip, i.e. pixels with value 0
    badpixels = True
    badpixels_clip = 0.98  # 0.9 for 10% bad pixels
    #

    # add global bleaching
    bleach = True
    bleach_percent = 10  # percentage bleaching
    bleach_tau = tSize / 5  # assume decay to 37% of percentage over this length

    # add lamp noise
    lampnoise = 0.1  # value in percent. 0 for no noise. Value is PEAK noise

    # add scattered light
    scatterlight = 0  # 2 # unit is gaussian pixels; 0 for no scattered light

    # change code, do exclude lateral step image

    # TODO
    # - add light scatter (smooth): modify
    # - add movement
    #
    def applytimecourse(matrix, glo_location, oneline):
        '''
        applies oneline as a factor (length: tSize)
        to square window (glomerulus) defined with upperleft, lowerright
        glo_location is (x_left,x_right,y_down, y_up)
        (y_down < y_up; but safety net included)
        '''
        x1 = np.min((glo_location[0], glo_location[1]))
        x2 = np.max((glo_location[0], glo_location[1]))
        y1 = np.min((glo_location[2], glo_location[2]))
        y2 = np.max((glo_location[3], glo_location[3]))
        matrix[x1:x2, y1:y2, :] = matrix[x1:x2, y1:y2, :] * oneline.reshape(1, 1, tSize)
        return matrix

    # set random numbers
    np.random.seed(randomseed)
    # create still image
    # with average light level as visible to the experimenter
    # therefore subtract darknoise_mean from lightlevel
    stillimage = np.full((xSize, ySize), (lightlevel - darknoise_mean))
    # create a ramp from 0 to 2*lightlevel
    oneline = np.linspace(0, 2 * lightlevel, ySize).reshape(1, ySize)
    stillimage[0:rampwidth, :] = oneline  # first band, going up
    stillimage[rampwidth:2 * rampwidth, :] = np.flip(oneline)  # first band, going up
    # create a ramp in the center, in order to avoid border effects
    oneline = np.linspace(0, 2 * lightlevel, ySize // 2).reshape(1, ySize // 2)
    stillimage[2 * rampwidth:np.int(2.5 * rampwidth),
    ySize // 4:ySize // 4 + ySize // 2] = oneline  # first band, going up
    stillimage[np.int(2.5 * rampwidth):3 * rampwidth, ySize // 4:ySize // 4 + ySize // 2] = np.flip(
        oneline)  # first band, going up

    # create a bit of a photo:.
    # background is darker
    stillimage[3 * rampwidth:xSize - rampwidth, 0:ySize] = (lightlevel - darknoise_mean) * 0.7
    # large area (antennal lobe) is average
    stillimage[40:95, 15:110] = (lightlevel - darknoise_mean)
    # some glomeruli are brighter, to unequal extent
    thisglo = glo1
    stillimage[thisglo[0]:thisglo[1], thisglo[2]:thisglo[3]] = (lightlevel - darknoise_mean) * 1.3
    thisglo = glo2
    stillimage[thisglo[0]:thisglo[1], thisglo[2]:thisglo[3]] = (lightlevel - darknoise_mean) * 1.5
    thisglo = glo3
    stillimage[thisglo[0]:thisglo[1], thisglo[2]:thisglo[3]] = (lightlevel - darknoise_mean) * 1.1
    thisglo = glo4
    stillimage[thisglo[0]:thisglo[1], thisglo[2]:thisglo[3]] = (lightlevel - darknoise_mean) * 1.8
    thisglo = glo5
    stillimage[thisglo[0]:thisglo[1], thisglo[2]:thisglo[3]] = (lightlevel - darknoise_mean) * 1.3
    thisglo = glo6
    stillimage[thisglo[0]:thisglo[1], thisglo[2]:thisglo[3]] = (lightlevel - darknoise_mean) * 1.3

    if badpixels:
        # bad pixels are fixed in space - therefore create in an image
        noise = np.random.rand(xSize, ySize) > badpixels_clip  # values in [0-1]
        stillimage[noise] = 0
        # assumes that from now on everything is multiplicative, not additive

    # check result
    # plt.imshow(stillimage[:,:].T, origin='lower')

    # broadcast still image to time domain
    #    movie memory structure
    raw666 = np.zeros((xSize, ySize, tSize))
    stillimage = stillimage.reshape(xSize, ySize, 1)
    raw666 = raw666 + stillimage  # use broadcasting

    # now go into the time domain:
    # add bleaching
    if bleach:
        fullframe = (0, xSize, 0, ySize)  # apply bleaching to full frame
        oneline = np.arange(tSize)
        oneline = (1 - bleach_percent / 200) + (bleach_percent / 100) * np.exp(-oneline / bleach_tau)
        raw666 = applytimecourse(raw666, fullframe, oneline)
        # plt.plot(oneline)

    if lampnoise:  # if lampnoise == 0, it is like false.
        fullframe = (0, xSize, 0, ySize)  # apply bleaching to full frame
        oneline = 1 + (lampnoise / 100) * np.random.rand(tSize)
        raw666 = applytimecourse(raw666, fullframe, oneline)
        # plt.plot(oneline)

    # add glomeruli

    ###sawtooth
    oneline = np.zeros(tSize)
    oneline[stimonset:stimoffset] = np.linspace(0, peaksignal / 100, stimoffset - stimonset)
    oneline[stimoffset:] = np.linspace(peaksignal / 100, 0, tSize - stimoffset)
    oneline = oneline + 1  # baseline factor is 1
    raw666 = applytimecourse(raw666, glo1, oneline)
    raw666 = applytimecourse(raw666, glo2, oneline)

    ###realistic:
    tau1 = stimoffset - stimonset
    tau2 = 2 * tau1
    c = 1
    oneline = np.ones(tSize)
    response = np.arange(tSize - stimonset)
    response = (-1) * np.exp(-response / tau1) + c * np.exp(-response / tau2)
    response = ((peaksignal / 100) / np.max(response)) * response  # scale to peaksignal
    oneline[stimonset:] = oneline[stimonset:] + response
    raw666 = applytimecourse(raw666, glo3, oneline)
    raw666 = applytimecourse(raw666, glo4, oneline)
    raw666 = applytimecourse(raw666, glo5, oneline)

    # late response
    oneline = np.ones(tSize)
    oneline[stimoffset:] = oneline[stimoffset:] + response[:(tSize - stimoffset)]
    raw666 = applytimecourse(raw666, glo6, oneline)

    # biphasic response
    oneline = np.ones(tSize)
    oneline[stimonset:] = oneline[stimonset:] + response
    oneline[stimoffset:] = oneline[stimoffset:] - 2 * response[:(tSize - stimoffset)]
    raw666 = applytimecourse(raw666, glo7, oneline)

    # negative response, builds on factors defined in realistic
    oneline = np.ones(tSize)
    oneline[stimonset:] = oneline[stimonset:] - response
    raw666 = applytimecourse(raw666, glo8, oneline)

    # plt.plot(oneline)

    # add scattered light, as gaussian filter
    if scatterlight:
        raw666[3 * rampwidth:xSize - 2 * rampwidth, :, :] = sp.ndimage.gaussian_filter(
            raw666[3 * rampwidth:xSize - 2 * rampwidth, :, :], sigma=[scatterlight, scatterlight, 0])

    if shotnoise:  # add noise, random and proportional to square root of signal
        # photons are poisson distributed
        #        noisier = lambda p : np.random.poisson(p)
        #        raw666 = noisier(raw666)
        raw666 = np.random.poisson(raw666)  # one line solution! Python is so cool...

    if darknoise:
        # add chip noise.
        # This comes at the end, because it is not influenced by light
        noise = np.random.rand(xSize, ySize, tSize)  # values in [0-1]
        noise = noise * darknoise_amplitude + darknoise_mean - darknoise_amplitude / 2
        raw666 = raw666 + noise

    # now, AFTER the noise, get a ramp of totally clean signals for calibration

    # create a step function with stepsize steps, also to 2*lightlevel
    # this area has no signals in time - only differrent background, no noise
    stepfunction = np.repeat(np.arange(stepsize), ySize / stepsize)
    stepfunction = stepfunction * (2 * lightlevel / np.max(stepfunction))
    # shift by darknoise_mean to avoid having values of 0, which cause trouble when dividing in CalcSig
    stepfunction = stepfunction + darknoise_mean
    stepfunction = stepfunction.reshape(1, ySize, 1)
    raw666[-rampwidth:, :, :] = stepfunction  # set to uniform background level

    # create a step function with stepsize steps
    stepfunction = np.repeat(np.arange(stepsize), ySize / stepsize) - stepsize // 2  # negative and positive signals
    # calibrate to peaksignal max both ways
    stepfunction = ((peaksignal / 100) / np.max(stepfunction)) * stepfunction
    # values are given in percent
    stepfunction = (stepfunction + 1) * lightlevel
    raw666[-2 * rampwidth:-rampwidth, :, :] = lightlevel  # set to uniform background level
    stepfunction = stepfunction.reshape(1, ySize, 1)
    raw666[-2 * rampwidth:-rampwidth, :, stimonset:stimoffset] = stepfunction
    #    plt.plot(raw666[-2*rampwidth,:,10])
    #    plt.plot(raw666[-2*rampwidth,:,25])
    #    plt.show()
    ##

    # camera is 12 bit, therefore clip to 4095, and integer
    raw666 = np.clip(raw666.astype(int), 0, 4095)


#    plt.imshow(raw666[:,:,30].T, origin='lower')
#    plt.show()
#    plt.plot(raw666[100,10,:])
#    plt.plot(raw666[100,60,:])
#    plt.plot(raw666[100,80,:])
#    plt.plot(raw666[80,60,:])
#    plt.plot(raw666[60,60,:])
#    plt.show()

    return raw666 # end of create_raw_data667


def create_raw_data666(p1_metadata, peaksignal):
    '''
    Giovanni, October 2020, based on previous 666 for square glomeruli, which is now called 667
    Add: glomeruli with round shapes, because CaImAn detects round shapes
    Add: movement (for now just lateral movements)
    Add: frames out of focus (simulated with smoothing)
    Add: unequal bleaching (created by adding non-bleaching base fluorescence)
    -> variable noBleach_lightlevel
    move bad pixels to the end (after artificial movement)
    
    Parameters
    ----------
    p1_metadata : TYPE
        contains all parameters, used are stimulus_on and stimulus_end
    peaksignal : TYPE real
        like odor concentration, i.e. how strong the response in the fictive glomeruli.

    Returns
    -------
    matrix : TYPE
        corresponds to p1.raw, to be copied there by caller

    '''

    print('ViewLoadData/LoadRaw666: generating test data with many fixed settings!')
    
    addRightBand = False
    #right band has fixed value squares, no noise, no change over time.
    addLeftBand = False
    # lateral band left is a continuus up and down, including noise

    stimulus_pulse_start_end_frames = p1_metadata["pulsed_stimuli_handler"].get_pulse_start_end_frames()
    stimonset = stimulus_pulse_start_end_frames[0][0]
    stimoffset = stimulus_pulse_start_end_frames[0][1]
    ### for playing around start after #:
#####
    #peaksignal, stimonset, stimoffset = 10, 25, 35 # - is in command line now
    # local flags
    lightlevel = 1000  # baseline value of each pixel.
    # at the setup, you would set exposure time and light level accordingly

    noBleach_lightlevel = 500 # add this base lavel after fictive bleaching,
    # the effect is that bleaching cannot be completely corrected by our standard procedure,
    # because it will not have the same parameters in the deltaF/F data across all glomeruli.
    randomseed = 0  # set to None for irreproducible random numbers
    # add chipnoise
    darknoise = True
    darknoise_mean = 100  # mean of background values in the chip
    darknoise_amplitude = 20  # max amplitude of background chip noise
    
    # subtract the constant parts from the light level, 
    # because in the experiment we set the light to the sum of them all
    brain_lightlevel = lightlevel - darknoise_mean - noBleach_lightlevel# 
    # I assume chip noise to be random over time
    #
    xSize, ySize, tSize = 172, 130, 80  # 120, 99, 80
    rampwidth = 10  # width of the ramp, 3 left, 2 right, i.e. 
    # usable range therefore is, in x, 30-152, center is 92
    stepsize = 13  # must be a divisor of ySze

    # glomerular locations for square glomeruli are (make sure to exclude rampwidth)
    # coordinates are x from left to right
    # y from bottom to top
    glo1 = (50, 70, 90, 110)  # x,x - y,y
    # glo2 = (60, 80, 60, 80)  # x,x - y,y
    # glo3 = (65, 75, 45, 55)
    # glo4 = (70, 90, 30, 50)
    # glo5 = (50, 65, 30, 45)
    # glo6 = (70, 90, 50, 70)  # off response
    # glo7 = (50, 70, 90, 110)  # biphasic response
    # glo8 = (75, 95, 90, 110)  # negative response

    # glomerular locations for circle glomeruli, syntax centerX, centerY, radius
    # x from left to right, y from bottom to top
    circle1left = (50, 65, 20)
    circle2     = (60, 85, 15)
    circle3     = (70, 97, 10)
    circle4top  = (92, 105, 18)
    circle5     = (110, 85, 12)
    circle6right= (120, 65, 15)
    circle7     = (110, 45, 10)
    circle8bottom=(92, 25, 19)
    circle9     = (70, 32, 10)
    circle0     = (60, 50, 16)
    circleCenter= (90, 65, 15)


    shotnoise = True  # add photon noise

    # add bad pixels on the CCD chip, i.e. pixels with value 0
    badpixels = True
    badpixels_clip = 0.98  # 0.9 for 10% bad pixels
    #

    # add global bleaching
    bleach = True
    bleach_percent = 10  # percentage bleaching
    bleach_tau = tSize / 5  # assume decay to 37% of percentage over this length

    # add lamp noise
    lampnoise = 0.1  # value in percent. 0 for no noise. Value is PEAK noise

    # add scattered light
    scatterlight = 2  # 2 # unit is gaussian pixels; 0 for no scattered light

    # smoothBackground
    smoothBackground = 5

    # smoooth some frames, to mimit out of focus movement
    smoothOutOfFocus = 5
    smoothOutOfFocus_frames = [4,5,34,35,36,37,50,51,52,53,53,55,70,71,72]

    # add movement
    AddMovement = True
    AddMovementSize = 3 # in pixels, x and y direction, gaussian distribution

    # change code, do exclude lateral step image

    # TODO
    # - add light scatter (smooth): modify
    # - add movement
    #
    def applytimecourse_square_glo(matrix, square_glo, oneline):
        '''
        applies oneline as a factor (length: tSize)
        to square window (glomerulus) defined with upperleft, lowerright
        glo_location is (x_left,x_right,y_down, y_up)
        (y_down < y_up; but safety net included)
        '''
        x1 = np.min((square_glo[0], square_glo[1]))
        x2 = np.max((square_glo[0], square_glo[1]))
        y1 = np.min((square_glo[2], square_glo[2]))
        y2 = np.max((square_glo[3], square_glo[3]))
        matrix[x1:x2, y1:y2, :] = matrix[x1:x2, y1:y2, :] * oneline.reshape(1, 1, tSize)
        return matrix


# functions to create circular regions, and apply time courses to them
    # def create_circular_mask(h, w, center=None, radius=None):
    # # from 
    # # https://stackoverflow.com/questions/44865023/how-can-i-create-a-circular-mask-for-a-numpy-array
    #     if center is None: # use the middle of the image
    #         center = (int(w/2), int(h/2))
    #     if radius is None: # use the smallest distance between the center and image walls
    #         radius = min(center[0], center[1], w-center[0], h-center[1])
    
    #     Y, X = np.ogrid[:h, :w]
    #     dist_from_center = np.sqrt((X - center[0])**2 + (Y-center[1])**2)
    
    #     mask = dist_from_center <= radius
    #     return mask
    def create_circular_mask(x, y, glomerulus):
        # glomerulus is (x, y, radius)
        # x from left to right, y from bottom to top
        Y, X = np.ogrid[:x, :y]
        # why x/y are inverted in the glomerulus coordinates (rows/columns instead of x/y) evades me
        dist_from_center = np.sqrt((X - glomerulus[1])**2 + (Y-glomerulus[0])**2)    
        mask = dist_from_center <= glomerulus[2]
        return mask # this is a boolean 2D array. 

    def applytimecourse_mask(matrix, mask, oneline):
        '''
        applies oneline as a factor (length: tSize)
        to a boolean glomerulus (2D) in mask
        '''
        #uses broadcasting to apply 2D mask
        matrix[mask,] = matrix[mask,] * oneline.reshape(1, 1, tSize)
        return matrix

    def applytimecourse_glomerulus(matrix, glomerulus, oneline):
        mask = create_circular_mask(matrix.shape[0], matrix.shape[1], glomerulus)
        matrix = applytimecourse_mask(matrix, mask, oneline)
        return matrix



    # set random numbers
    np.random.seed(randomseed)
    # create still image
    # with average light level as visible to the experimenter
    # therefore subtract darknoise_mean from lightlevel (has been done avoe)
    stillimage = np.full((xSize, ySize), brain_lightlevel, dtype='float64')
    
    # create a bit of a photo:.
    # background is darker 
    stillimage[:, :] = brain_lightlevel * 0.7
    # large circle in the middle (antennal lobe) is average
    circlesize = min(xSize//2, ySize//2)
    position =  (xSize//2, ySize//2, circlesize)
    stillimage[create_circular_mask(xSize, ySize, position)] = brain_lightlevel
    # two concentric circles inside, brighter
    position =  (xSize//2, ySize//2, circlesize//1.5)
    stillimage[create_circular_mask(xSize, ySize, position)] = brain_lightlevel * 1.5
    position =  (xSize//2, ySize//2, circlesize//2)
    stillimage[create_circular_mask(xSize, ySize, position)] = brain_lightlevel * 2

    # some glomeruli have different brightness, to unequal extent
    stillimage[create_circular_mask(xSize, ySize, circle1left)]   *= 1.7
    stillimage[create_circular_mask(xSize, ySize, circle2)]       *= 0.9
    stillimage[create_circular_mask(xSize, ySize, circle3)]       *= 2.0
    stillimage[create_circular_mask(xSize, ySize, circle4top)]    *= 0.7
    stillimage[create_circular_mask(xSize, ySize, circle5)]       *= 1.4
    stillimage[create_circular_mask(xSize, ySize, circle6right)]  *= 0.9
    stillimage[create_circular_mask(xSize, ySize, circle7)]       *= 1.5
    stillimage[create_circular_mask(xSize, ySize, circle8bottom)] *= 0.7
    stillimage[create_circular_mask(xSize, ySize, circle9)]       *= 1.9
    stillimage[create_circular_mask(xSize, ySize, circle0)]       *= 0.8
    stillimage[create_circular_mask(xSize, ySize, circleCenter)]  *= 2.0

    # smoooth image,  sigma is smoothBackground
    stillimage = sp.ndimage.gaussian_filter(stillimage, smoothBackground, mode='nearest')

    if addLeftBand:
        # left side, overwriting everything here: create four ramps
        # create a ramp from 0 to 2*lightlevel
        oneline = np.linspace(0, 2 * lightlevel, ySize).reshape(1, ySize)
        stillimage[0:rampwidth, :] = oneline  # first band, going up
        stillimage[rampwidth:2 * rampwidth, :] = np.flip(oneline)  # second band, going down
        # create a ramp in the center, in order to avoid border effects
        oneline = np.linspace(0, 2 * lightlevel, ySize // 2).reshape(1, ySize // 2)
        stillimage[2 * rampwidth:np.int(2.5 * rampwidth),
                   ySize // 4 : ySize // 4 + ySize // 2] = oneline  # third half band, going up
        stillimage[np.int(2.5 * rampwidth):3 * rampwidth, 
                   ySize // 4:ySize // 4 + ySize // 2] = np.flip(oneline)  # fourth half band, going down

   

    # check result while debugging
    # plt.imshow(stillimage[:,:].T, origin='lower')

    # broadcast still image to time domain
    #    movie memory structure
    raw666 = np.zeros((xSize, ySize, tSize))
    stillimage = stillimage.reshape(xSize, ySize, 1)
    raw666    += stillimage  # use broadcasting

    # now go into the time domain:
    # add bleaching
    if bleach:
        fullframe = (0, xSize, 0, ySize)  # apply bleaching to full frame
        oneline = np.arange(tSize)
        oneline = (1 - bleach_percent / 200) + (bleach_percent / 100) * np.exp(-oneline / bleach_tau)
        # calculate deltaF/f first - avoid values of 0, therefore add 10
        stillimage += 10
        raw666     += 10
        raw666 /= stillimage
        raw666 = applytimecourse_square_glo(raw666, fullframe, oneline)
        # calculate back to "original" data
        raw666 *= stillimage
        raw666 += np.min(raw666) # avoid negative values
        # plt.plot(oneline)

    if lampnoise:  # if lampnoise == 0, it is like false.
        fullframe = (0, xSize, 0, ySize)  # apply lampnoise to full frame
        oneline = 1 + (lampnoise / 100) * np.random.rand(tSize)
        raw666 = applytimecourse_square_glo(raw666, fullframe, oneline)
        # plt.plot(oneline)

    # add glomeruli, using different time courses

    ###sawtooth
    oneline = np.zeros(tSize)
    oneline[stimonset:stimoffset] = np.linspace(0, peaksignal / 100, stimoffset - stimonset)
    oneline[stimoffset:] = np.linspace(peaksignal / 100, 0, tSize - stimoffset)
    oneline = oneline + 1  # baseline factor is 1
    #raw666 = applytimecourse_square_glo(raw666, glo1, oneline)
    # raw666 = applytimecourse_square_glo(raw666, glo2, oneline)
    raw666 =  applytimecourse_glomerulus(raw666, circle1left, oneline)


    ###realistic:
    tau1 = stimoffset - stimonset
    tau2 = 2 * tau1
    c = 1
    oneline = np.ones(tSize)
    response = np.arange(tSize - stimonset)
    response = (-1) * np.exp(-response / tau1) + c * np.exp(-response / tau2)
    response = ((peaksignal / 100) / np.max(response)) * response  # scale to peaksignal
    oneline[stimonset:] +=  response
    # raw666 = applytimecourse_square_glo(raw666, glo3, oneline)
    # raw666 = applytimecourse_square_glo(raw666, glo4, oneline)
    # raw666 = applytimecourse_square_glo(raw666, glo5, oneline)
# apply to circle glomerulus
    raw666 =  applytimecourse_glomerulus(raw666, circle2, oneline)
    oneline = (oneline -1)*1.5 +1
    raw666 =  applytimecourse_glomerulus(raw666, circle3, oneline)
    # late response
    oneline = np.ones(tSize)
    oneline[stimoffset:] = oneline[stimoffset:] + response[:(tSize - stimoffset)]
    # raw666 = applytimecourse_square_glo(raw666, glo6, oneline)
# apply to circle glomerulus
    raw666 =  applytimecourse_glomerulus(raw666, circle4top, oneline)
    oneline = (oneline -1)*1.5 +1
    raw666 =  applytimecourse_glomerulus(raw666, circle5, oneline)

# slightly delayed
    oneline = np.ones(tSize)
    oneline[stimonset+5:] +=  response[:-5]
    raw666 =  applytimecourse_glomerulus(raw666, circleCenter, oneline)


    # biphasic response
    oneline = np.ones(tSize)
    oneline[stimonset:] = oneline[stimonset:] + response
    oneline[stimoffset:] = oneline[stimoffset:] - 2 * response[:(tSize - stimoffset)]
    # raw666 = applytimecourse_square_glo(raw666, glo7, oneline)
# apply to circle glomerulus
    raw666 =  applytimecourse_glomerulus(raw666, circle6right, oneline)
    oneline = (oneline -1)*1.5 +1
    raw666 =  applytimecourse_glomerulus(raw666, circle7, oneline)
    oneline = (oneline -1)*0.6 +1
    raw666 =  applytimecourse_glomerulus(raw666, circle0, oneline)

    # negative response, builds on factors defined in realistic
    oneline = np.ones(tSize)
    oneline[stimonset:] = oneline[stimonset:] - response
    # raw666 = applytimecourse_square_glo(raw666, glo8, oneline)
# apply to circle glomerulus
    raw666 =  applytimecourse_glomerulus(raw666, circle8bottom, oneline)
    oneline = (oneline -1)*1.5 +1
    raw666 =  applytimecourse_glomerulus(raw666, circle9, oneline)

    # plt.plot(oneline)

    # add scattered light, as gaussian filter
    if scatterlight:
        raw666[3*rampwidth:xSize - 2*rampwidth, :, :] = sp.ndimage.gaussian_filter(
            raw666[3 * rampwidth:xSize - 2 * rampwidth, :, :], sigma=[scatterlight, scatterlight, 0])

    if shotnoise:  # add noise, random and proportional to square root of signal
        # photons are poisson distributed
        #        noisier = lambda p : np.random.poisson(p)
        #        raw666 = noisier(raw666)
        raw666 = np.random.poisson(raw666)  # one line solution! Python is so cool...

##movement. I want movement that is subpixel, therefore each frame is rescaled 10fold.
# using for-loop to save memory space
    if AddMovement:
        # create random movement array in x and y. AddMovementSize
        # movement is slow, therefore random numbers first on array a tenth of the size
        # then blown up by 10, and limited to tSize elements
        x_movement = np.random.rand(tSize//10 + 1)*AddMovementSize
        x_movement = ndimage.zoom(x_movement, 10)[:tSize]
        y_movement = np.random.rand(tSize//10 + 1)*AddMovementSize
        y_movement = ndimage.zoom(y_movement, 10)[:tSize]
        # shift image by image
        for i in range(tSize):
            raw666[3*rampwidth:xSize - 2*rampwidth,:,i] = ndimage.shift(
                raw666[3*rampwidth:xSize - 2*rampwidth,:,i], (x_movement[i], y_movement[i]), 
                mode='nearest')

    if darknoise:
        # add chip noise.
        # This comes at the end, because it is not influenced by light
        noise = np.random.rand(xSize, ySize, tSize)  # values in [0-1]
        noise = noise * darknoise_amplitude + darknoise_mean - darknoise_amplitude / 2
        raw666 = raw666 + noise



    # add background fluorescence level that is not affected by any of the above manipulations
    # simulating fluorescence that is not from the reporter
    # and that is not affected by bleaching
    raw666 += noBleach_lightlevel 
    
    # now add movement. Smooth to mimic vertical movement
        # smoooth some frames, to mimit out of focus movement
    # smoothOutOfFocus = 5
    # smoothOutOfFocus_frames = [4,5,34,35,36,37,50,51,52,53,53,55,70,71,72]
    if smoothOutOfFocus: #only if not 0
    # syntax as for scatterlight
        raw666[3 * rampwidth:xSize - 2 * rampwidth, :, smoothOutOfFocus_frames] = sp.ndimage.gaussian_filter(
            raw666[3 * rampwidth:xSize - 2 * rampwidth, :, smoothOutOfFocus_frames], sigma=[scatterlight, scatterlight, 0])

    
    if badpixels: ##move to after movement creation
        # bad pixels are fixed in space - therefore equal for third dimension
        noise = np.random.rand(xSize, ySize) > badpixels_clip  # values in [0-1]
        raw666[noise,:] = 0


    # now, AFTER the noise, get a ramp of totally clean signals for calibration
    if addRightBand:
        # create a step function with stepsize steps, also to 2*lightlevel
        # this area has no signals in time - only differrent background, no noise
        stepfunction = np.repeat(np.arange(stepsize), ySize / stepsize)
        stepfunction = stepfunction * (2 * lightlevel / np.max(stepfunction))
        # shift by darknoise_mean to avoid having values of 0, which cause trouble when dividing in CalcSig
        stepfunction = stepfunction + darknoise_mean
        stepfunction = stepfunction.reshape(1, ySize, 1)
        raw666[-rampwidth:, :, :] = stepfunction  # set to uniform background level
    
        # create a step function with stepsize steps
        stepfunction = np.repeat(np.arange(stepsize), ySize / stepsize) - stepsize // 2  # negative and positive signals
        # calibrate to peaksignal max both ways
        stepfunction = ((peaksignal / 100) / np.max(stepfunction)) * stepfunction
        # values are given in percent
        stepfunction = (stepfunction + 1) * lightlevel
        raw666[-2 * rampwidth:-rampwidth, :, :] = lightlevel  # set to uniform background level
        stepfunction = stepfunction.reshape(1, ySize, 1)
        raw666[-2 * rampwidth:-rampwidth, :, stimonset:stimoffset] = stepfunction
    #    plt.plot(raw666[-2*rampwidth,:,10])
    #    plt.plot(raw666[-2*rampwidth,:,25])
    #    plt.show()
    ##


    # camera is 12 bit, therefore clip to 4095, and integer
    raw666 = np.clip(raw666.astype(int), 0, 4095)


#    plt.imshow(raw666[:,:,30].T, origin='lower')
#    plt.show()
#    plt.plot(raw666[100,10,:])
#    plt.plot(raw666[100,60,:])
#    plt.plot(raw666[100,80,:])
#    plt.plot(raw666[80,60,:])
#    plt.plot(raw666[60,60,:])
#    plt.show()

    return raw666


def MovementCorrection(MatrixIN, flag):
#;input: a 3-dim-matrix MatrixIN
#;output: another matrix, with each frame shifted in x and y so that the movements are corrected 
#;this output has been removed - program should crash when called in old mode
#;output: shiftArray contains how much each frame was shifted 
#;options 
    def old_RollIt(frames, shiftArray, neighbourSearch, MatrixIN, matrixOUT, correlation, maxShiftX, maxShiftY):
        # uses shiftArray, matrix etc. 
        # does not work yet (26.7.2018)
        bestXshift = shiftArray[0,frames] 
        bestYshift = shiftArray[1,frames] 
#		;take values from previous shift 
        for sx in range( (-1)*neighbourSearch, neighbourSearch+1): 
            for sy in range( (-1)*neighbourSearch, neighbourSearch+1): 
                shift1x = shiftArray[0,frames] + sx 
                shift1y = shiftArray[1,frames] + sy 
                if (shift1x > maxShiftX) : shift1x =  maxShiftX 
                if (shift1y > maxShiftY) : shift1y =  maxShiftY 
                if (shift1x < -maxShiftX): shift1x = -maxShiftX 
                if (shift1y < -maxShiftY): shift1y = -maxShiftY 

                result = np.corrcoef(MatrixIN[ (maxShiftX+shift1x):(maxShiftX+smallMsizeX+shift1x), 
                                               (maxShiftY+shift1y):(maxShiftY+smallMsizeY+shift1y),
                                               frames].flatten(),
                                     MatrixIN[ (maxShiftX):(maxShiftX+smallMsizeX),
                                               (maxShiftY):(maxShiftY+smallMsizeY),
                                               compareFrame].flatten())    
#    		result = correlate(matrixIN(maxShiftX+shift1x:(maxShiftX+smallMsizeX+shift1x-1),maxShiftY+shift1y:(maxShiftY+smallMsizeY+shift1Y-1),frames),    $ 
#                               matrixIN(maxShiftX:(maxShiftX+smallMsizeX-1),MaxShiftY:(MaxShiftY+smallMsizeY-1),compareFrame) ) 
#
                if (result[1][0] > correlation): # THEN begin ; found a better shift 
                    bestXshift = shift1x 
                    bestYshift = shift1y 
                    correlation= result[1][0] 
        if (bestXshift > maxShiftX):  print('*****Movementcorrection: shiftX exceeds positive limit!') 
        if (bestXshift < -maxShiftX): print('*****Movementcorrection: shiftX exceeds negative limit!') 
        if (bestYshift > maxShiftY):  print('*****Movementcorrection: shiftY exceeds positive limit!') 
        if (bestYshift < -maxShiftY): print('*****Movementcorrection: shiftY exceeds negative limit!') 
        shiftArray[0,frames] = bestXshift 
        shiftArray[1,frames] = bestYshift 
        shiftArray[2,frames] = int(correlation*10) 
# the IDL program shifted by the negative amount??        
        matrixOUT[:,:,frames] = np.roll(matrixOUT[:,:,frames], bestXshift, axis=0)
        matrixOUT[:,:,frames] = np.roll(matrixOUT[:,:,frames], bestYshift, axis=1)
        return (shiftArray, matrixOUT, correlation) #Rollit within MovementCorrection

    def RollIt(frames, compareFrame, neighbourSearch, MatrixIN, MatrixOUT, shiftArray):
#simplified version  -  shifts always from central 0 position
#this solution is slow, because all shifts are evaluated every time
# in IDL (old_RollIt), neighbour search meant that only few additional shifts were tested each time
        # shift matrix by all pixel values up to neighbourSearch
        correlation = 0
        for sx in range( (-1)*neighbourSearch, neighbourSearch+1): 
            for sy in range( (-1)*neighbourSearch, neighbourSearch+1): 
                # for each shift, calculate correlation
                shiftMatrix = np.roll(   MatrixIN[:,:,frames], sx, axis=0)
                shiftMatrix = np.roll(shiftMatrix, sy, axis=1)
                #calculate correlation, avoiding the border region
                result = np.corrcoef(shiftMatrix[ (neighbourSearch):(-neighbourSearch), 
                                               (neighbourSearch):(-neighbourSearch)].flatten(),
                                     MatrixIN[ (neighbourSearch):(-neighbourSearch), 
                                               (neighbourSearch):(-neighbourSearch),
                                               compareFrame].flatten())    
                if (result[1][0] > correlation): # THEN begin ; found a better shift 
                    bestXshift = sx 
                    bestYshift = sy 
                    correlation= result[1][0] 
        shiftArray[0,frames] = bestXshift 
        shiftArray[1,frames] = bestYshift 
        shiftArray[2,frames] = int(correlation*10) 
# the IDL program shifted by the negative amount??        
        MatrixOUT[:,:,frames] = np.roll( MatrixIN[:,:,frames], bestXshift, axis=0)
        MatrixOUT[:,:,frames] = np.roll(MatrixOUT[:,:,frames], bestYshift, axis=1)
        return (shiftArray, MatrixOUT) #Rollit within MovementCorrection

    # local settings for MovementCorrection
    maxShift     = 0.10  #;proportion of maximal shift allowed 
    compareFrame = 5     #;which frame to take as standard view (i.e. not moved)
    plotShift    = True  #; plot the shift result 
    logFile      = True  #; 
    # logFileName  = flag.STG_OdorReportPath +flag.STG_ReportTag +'_Shift.log' 
#				; if set to 0 then all possible movements are checked 
    (sizeX, sizeY, sizeZ) = MatrixIN.shape
    neighbourSearch = min([int(sizeX * maxShift),int(sizeY * maxShift)]) 
#;define ShiftArray which contains all shift information 
    shiftArray = np.zeros((3, sizeZ), dtype=int) #;dim0:shiftX,dim1:shiftY, dim3:corr*100 
#;define outputmatrix 
    MatrixOUT = MatrixIN.copy() 
 #	;up from compareframe 
    for frames  in range(compareFrame+1, sizeZ): 
        (shiftArray, MatrixOUT) = RollIt(frames, compareFrame, neighbourSearch, MatrixIN, MatrixOUT, shiftArray)
#	;down from compareframe 
    for frames  in range(compareFrame-1, -1, -1): 
        (shiftArray, MatrixOUT) = RollIt(frames, compareFrame, neighbourSearch, MatrixIN, MatrixOUT, shiftArray)
#
#;suboptimal approach: go through all possibel shifts 
# implemented differently from IDL now, by increasing neighbourSearch to very high values
######## done movement correction
    if plotShift:
        # evenly sampled time at 200ms intervals
        t = np.arange(0., sizeZ, 1) #maybe replace 1 with framerate, to have time
        # use p1.frequency or the like
        # red dashes, blue squares and green triangles
        plt.plot(t, shiftArray[0,:], 'r--', t, shiftArray[1,:], 'b--', t, shiftArray[2,:], 'g^')
        plt.show()
#	window, 0 
#	;loadCT, 39 
#	range = max([maxshiftX,maxshiftY]) 
#	plot, shiftArray(0,*), yrange=[(-1)*range,range],color=140 
#	oplot, shiftarray(1,*), color=254 
#	oplot, shiftarray(2,*), color=255 
    if logFile: 
        print('ViewLoadData.MovementCorrection: logFile not implemented - still to do')
        #no need for log file, shifts are written in other program
#	openW, 10, logFileName,  /APPEND 
#	printF, 10, string(9b)+string(9b)+'Followes report shift for measurement ',p1.ex_name,'*',p1.experiment 
#	for i=0,sizeZ-1 do begin #
#		printF, 10, strtrim(string(shiftArray(0,i)),2),+string(9b)+strtrim(string(shiftArray(1,i)),2) #
#	endFOR 
#	printF, 10, string(9b)+string(9b)+'****************end of************** ',p1.ex_name 
#	close, 10 
    return (MatrixOUT, shiftArray) #MovementCorrection

def ReadWriteMovementValues(flagWrite, MovementList, p1, flag):
#;reads or writes movement values for within one measurement
#;uses standard file name conventions
#;write or read data? readFlag now boolean
    readFlag =  (flagWrite == 'read')
#any other string means: write.
#filename for the list
    MoveFile =  os.path.join(flag["STG_OdorInfoPath"],flag["STG_ReportTag"])+'.moveList'
#what is the current measurement??
#???inputlabel = fix(inputOdorFile)
    #debug MoveFile
    #MoveFile = 'C:/Users/Giovanni Galizia/Documents/Production/2017_Alja_PostOdor/Filme_data/data/ORN_Glomeruli/al_100312_e.moveList'
    if readFlag:
#  ;read the file
        if os.path.isfile(MoveFile):
            print('ReadWriteMovementValues: open info file for reading movement:', MoveFile)
    # format of movelist:
    # first column is the name of the measurement. For each measurement there are six rows.
    # first three rows relate to odor 0, second three rows to odor 1. Take odor 1 here.
    # the second column is the row label: 0 for x movement, 1 for y movement, 2 for "quality", i.e. 0,1,2 ... repeat this...
    # the third column is the odor flag, generally 0,0,0,1,1,1, ...repeat this...
    # HERE: take row 4 for x movement, and row 5 for y movement, IGNORE the rest for now.
    # movelist is tab-separated
            moveList_df = pd.read_csv(MoveFile, sep='\t', header=None)
    # which is the measurement I am interested in?
            measuNum = p1.messungszahl
    # I only want the rows that have measuNum in the first column
            moveList_df = moveList_df.loc[moveList_df.iloc[:,0] == measuNum]
    # remove the first two columns, and keep only fourth and fifth row
            #moveList_df = moveList_df.iloc[3:5,3:] #take rows 3-5, i.e. second three rows
            moveList_df = moveList_df.iloc[-3:,3:p1.metadata.frames+3]  #take last three rows,
            # and only as many columns as frames starting at 3
#;definition of movement list in the master is:
#;movementList = intarr(3,p1.frames,p1.odors+1); x/y/quality, frames, data(odor/wavelength)
            # because in IDL there were, generally, two odors, the first fictive, the second not
            # in most moveLists there will be 6 lines, with identical values in the first 3  and secont 3
            # or with 0 in the first 3 lines. 
            # therefore, here in Phython I take the LAST 3 lines
            # this way, in the future, I can write 3 lines only. 
            # will go wrong if several odors are used (e.g. separate movementlist in Fura? CHECK)
            MovementList = moveList_df.values # report matrix only
    else: #write file
        print('ReadWriteMovementValues: open info file for writing ', MoveFile)
        # add the first three columns to movementList matrix
        # first column: p1.messungszahl
        # second column 0,1,2 (for x/y/quality)
        # third column 0 (for odor - not used in Python, yet)
        out_info = np.array([[p1.messungszahl,0,0],[p1.messungszahl,1,0],[p1.messungszahl,2,0]])
        out_move   = pd.DataFrame(np.append(out_info, MovementList, axis=1)) #also convert to dataframe
        if os.path.isfile(MoveFile): #file exists
            print('ReadWriteMovementValues: appending to old file')
            # load previous data
            old_move  = pd.read_csv(MoveFile, sep='\t', header=None)
            out_move  = pd.concat([old_move,out_move]) #add this one to the existing list
        # now write the new movementList to file. 
        # use dataframe format for my lazyness  -  np.savetxt would be leaner
        # do not add header line (also IDL did not do that any more)
        out_move.to_csv(MoveFile, sep='\t', header=False, index=False)
    #movementList is just the shiftArray, movementList_w has the first three columns added
    return MovementList #
#end; ReadWriteMovementValues


def MovementCorrectionMaster(p1, flag):
#
#;old movement correction (giovanni, beware, does not work for all datasets)
#;or new movement correction (mathias, yet to be tested as of April 1st, 2003), with flag setting above 10
#
#; recalculate movement (flag set to 1), or recalculate and save the shifts (flag set to 2), or use saved shifts (flag set to 3)
    MovementFlag = flag.CSM_Movement
    ShrinkFactor = flag.LE_ShrinkFaktor #
    # movement values are stored WITHOUT shrink factor
    MathiasCorrection = (MovementFlag > 10)
    if MathiasCorrection: MovementFlag = MovementFlag - 10
#;either recalculate movement (flag set to 1), or recalculate and save the shifts (flag set to 2), or use saved shifts (flag set to 3)
    if (MovementFlag == 1): print('ViewLoadData.MovementCorrectionMaster: on the spot')
    if (MovementFlag == 2): print('ViewLoadData.MovementCorrectionMaster: on the spot, saving values')
    if (MovementFlag == 3): print('ViewLoadData.MovementCorrectionMaster: using saved values')
#IF (movementFlag eq 4) THEN print, 'MovementCorrectionMaster: using saved values, being equal for both sets (master/slave)'
#IF (movementFlag eq 5) THEN print, 'Extracting Shifts from Movement List - ignoring movements'
#
#;check movement on monitor?
#    MonitorMovement = 1 # ;(movementFlag eq 2)
#
#;define movement value array
#    odors = 1 # or copy p1.odors, if that exists
#    MovementList = np.zeros((3, p1.frames, odors), dtype=int) # I take 2 odors for backwards compatibility
#    MovementList = np.zeros(3, p1.frames, 1, dtype=int) # I take 2 odors for backwards compatibility
    # the two odors are: 0 for control (empty) or fura1, 1 for measurement or fura2
    #intarr(3,p1.frames,p1.odors+1); x/y/quality, frames, data(odor/wavelength)
    MovementList = np.zeros((3, p1.metadata.frames), dtype=int) # I would take 2 odors for backwards compatibility
####################
# Problem here: odors is abolished in this Python setting, but for FURA I don't have a solution yet
# the thing is: I cannot do a movement correction separately for the two wavelengths, without alignem them,
# because they might move astray.
# For new data, movement correction should use new tools anyway. 
#
#
#	;go through raw data, do movement correction, for each 'odorset' separatedly (e.g. also for the two wavelengths in FURA)
    if MovementFlag in [1,2]:
#	IF ((MovementFlag ge 1) AND (MovementFlag le 2)) THEN begin
#	for i=0,  p1.odors-1 do begin
#		IF (total(raw1[*,*,*,i]) gt 0) THEN begin
        if MathiasCorrection:
            print('MovementCorrectionMaster - MathiasCorrection still to do')
            # MovementCorrectionMathias()
#				;MovementCorrectionMathias, raw1[*,*,*,i], movementList[*,*,i] ;in ImageALMathias
#				movementList[0:1,*,i] = MovementCorrectionMathias(raw1[*,*,*,i])  ;eine Funktion??
#				;MovementCorrectionMathias gibt nur x/y, nicht qualität 'raus
        else:
            #MovementCorrection, raw1[*,*,*,i], movementList[*,*,i] # MatrixIN, shiftArray, flag
            print('MovementCorrectionMaster: now calling MovementCorrection - be patient!')
            (MatrixOUT, MovementList) = MovementCorrection(p1.raw1, flag)
            print('MovementCorrectionMaster: now done with MovementCorrection.')
    if MovementFlag in [2]:
        MovementList = ReadWriteMovementValues('write', MovementList, p1, flag)

    if MovementFlag in [3]:
#	;load movementList for flag set to 3
#	IF ((MovementFlag ge 3) AND (MovementFlag le 4)) THEN begin
#		ReadWriteMovementValues, 'read', movementList
#		print, 'Reading movement information - values are corrected for shrinkraktor! (MovementCorrectionMaster)'
#		IF (ShrinkFactor ge 2) then begin
#			movementList[0,*,*] = fix(movementList[0,*,*] / shrinkfactor)
#			movementList[1,*,*] = fix(movementList[1,*,*] / shrinkfactor)
#		endIF
#	endIF
        MovementList = ReadWriteMovementValues('read', MovementList, p1, flag)
        if ShrinkFactor > 1:
            MovementList[0:2,:] = (MovementList[0:2,:] / ShrinkFactor).astype(int)
        # now apply to data
        MatrixOUT = p1.raw1.copy
        MatrixOUT[:,:,frames] = np.roll(MatrixOUT[:,:,frames], bestXshift, axis=0)
        MatrixOUT[:,:,frames] = np.roll(MatrixOUT[:,:,frames], bestYshift, axis=1)

    if MovementFlag in [4,5]:
        print('MovementCorrectionMaster: flag 4,5 not implemented yet in phython')
#	;write info from one odor into the other one
#	IF  (MovementFlag eq 4) THEN begin
#		;which one is the odor that has information?
#		IF total(movementList[*,*,0]) eq 0 then begin
#			;0 is the empty odor
#			movementList[*,*,0] = movementList[*,*,1]
#		endIF else begin
#			;1 is the empty odor
#			movementList[*,*,1] = movementList[*,*,0]
#		endELSE
#	endIF
#	IF (movementFlag eq 5) THEN begin
#		ReadWriteMovementValues, 'read', movementList
#		;no movement correction, but extract shifts
#		referenceImage = fix(flag[LE_StartBackground])
#		referenceOdorBuffer = 1
#		p1.shiftX = movementList[0,referenceImage,referenceOdorBuffer]
#		p1.shiftY = movementList[1,referenceImage,referenceOdorBuffer]
#		monitorMovement = 0 ; no need to see the movement on screen
#		print, 'Movement correction OFF, shifts taken from moveList frame ',referenceimage,'; and odorBuffer ',referenceOdorBuffer
#	ENDIF else begin
#		;apply movementList to raw data
#		for i=0,  p1.odors do begin
#			for j=0, p1.frames-1 do begin
#				raw1[*,*,j,i] = shift(raw1[*,*,j,i],movementList[0,j,i],movementList[1,j,i])
#			endFor
#		endFOR
#	endELSE ;movementFlag 5
#
#	;check movement with screen output for flag set to 2
#	;show corrected data
#	IF monitorMovement then begin
#		;part1: plot shifts and quality
#		window, 2*p1.odors, xsize=250, ysize=250
#		loadCT, 39
#		;schleife über odors und x/y/qualität
#		rangeTop = max(MovementList(0:1,*,*))
#		rangeBot = min(MovementList(0:1,*,*))
#		plot, movementList[2,*,0], yrange=[rangeBot-1,rangeTop+1],color=255
#		oplot, movementList[1,*,0], color=254
#		oplot, movementList[0,*,0], color=140
#
#		;part 2, plot x/y intersection over time
#		for i=0,  p1.odors-1 do begin
#			IF (total(raw1[*,*,*,i]) gt 0) THEN begin
#				showMovement, raw1[*,*,*,i], i+p1.odors ;opens one window for each 'odor'
#			endIF
#		endFOR
#	endIF
#
#
#
    #now overwrite p1.raw1
    p1.raw1 = MatrixOUT
#end; MovementCorrectionMaster
    return p1 # end movementcorrectionmaster


# def loadDataMaster(flag, p1):
# #    ;correct flag setting
# #IF (fix(flag[LE_ShrinkFaktor]) eq 0) THEN flag[LE_ShrinkFaktor]=1
#     if flag["LE_ShrinkFaktor"] == 0:
#         print("ViewLoadData.loaddatamaster: flag.le_shrinkfactor == 0, add correction ")
# #;that has become necessary for pixel display and coordinate calculation
# #;in the loading routines 0 and 1 were already equivalent
# #;Giovanni, FEb.05
#     setup = flag["LE_loadExp"]
# #;flag to clip dark pixels to a minimum value, Gio Sept 2015
# #;default value 0, i.e. no clipping.
# #    ClipPixels = flag.le_ClipPixels
# #
# #      	   	;load experiment
#
#     # try to read dbb1 value as the absolute path of a VIEW-tiff. If there are any expected exceptions, abort.
#     try:
#         p1 = load_VIEW_tif(flag, p1)
#         setup = 30
#     except FileNotFoundError as fnfe:
#         pass
#     except AssertionError as ae:
#         if str(ae).startswith("Error reading"):
#             pass
#     except IOError as ioe:
#         if str(ioe).endswith("(3 expected)"):
#             pass
#
#     if (setup == 0):
#         print("ViewLoadData.loaddatamaster: setup is 0, old Berlin system - load not implemented in python yet")
# #				inFile = flag[stg_DataPath]+inputMark
# #				loadexp, InFile, raw1, foto1, dark1, p1
# #				parts = str_sep(inputMark, dirsign)		; separate parts of path+name
# #				info = size(parts)			; get info on variable PARTS, info(1) holds size of array
# #				experiment = parts(info(1)-1)		; name is at last position of array PARTS
# #				p1.experiment = experiment
# #			endIF
#
#     elif (setup == 3):
#         p1 = loadTILL(flag, p1)
# #			IF setup eq 3 THEN begin
# #				IF fix(flag[VIEW_No4Darray]) THEN begin
# #					loadTILL_3Dim, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #				endIF else begin
# #					loadTILL, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #				endELSE
# #			endIF
#     elif (setup == 4):
#         p1 = loadFURA(flag, p1)
# #			IF setup eq 4 THEN loadFURA, inputMark, measu2, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #			;setup 4 is compatible with VIEW_no4Darray
# #
# #			IF setup eq 5 THEN loadFURA_and_CaGr, inputMark, measu2, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #
# #			IF setup eq 6 THEN loadZseries, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #
# #			IF setup eq 7 THEN begin
# #				loadTILL, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #				shuffleMultipleLayers, 3 ; 3 for three layers, recorded in one film, to be splitted as if 3 odors
# #			endIF
# #
# #			;load till photonics setup, with split image of two wavelength,
# #			;treat as FURA data
# #			IF setup eq 8 THEN loadMicroImager, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #
# #
# #			IF setup eq 13 THEN loadTILLbyte, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #
# #			IF setup eq 14 THEN loadIDLraw, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #
# #
# #			IF setup eq 17 THEN begin
# #				print, 'loading using setup type 17'
# #				loadTILL3Layer, inputMark, measu2, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #			;loads measurements done on threelayers in 3 separate dbb files, and glues them side by side
# #			; Inga, Aug. 2014, Konstanz
# #			endIF
# #
# #			;setup 9 loads single wavelength data, using the DBB-file specified in the measu2 column of the .lst file (TILL data)
# #			;usefult to load only the slave, or only the 380nm measurements in FURA data
# #			IF setup eq 9  THEN loadTILL, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 2
# #
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			IF setup eq 15 THEN loadOlympusR, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			IF setup eq 20 THEN loadZeiss, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
#     elif (setup == 20):
#         p1 = loadZeiss(flag, p1)
# #
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			;21 reads a .tif file (the .lst may contain any extension, that is ignored and replaced by .tif
# #			IF setup eq 21 THEN Load3DTiff, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #			;22 reads a _affine.tif
# #			IF setup eq 22 THEN Load3DTiff, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #			;23 reads a _full.tif
# #			IF setup eq 23 THEN Load3DTiff, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #
# #
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			IF setup eq 26 THEN load_3DArray_Raw, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			IF setup eq 30 THEN load_redshirtimaging, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst', 1
# #
# #
# #			;load format from Olympus Imaging system, Andy March 2010
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			IF setup eq 40 THEN loadOlympusR, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
# #			;inputmark can be the file name, or the line tag number in the .lst file .
# #			IF setup eq 41 THEN loadOlympusR_ratio, inputMark, flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.lst'
#     elif setup == 30:  # internal tif format
#         pass  # should have been read above
#     elif (setup == 665): #generate test data, use odor concentration as max value
#         p1 = LoadRaw666(flag, p1, peaksignal = -10)
#         #generate test data, peaksignal -10
#     elif (setup == 666):
#         p1 = LoadRaw666(flag, p1, peaksignal = p1.odor_nr)
#         # this allows to use the column odor concentration in a list file to generate different signal sizes
#     elif (setup == 667): #generate test data
#         p1 = LoadRaw666(flag, p1, peaksignal = 10)
#         #generate test data, peaksignal 10
#     else:
#
#         print("ViewLoadData.loaddatamaster: setup load not implemented in python yet")
#         raise NotImplementedError
# #
# #;SlaveCorrection ##NOT IMPLEMENTED IN PYTHON - from old mirror system
# #;if the image of the slave is shifted/rotated/distorted, correct it
# #IF ((setup eq 4) OR (setup eq 8)) THEN begin
# #	;the correction parameters are in file ....slaveMod
# #	;in the directory with the .inf files
# #	;a file 'all.slaveMod' is active for ALL files in that /listen directory
# #	;a file 'animal.slaveMod' overwrites 'all.slaveMod' should both be present
# #	modifyFile1 = flag[stg_OdorInfoPath]+flag[stg_ReportTag]+'.slaveMod'
# #	modifyFile2 = flag[stg_OdorInfoPath]+'all'+'.slaveMod'
# #	existFile1  = existFile(modifyFile1)
# #	existFile2  = existFile(modifyFile2)
# #	IF (existFile1 OR existFile2) THEN begin ;modify if there is the necessary information
# #		;read that information
# #		IF existFile1 THEN	modifyFile = modifyFile1 ELSE modifyFile = modifyFile2
# #		openR, unit, modifyFile, /GET_LUN
# #		line = ''
# #		readF, unit, line
# #		readF, unit, line ;the second line contains the modify information
# #		free_lun, unit ;close the file
# #		print, 'LoadDataMaster: Modifying SLAVE according to information in file: ',modifyFile
# #		print, 'Modify parameters are: ', line
# #		;line is: shiftX	shiftY	mod	rotAng	magni	rotCentX	rotCentY
# #		shiftArray = str_sep(line, string(9b))
# #		;the slave to be modified is the dataset raw(*,*,*,1)
# #		;first the shift, then the rotation
# #		for i=0, p1.frames-1 do begin
# #			b = float(reform(raw1(*,*,i,1))) ; take that frame, remove spurious dimensions
# #			b = shift(b,shiftArray(0),shiftArray(1))
# #			;modify this slice - after shift
# #			b = rot(b,        shiftArray(3),shiftArray(4)/100.0,shiftArray(5),shiftArray(6), /interp, /pivot)
# #			;Result = ROT( A, Angle,        [Mag,               X0,           Y0]         [, /INTERP] [, CUBIC=value{-1 to 0}] [, MISSING=value] [, /PIVOT] )
# #			;rotate around point x0/y0 by Angle clockwise, Magnify by Mag
# #			raw1(*,*,i,1) = fix(b)
# #		endFor
# #	endIF
# #endIF
# #
# #;movementCorrection
# #;the settings in movementCorrection affect the shift correction - therefore, movement correction preceeds shift correction
#     if (flag["CSM_Movement"] > 0):
#         p1 = MovementCorrectionMaster(p1, flag)
# #endIF ; movementCorrection
# #
# #
# #;shift correction: if flag is 0: no shift here, but coordinates are shifted
# #;				   if flag is 1: shift here   ,     coordinates are not shifted
# #;				   if flag is 2: shift entry in p1.shift is ignored altogether (e.g. when movement correction contains shift information)
# #$ DataShift not translated yet
# #IF (fix(flag[CSM_DataShift]) eq 1) THEN begin
# #	print, 'LoadDataMaster: shift Data by ',p1.shiftX, p1.shiftY
# #	;correct shifts
# #	p1.shiftX = (-1)*p1.shiftX / fix(flag[LE_ShrinkFaktor])
# #	p1.shiftY = (-1)*p1.shiftY / fix(flag[LE_ShrinkFaktor])
# #	;shift the data instead of shifting the masks
# #	raw1 = shift(raw1,p1.shiftX,p1.shiftY,0,0)
# #	;put the shifts to 0, to avoid that the masks will be shifted
# #	p1.shiftX = 0
# #	p1.shiftY = 0
# #endIF
# #IF (fix(flag[CSM_DataShift]) eq 2) THEN begin
# #	print, 'LoadDataMaster: shift information ignored'
# #	;put the shifts to 0, to avoid that the masks will be shifted
# #	p1.shiftX = 0
# #	p1.shiftY = 0
# #endIF
# #
# #
# #
# #IF (fix(flag[VIEW_No4Darray]) eq 1) THEN begin
# #	IF ((setup eq 4) OR (setup eq 3) OR (setup eq 8)) THEN begin
# #		;for these options specific care has been taken
# #	end else begin
# #		;remove the odor buffer 0
# #		;watchout with FURA data
# #		raw1 = raw1(*,*,*,1:p1.odors)
# #		p1.odors = p1.odors-1
# #		odor = (odor - 1)>0
# #		IF (fix(flag[LE_UseFirstBuffer]) ge 1) THEN flag[LE_UseFirstBuffer] = flag[LE_UseFirstBuffer] - 1
# #		print, '*****************LoadDataMaster: deleted odor buffer 1, only 0. '
# #	endELSE
# #endIF
# #
#         ## skip NOT IMPLEMENTED in python (yet?)
# #;skip frames if requested
# #SF_upFront 	= fix(flag(CSM_SkipFrmUpFront))
# #SF_atBack 	= fix(flag(CSM_SkipFrmAtBack))
# #SkipFrames  = (SF_upFront ne 0) OR (SF_atBack ne 0)
# #IF SkipFrames THEN begin
# #	;if the numbers are negative, they are relative to Stimulus ONSET, otherwise to FIRST FRAME,
# #	IF SF_upFront lt 0 THEN begin
# #		SK_firstFrame = p1.stimulus_on + SF_upFront
# #	endIF else begin
# #		SK_firstFrame = SF_upFront
# #	endELSE
# #	;if the numbers are negative, they are relative to Stimulus ONSET, otherwise to FIRST FRAME,
# #	IF SF_atBack lt 0 THEN begin
# #		SK_lastFrame = p1.stimulus_on - SF_atBack
# #	endIF else begin
# #		SK_lastFrame = SF_atBack
# #	endELSE
# #	IF (SF_atBack eq 0) THEN begin
# #		SK_lastFrame = p1.frames -1
# #	endIF
# #	;error messages
# #	IF (SK_firstFrame lt 0) then begin
# #		print, 'skipping frames with wrong parameters in LoadDataMaster.pro: SK_firstFrame = ',SK_firstframe
# #		stop
# #	endIF
# #	IF (SK_lastFrame ge p1.frames) then begin
# #		print, 'skipping frames with wrong parameters in LoadDataMaster.pro: SK_lastFrame = ',SK_lastFrame
# #		stop
# #	endIF
# #	SK_Frames = SK_lastFrame - SK_firstFrame + 1
# #	IF SK_Frames lt 1 THEN begin
# #		print, 'skipping frames with wrong parameters in LoadDataMaster.pro: SK_Frames = ',SK_Frames
# #		stop
# #	endIF
# #	;now cut the excess frames
# #	raw1 = raw1(*,*,SK_firstFrame:SK_lastFrame,*)
# #	print, 'Frames skipped. Kept frames from ',SK_firstFrame,' to ',SK_lastFrame
# #	;correct parameters
# #	p1.frames 		= SK_Frames
# #	p1.stimulus_on 	= P1.stimulus_on  - SK_firstFrame
# #	p1.stimulus_end = p1.stimulus_end - SK_firstFrame
# #	p1.stimulus_del = p1.stimulus_del - SK_firstFrame*p1.trial_ticks
# #	p1.stim2ON		= p1.stim2ON	  - SK_firstFrame
# #	p1.stim2OFF     = p1.stim2OFF	  - SK_firstFrame
# #	p1.stim2_del	= p1.stim2_del	  - SK_firstFrame*p1.trial_ticks
# #endIF ;SkipFrames
# #
# #IF ClipPixels gt 0 THEN begin
# #    print, 'LoadDataMaster: Clip data to ', ClipPixels
# #    raw1 = raw1 > ClipPixels
# #endIF
# #
# #IF ClipPixels lt 0 THEN begin
# #	;clips pixels to the positive value, and creates a mask file that can be used for overviews
# #	;example of how to run: set to -300, all pixels <300 will be set to 300, and a mask for the remaining pixels is saved
# #	;for faster performance, the second time the flag can be set to 300, because the mask file already exists
# #	ClipPixels = (-1)*ClipPixels
# #    print, 'LoadDataMaster: Clip data to ', ClipPixels
# #    raw1 = raw1 > ClipPixels
# #    ;create mask
# #    IF (fix(flag[VIEW_No4Darray]) eq 1) THEN dataPlace = 0 ELSE dataPlace = 1
# #    copyData = reform(raw1(*,*,*,dataPlace)) ;take the measurement
# #    copyData = copyData gt ClipPixels ;gives 1 for all pixels gt clip
# #    ;because we are not working on single frames, average for the time course
# #    copyData = total(copyData, 3);sums across frames, now floating point
# #    copyData = copyData / p1.frames;
# #    copyData = copyData gt 0.5 ; take all pixels where for at least half of the frames
# #    ; the value was larger than ClipPixels
# #    maskFrame = byte(copyData) ;convert to byte
# #    ;no save this mask to file
# #    ;file name taken from singleOverview.pro
# #    areaFileName =  flag[stg_OdorMaskPath]+flag[stg_ReportTag]+'.Area'
# #    print, 'LoadDataMaster.pro: saving area file to ',areaFileName
# #    save, filename=areaFileName, maskFrame
# #    copyData = 0B ; empty memory space
# #    maskFrame = 0B
# #endIF ; ClipPixels lt 0
# #
# #
#     data_sampling_period = pd.Timedelta(f"{p1.trial_ticks}ms")
#     p1.pulsed_stimuli_handler.initialize_stimulus_offset(flag["mv_correctStimulusOnset"], data_sampling_period)
#
#     print('ViewLoadData.LoadDataMaster: Data loaded, setup type ',setup)
#     return # no return any more. p1