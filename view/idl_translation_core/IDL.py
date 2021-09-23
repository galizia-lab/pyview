# -*- coding: utf-8 -*-
"""
Created on Sat Sep 15 13:42:30 2018

@author: Giovanni Galizia

collection of IDL commands
and other useful snippets for the IDL_view->python translation
"""
import logging
from tkinter import filedialog
import tkinter as tk
import numpy as np
import scipy.ndimage as sci
#import skimage as ski
import PIL as PIL
from PIL import ImageDraw, ImageFont, ImageOps, Image
import os

import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap
from matplotlib.colors import hsv_to_rgb


#outFile = dialog_pickfile(/WRITE, path=flag[stg_odorReportPath],file='TIF_'+p1.experiment)
def dialog_pickfile(path, default = '', write=True, defaultextension = 'tif'):
#IDL:    Result = DIALOG_PICKFILE( [, DEFAULT_EXTENSION=string] [, /DIRECTORY] [, DIALOG_PARENT=widget_id] [, DISPLAY_NAME=string] [, FILE=string] [, FILTER=string/string array] [, /FIX_FILTER] [, GET_PATH=variable] [, GROUP=widget_id] [, /MULTIPLE_FILES] [, /MUST_EXIST] [, /OVERWRITE_PROMPT] [, PATH=string] [, /READ | , /WRITE] [, RESOURCE_NAME=string] [, TITLE=string] )
    # path is given, file is output
    root = tk.Tk()
##    root.outCanvasFile = filedialog.asksaveasfilename(mode='w', initialdir = flag.stg_odorReportPath, defaultextension=".tif")
##    root.outCanvasFile = filedialog.asksaveasfilename(initialdir = 'C:/Users/Giovanni Galizia/')
#    root.outCanvasFile = filedialog.asksaveasfilename(initialdir = path)
#    if outCanvasFile is None: # asksaveasfile return `None` if dialog closed with "cancel".
#        outCanvasFile = default
#    path = 'C:/Users/Giovanni Galizia/'
    root.withdraw() # we don't want a full GUI, so keep the root window from appearing
    #root.focus_force()
#    root.lift()
    root.attributes("-topmost", True)
#    svg_filename = tkFileDialog.asksaveasfilename(title='SVG export filename',defaultextension = 'svg',initialdir = IDT_group_dir);
    if write:
        filename = filedialog.asksaveasfilename(parent = root, title='TIF export filename',defaultextension = 'tif',initialdir = path)
    else:
        filename = filedialog.askopenfilename(parent = root, title='Open existing file',defaultextension = defaultextension, initialdir = path)
    return filename    
#   outside: open file like this:
#    file = open(name,'w')
    
def bytarr(x,y):
    return np.zeros([x,y], dtype=np.uint8)

def fltarr(x,y):
    return np.zeros([x,y], dtype=np.float64)

def smooth(arrayND, filterSize):
    '''
    arrayND or any dimenstion, filterSize applied to all dimenstion
    in IDL it was a boxcar filter, here I use gaussian
    in IDL filterSize is a single value, here it can be a tuple
    '''
    return sci.gaussian_filter(arrayND, filterSize, mode='nearest')


def xyouts(x,y, text, img, orientation=90, fill=255, align = 'left'):
    '''
    tries to replicate the IDL xyouts command, approximately
    align can be 'left' or 'right' or 'center', implemented by shifting the coordinates (corresponds to 0, 1, 0.5 in IDL)
    x, y are lower left corner of text box for horizontal text
    '''
