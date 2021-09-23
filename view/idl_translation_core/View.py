# -*- coding: utf-8 -*-
"""
Created on Tue Sep 18 10:46:39 2018

@author: Giovanni Galizia

file to collect the routines that were in the folder "View" in IDL
"""

import numpy as np
import scipy.ndimage as sci
import scipy as sc


def SpaceFilter(frame, filtersize):
    '''
    ;this funtion filters a picture array in space with any desired kernel
    ; used for spacial smoothing of pictures
    ; Author Jasdan Joerges 12/95
    ; parameters:
    ; frame         input frame
    ; filtersize	size of spacial filter
    ; p		parameterset
    ; results:	FilteredFrame
    '''
    def DiagonalKernel(kernel,i,kernelSize):
        # i and kernelSize are separate because of the recursive nature
        # for a square kernel size 100, call DiagonalKernel(kernel,100,100)
        if kernelSize % 2 == 0: #number is even
            print('IncreaseCenterByOne not for even numbers')
            i = 1 # prevent eternal loops
        if i > (kernelSize+1)/2: 
            print('View/SpaceFilter: working on kernel with i = ',i)
            #increase central region by one
            i -= 1
            kernel[kernelSize-i:i,kernelSize-i:i] += 1
            DiagonalKernel(kernel,i,kernelSize)
        else: i = 1
        return kernel


    if filtersize > 0: #triangular filter; in Jasdans version, they were done by hand. Here I use a recursive function
        kernelSize = filtersize
        #kernel = IDL.fltarr(kernelsize, kernelsize)
        kernel = np.ones([kernelSize, kernelSize])
            
        DiagonalKernel(kernel,kernelSize, kernelSize)
        
        frame = sc.signal.convolve(frame,  kernel, mode='same')
#    if filtersize == 5:  ###example for Jasdan's solution
#    kernel(*,*) = 	[1,1,1,1,1,		$ ; triangular 5x5
#			 1,2,2,2,1,		$
#			 1,2,3,2,1,		$
#			 1,2,2,2,1,		$
#			 1,1,1,1,1]
#  END
            
            ## default: all values are 1
    #;better than boxcar: triangular window average
    else: #negative filter: gaussian. In Jasdans version, it was a filter + convolve
        print('View/SpaceFilter: Gaussian filter size ',filtersize)
        frame = sci.gaussian_filter(frame, -filtersize, mode='nearest')
#    -7: BEGIN
#	kernel(*,*) = 	[-0.00580155,-0.00580155, -0.00580155, -0.00580155, -0.00580155, -0.00580155, -0.00580155,		$ ; triangular 7x7
#			      -0.00580155,-5.12869e-09,-5.12869e-09,-5.12869e-09,-5.12869e-09,-5.12869e-09,-0.00580155,		$
#			      -0.00580155,-5.12869e-09, 0.253284   , 0.253284   , 0.253284   ,-5.12869e-09,-0.00580155,		$
#			      -0.00580155,-5.12869e-09, 0.253284,    0.500000,    0.253284,   -5.12869e-09,-0.00580155,		$
#			      -0.00580155,-5.12869e-09, 0.253284   , 0.253284   , 0.253284   ,-5.12869e-09,-0.00580155,		$
#			      -0.00580155,-5.12869e-09,-5.12869e-09,-5.12869e-09,-5.12869e-09,-5.12869e-09,-0.00580155,		$
#			      -0.00580155,-0.00580155, -0.00580155, -0.00580155, -0.00580155, -0.00580155, -0.00580155]
#  END
#FilteredFrame = convol(Frame, kernel, /edge_truncate) / total(kernel)
#;FilteredFrame  = median(frame,filtersize)
#return, FilteredFrame
#end ; of program
    return frame






