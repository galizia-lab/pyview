#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Oct 12 08:56:46 2018

@author: galizia
"""

import numpy as np
#import FID_names as FID_names

from time import time
from datetime import timedelta
#import datetime
#import numpy as np
#import pandas as pd
#import os
#from ggplot import *
# import struct
import matplotlib.pyplot as plt
#from matplotlib.backends.backend_pdf import PdfPages
from moviepy.editor import VideoClip
from moviepy.video.io.bindings import mplfig_to_npimage


def calc_timetrace(imaging_Data, mask):
    ##section to flatten array with mask
    xpixels, ypixels, frames = imaging_Data.shape
    timetrace = np.zeros(frames)
    mask_sum = mask.sum()
    for i in range(frames): #I'm sure there is an inbuild way to get the time trace, I'll search for it later
# np.mean(array, axis=(1,2))
        # temp = mask * imaging_Data[:,:,i]
        temp = np.multiply(mask,imaging_Data[:,:,i]) #is this multiplication better?
        timetrace[i] = temp.sum()/mask_sum
    return timetrace
#end calc_timetrace

def secondsToStr(t):
    return str(timedelta(seconds=t))

def log(s='start counting', elapsed=None):
    start = time()
    line = "="*42
    print(line)
    print(secondsToStr(time()), '-', s)
    if elapsed:
        print("Elapsed time:", elapsed)
    print(line)
    print()
    return start

def endlog(start, s="End Program"):
    end = time()
    elapsed = end-start
    log(s, secondsToStr(elapsed))

def now():
    return secondsToStr(time())

def save_movie_file_xyt(dataMtrx, fps=24, bitrate="256k", movie_filename=''):
    #Oct18: procedure adapted from FID_out
    # dataMtrx has shape x,y,t
    # lcl_flags needed for filename, if filename is given, ignore lcl_flags
    start = log("save_movie_file_test2")
    if movie_filename == '':
        movie_filename = 'dummyMovie.mp4'
    zlen = dataMtrx.shape[2]
    # scale matrix to min, max
    scaleMin = dataMtrx.min()
    scaleMax = dataMtrx.max()
    duration = (zlen-1)/fps #frames/fps
    fig = plt.figure()
    ax = fig.add_subplot(111)
    fig.tight_layout(pad=1.0)
    def make_frame(t):
        #gives frame at time t
        ax.clear() #without this, it is very slow
        ax.axis('off')
        #ax.set_title("Frame " + str(int(zlen/duration*t)) + "/" + str(zlen))
        ax.imshow(dataMtrx[:,:,int(zlen/duration*t)], clim=(scaleMin, scaleMax))
        #fig.colorbar()
        return mplfig_to_npimage(fig)
    animation = VideoClip(make_frame, duration=duration)
    # export as a video file
    # animation.write_gif(movie_filename+'.gif', fps=fps) #gif is larger
    animation.write_videofile(movie_filename, fps=fps, bitrate=bitrate)
    plt.close()
    endlog(start, "save_movie_file_xyt")