#;           xyouts, NextPosition(0)+p1.format_x+border-2, NewSizeCanvas(1)-NextPosition(1)-p1.metadata.format_y, strTrim(string(fix(minimum*annotateFactor)),2), /device, ALIGNMENT=0, ORIENTATION=90
#### analysis#;           xyouts, 
#                               x coordinate: NextPosition(0)+p1.format_x+border-2, 
#                               y coordinate: NewSizeCanvas(1)-NextPosition(1)-p1.format_y, 
#                               text2write:   strTrim(string(fix(minimum*annotateFactor)),2), 
#                               where to write: /device, 
#                               ALIGNMENT=0, #0 means left alignment
#                               ORIENTATION=90 #90 means vertical going up  
#def add_vertical_text(x,y,text,img, fill):
    #adds text into img, vertically upwards
    width, height = img.size
    if x > width: print('IDL.xyouts - text appears to be outside x range')
    if y > height: print('IDL.xyouts - text appears to be outside y range')
    #img = img.rotate(-orientation) #rotate the original image
    #this does not work, because it rotates WITHIN the window
    # the coordinates are different due to the rotation
    if orientation == 90:
        img = img.transpose(Image.ROTATE_90)
        rot_x = y
        rot_y = width - x
    elif orientation == 0:
        rot_y = y
        rot_x = x
    else:
        print('IDL.xyouts: this value of rotation not implemented yet. If not 0,90,180,270, think hard')
    # x' = x*cos + y*sin
    # y' = -x*sin + y*cos
    # -- or as vectors --
    #  x'      cos  sin       x
    #(   ) = (          ) * (   )
    #  y'     -sin  cos       y
    # but this does not work, because I do not know if to subtract negative values from x or from y
#    orientation = 180
#    r = np.deg2rad(orientation)
#    rot_x = x*np.cos(r) + y*np.sin(r)
#    rot_y = -x*np.sin(r) + y*np.cos(r)
#    print(rot_x, rot_y)
    # now write the text into this place
    draw = PIL.ImageDraw.Draw(img)
    # corect x axis if right alignement
    text_box_size = draw.textsize(text)
    if align.lower() == 'right':
        rot_x = rot_x - text_box_size[0]      
    if align.lower() == 'center':
        text_box_size = draw.textsize(text)
        rot_x = rot_x - text_box_size[0]/2      
    #coordinates are different from IDL, it seams - so shift the y by the text height
    rot_y = rot_y - text_box_size[1]
    #draw the text
    draw.text((rot_x, rot_y),text,fill=fill)#,font=font)
    #rotate back
    if orientation == 90:
        img = img.transpose(Image.ROTATE_270)
    return img #end xyouts


def gio_get_filenames(extension, title):
    import tkinter as tk
    from tkinter.filedialog import askopenfilenames
    root = tk.Tk()
    root.withdraw() # so that windows closes after file chosen 
    root.attributes('-topmost', True)
    filenames = askopenfilenames(
                parent=root,
                title=title,
                filetypes=[('settings files', extension), ('all files', '*')]
                ) # ask user to choose file
    return filenames


def restore_maskframe(flag):
    areafilename = os.path.join(flag.STG_OdormaskPath,flag.STG_ReportTag) + '.Area'
        #os.path.isfile(areaFileName)
    if not(os.path.isfile(areafilename)):
        print('CalcSigAll3000.pro: AreaFileName does not exist :', areafilename)
        ## pick the right file name, to do. 
        areafilename = gio_get_filenames('.Area', "Choose perimeter file .Area")[0] #only the first file name, if more were chosen
#		areaFileName = Dialog_Pickfile(Path=flag[stg_OdorMaskPath], get_Path = inPath, Filter='*.Area', title='Choose perimeter file!')
#		flag[stg_OdorMaskPath] = inpath
    from scipy.io.idl import readsav #command to read IDL files
    #temp = readsav(areaFileName, verbose=True) #reads IDL structure into temp. The Area file is in maskframe
    maskframe = readsav(areafilename).maskframe #only works because it was saved with the name maskFrame
    print('IDL.py: restored area file ',areafilename)
    return maskframe


#bytscl(overviewframe, MIN=setminimum, MAX=setmaximum, TOP=!d.table_size)
def bytscl(inf, MIN=0, MAX=255, TOP=255):
    inframe = inf.copy().astype('float')
    inframe = np.clip(inframe, MIN, MAX)
    inframe -= MIN
    inframe *= TOP/(MAX-MIN)  #image *= (255.0/image.max())
    #inframe *= TOP/MAX  #image *= (255.0/image.max())
    #astype does not round, but floors
    inframe = inframe + 0.5
    return inframe.astype('uint8')

##    frame2 = rebin(frame2, (p1.format_x) * zoomfactor, p1.format_y * zoomfactor, sample = 1)
def rebin(frame, newxsize, newysize, sample=1):
    from skimage.transform import resize
    #interp = 'bilinear'
    #if sample == 1: interp = 'nearest'
    #plt.imshow(resize(frame2, frame2.shape, mode='constant')).astype('uint8')
    print(newxsize, newysize)
    outframe = resize(frame, (newxsize,newysize), mode='constant')#, interp=interp)
    return outframe.astype('uint8')


#write_tiff, outCanvasFile, TIFFCanvas, red=r, blue=b, green=g, xresol=A4resolution, yresol=A4resolution
def write_tiff(outfile, MyArray, red, green, blue, xresol=100, yresol=100):
    """
    simulate the IDL write_tiff command, with only those options that I used in my view program
    writes an 8bit TIFF file, with the palette defined by red,blue,green
    input is array, a uint8 array
    """
    #21.8.2019 write tiff is only used for Canvas, so far, and the image is rotated.
    #fix: rotate the image here, and rotate it back in read_tiff
    MyArray = np.rot90(MyArray)
    #convert array into image
    mode = 'P' #(8-bit pixels, mapped to any other mode using a color palette
    img = PIL.Image.new(mode, MyArray.shape)
    img = PIL.Image.fromarray(MyArray) #creates an image into object window10
    # add palette
    #make sure colors are 8bit
    palette = palette_IDL2PIL(red,green,blue)
    img.putpalette(palette)    
    #save to file
    img.save(outfile, dpi=(xresol, yresol))
    print('IDL.write_tiff: written 8bit tiff file to: ', outfile)
    return #nothing to give back

#read_tiff(outCanvasFile, R, G, B)
def read_tiff(filename):
    '''
    reads a tiff file, returns the array, and the red, green, blue palette 
    emulates the IDL read_tiff with the options I used in view
    '''
    img = PIL.Image.open(filename)
    img_array = np.array(img)
    # rotate back, i.e. 3 times by 90 deg
    img_array = np.rot90(img_array,3)
    #here is the palette
    palette = img.getpalette()
    IDLpalette = palette_PIL2IDL(palette)
    # palette is a single list with R, G, B, R, G....
    return (img_array, IDLpalette)

def palette_IDL2PIL(red,green,blue):
    red = red.astype('uint8')
    blue = blue.astype('uint8')
    green = green.astype('uint8')
    rgb = [red, green, blue]
    palette = [val for tup in zip(*rgb) for val in tup]
    return palette

def palette_PIL2IDL(palette):
    red = palette[0::3]    
    green = palette[1::3]    
    blue = palette[2::3]    
    return (red, green, blue)

def palette_pyplot2PIL(pyplot_cm):
    ctP = pyplot_cm(np.linspace(0,1,256))
    #R is in ctP[:,0]
    R = ctP[:,0]*255
    G = ctP[:,1]*255
    B = ctP[:,2]*255
    return (R, G, B)


def createPalette(SO_MV_colortable):
    """
    creates an RGBA palette (0-255) as tuple (r,g,b,a)
    extension of interpretation of SO_MV_colortable, allowing flags to have multiple expected types, FT_*Frame ->mv_*Frame
    based on the numbers that I used in IDL. Mostly based on DefineExplicitCt in the tools folder
    Most numbers not implemented yet - just translate as necessary
    """
##from IDL
#;set 11: equal saturation, different hue
#;define it in hsv system
#s = replicate(1.0, 255)
#v = replicate(1.0, 255)
#h = 255-findgen(255) ;starting with blue, go to red (the entire circle is 360 deg, here we use 255 deg)
#;load these values, get the corresponding r,g,b values
#tvlct, h, s, v, /hsv
#tvlct, r, g, b, /get
#;define color table 11
#modifyct, 11, 'HSVconst', r, g, b

    #from IDL, define 11
    hsv = np.zeros((256, 3))
    hsv[:, 0] = np.linspace(255/360, 0, 256) #in IDL, circle 360  - to to 255
    hsv[:, 1] = 1.
    hsv[:, 2] = 1. # np.linspace(0, 1, 512)[:, np.newaxis]
    rgba = np.ones((256, 4))
    rgba[:,0:3] = hsv_to_rgb(hsv) # transparency a  fixed to 1
    
    #define color map 11
#    IDLcm11 = ListedColormap(rgba, name='HSVconst')
    rgba_11 = rgba.copy()
    
    #;into 12, set bottom white, top black
    #r1 = r    & g1 = g    & b1 = b
    #r1(0)=255 & g1(0)=255 & b1(0)=255
    #r1(255)=0 & g1(255)=0 & b1(255)=0
    #modifyct, 12, 'HSVconstWB', r1, g1, b1
    rgba[0,:] = [1,1,1,1]
    rgba[-1,:] = [0,0,0,1]
#    IDLcm12 = ListedColormap(rgba, name='HSVconstWB')
    rgba_12 = rgba.copy()
    
    
    #;into 13, set bottom black, top white
    rgba[-1,:] = [1,1,1,1]
    rgba[0,:] = [0,0,0,1]
#    IDLcm13 = ListedColormap(rgba, name='HSVconstBW')
    rgba_13 = rgba.copy()

    
    #;into 14, set center range centersize to gray
    #;left part via cyan to blue
    #;right part via yellow to red
    #;0 to black; 255 to white
    
    rgba[0,:] = [1,1,1,1] #r1(255)=255 & g1(255)=255 & b1(255)=255
    rgba[-1,:] = [0,0,0,1] #r1(*)=0     & g1(*)=0     & b1(*)=0
    centersize = 10
    grayValue  = 180/255
    p1  = 64
    p2l = 128 - centersize
    p2r = 128 + centersize
    p3  = 192
    #;part from blue to cyan, range 0 to p1
    rgba[1:p1, 0] = 0 #r1(0:p1-1)	=	0
    rgba[1:p1, 1] = np.linspace(0,1,p1-1) #g1(0:p1-1)	=	createLinearArray(0,255,p1)
    rgba[1:p1, 2] = 1 #b1(0:p1-1)	=	255
    #;part from cyan to gray, range p1 to p2l
    rgba[p1:p2l,0] = np.linspace(0,grayValue,p2l-p1) #r1(p1:p2l-1)	=	createLinearArray(0  ,grayvalue, p2l-p1)
    rgba[p1:p2l,1] = np.linspace(1,grayValue,p2l-p1)#g1(p1:p2l-1)	=	createLinearArray(255,grayvalue, p2l-p1)
    rgba[p1:p2l,3] = np.linspace(1,grayValue,p2l-p1)#b1(p1:p2l-1)	=	createLinearArray(255,grayvalue, p2l-p1)
    #;part constant gray, range p2l to p2r
    rgba[p2l:p2r,0:3] = grayValue #r1(p2l:p2r-1)	=	grayvalue
    #g1(p2l:p2r-1)	=	grayvalue
    #b1(p2l:p2r-1)	=	grayvalue
    #;part from gray to yellow, range p2r to p3
    rgba[p2r:p3,0] = np.linspace(grayValue,1,p3-p2r) #r1(p2r:p3-1)	=	createLinearArray(grayvalue,255, p3-p2r)
    rgba[p2r:p3,1] = np.linspace(grayValue,1,p3-p2r)#g1(p2r:p3-1)	=	createLinearArray(grayvalue,255,  p3-p2r)
    rgba[p2r:p3,2] = np.linspace(grayValue,0  ,p3-p2r)#b1(p2r:p3-1)	=	createLinearArray(grayvalue,  0, p3-p2r)
    #;part from yellow to red, range p3 to 2554
    rgba[p3:256,0] = 1 #r1(p3:254)		=	255
    rgba[p3:256,1] = np.linspace(1,0,256-p3) #g1(p3:254)		=	createLinearArray( 255,  0,  255-p3)
    rgba[p3:256,2] = 0 #b1(p3:254)		=	0
    #;rest bottom to black,top to white
    #r1(0)=0     & g1(0)=0     & b1(0)=0
    #r1(255)=255 & g1(255)=255 & b1(255)=255
    #modifyct, 14, 'GrayCenter', r1, g1, b1; for britons: GreyCentre
    #IDLcm14 = ListedColormap(rgba, name='GrayCenter')
    rgba_14 = rgba.copy()

#
#;into 15, use 14 above, set center range centersize to gray
#;left part via cyan to blue
#;right part via yellow to red
#;0 to white; 255 to black
#;rest bottom to white,top to black
#r1(255)=0     	& g1(255)=0     & b1(255)=0
#r1(0)=255 		& g1(0)=255 	& b1(0)=255
#modifyct, 15, 'GrayCenterBW', r1, g1, b1; for britons: GreyCentre
#
#
#;make cyan-blue-*black*-red-yellow-white
#
#;position 0 is black
#r(0) = 0    & g(0) = 0    & b(0) = 0
#;positions 1 to 63 from cyan to (almost) blue
#r(1:63)=0 &  g(1:63) = byte(255*(1 - findgen(63)/63)) & b(1:63) = 255
#;positions 64 to 127 from blue to (almost) black
#r(64:127)=0 &  g(64:127) = 0 & b(64:127) = byte(255*(1 - findgen(64)/64))
#;positions 128 to 170 from black to (almost) red
#r(128:170) = byte(255*(findgen(43)/43)) & g(128:170) = 0 & b(128:170) = 0
#;position 171 to 213 from red to (almost) yellow
#r(171:213) = 255 & g(171:213) = byte(255*(findgen(43)/43))  & b(171:213) = 0
#;position 214 to 255 from yellow to white (divide by one less to get maximum in the array)
#r(214:255) = 255 & g(214:255) = 255 & b(214:255) = byte(255*(findgen(42)/41))
#modifyct, 36, 'cb_black_ryw', r, g, b
#
#
#;make cyan-blue-*black*-red-yellow
#
#;position 0 is black
#r(0) = 0    & g(0) = 0    & b(0) = 0
#;positions 1 to 63 from cyan to (almost) blue
#r(1:63)=0 &  g(1:63) = byte(255*(1 - findgen(63)/63)) & b(1:63) = 255
#;positions 64 to 127 from blue to (almost) black
#r(64:127)=0 &  g(64:127) = 0 & b(64:127) = byte(255*(1 - findgen(64)/64))
#;positions 128 to 191 from black to (almost) red
#r(128:191) = byte(255*(findgen(64)/64)) & g(128:191) = 0 & b(128:191) = 0
#;position 192 to 255 from red to  yellow
#r(192:254) = 255 & g(192:254) = byte(255*(findgen(63)/62))  & b(192:254) = 0
#;position 255 is white
#r(255) = 255    & g(255) = 255    & b(255) = 255
#
#modifyct, 37, 'cb_black_ry', r, g, b
#
#
#
#
#;make black-red-yellow-white table
#;positions 0 to 84 from black to almost red
#r(0:84) = byte(255*(findgen(85)/85)) & g(0:84) = 0 & b(0:84) = 0
#;;position 85 to 170 from red to (almost) yellow
#r(85:170) = 255 & g(85:170) = byte(255*(findgen(86)/86))  & b(85:170) = 0
#;;position 170 to 255 from yellow to white (divide by one less to get maximum in the array)
#r(170:255) = 255 & g(170:255) = 255 & b(170:255) = byte(255*(findgen(86)/85))
#modifyct, 38, 'b_r_y_w', r, g, b
#
#
#;make a greyscale, but with b/w inverted for toner-friendly printing
#g	=	createLinearArray(0,255,255)
#r   = g
#b   = g
#modifyct, 40, 'colorfriendly bw', r, g, b
#;changed to 40 instead of 39, Jan 2010, with Daniel.
#
#
#end ;procedure DefineExplicitCT
    if SO_MV_colortable == 11:
        logging.getLogger("VIEW").info('IDL.createpalette: returning palette 11')
        IDLcm11 = ListedColormap(rgba_11, name='HSVconst')
        return IDLcm11
    elif SO_MV_colortable == 12:
        logging.getLogger("VIEW").info('IDL.createpalette: returning palette 12')
        IDLcm12 = ListedColormap(rgba_12, name='HSVconstWB')
        return IDLcm12
    elif SO_MV_colortable == 13:
        logging.getLogger("VIEW").info('IDL.createpalette: returning palette 13')
        IDLcm13 = ListedColormap(rgba_13, name='HSVconstBW')
        return IDLcm13
    elif SO_MV_colortable == 14:
        logging.getLogger("VIEW").info('IDL.createpalette: returning palette 14')
        IDLcm14 = ListedColormap(rgba_14, name='GrayCenter')
        return IDLcm14
    else:
        raise NotImplementedError(
            f'IDL.createpalette: a palette for SO_MV_colortable={SO_MV_colortable} has not been defined yet in python package')


##debugging section
if __name__ == "__main__":
    print('')
    
    #enter 
#    outfile = 'dummytiff.tiff'
#    write_tiff(outfile, myImage, red, green, blue, 100, 100)
#    (i,p) = read_tiff(outfile)


    