#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 15:59:15 2018

@author: galizia
collection of functions in ImageAL_Local_Gio


"""
import pandas as pd


def localodortext(flags_input, p1):
    
# this function creates text chuncs that are used in VIEW
# for example in file names, or in labels for images or windows
    
# this function should be user accessible - every person needs to be able to 
# modify output names at will. 
# could be implemented with a string in an external file
    #flags_input should be a series - if it is not, convert it
    if  isinstance(flags_input, pd.Series):
        flag = flags_input
    else:
        flag = flags_input.to_series()
    
    maxTextLength = 10

#    ;odorText enthält Text, der unterhalb des Bildes ist
#    ;odorText = p1.ex_name + '_' + p1.treatment + '_' + strtrim(string(fix(p1.treat_conc *10)),2) ; neue Listen
#    ;odorText = p1.odor(odor) + '_' +strTrim(string(p1.odor_nr(1)),2)
#    ;odorText  = p1.ex_name + '_' + strmid(p1.treatment,0,1);vom treatment nur der erste buchstabe
#    ;odorText = p1.odor(odor) + '_' +strTrim(string(p1.stimulus_isi),2)
# 	;odorText = p1.odor(odor)
#	;odorText = p1.ex_name
#;gut f¸r 12
    odorText = p1.metadata.experiment[0:8] + '_' + p1.metadata.ex_name[0:8]
#;gut f¸r 10 - Beateq
#	odorText = strmid(p1.ex_name,0,min([6,strlen(p1.ex_name)])) + '_'+strtrim(string(fix(p1.posz)),2)+'_'+strtrim(string(p1.stimulus_on),2);max text length 12 chars
#	odorText = strmid(odortext,0,min([15,strlen(odortext)])) ;max text length 12 chars
#
#		;text f¸r Ringertest
#    txt_VisionTag = strmid(p1.ex_name,strlen(p1.ex_name)-2,strlen(p1.ex_name)) ;letzte beide Buchstaben vom Vision File_Namen
    #txt_VisionTag = p1.ex_name[-2:] # ;letzte beide Buchstaben vom Vision File_Namen
    txt_odor      = p1.odor #(odor) ;Duft
    txt_odor0     = txt_odor.strip()
#		;txt_treatment: treatment, e.g. Ring
    txt_treatment   = p1.treatment[0:4] # welcher Ringer
#		;txt_treatment0: treatment, e.g. Ring, remove blanks
    txt_treatment0  = txt_treatment.strip() # strmid(strtrim(p1.treatment,2),0,min([4,strlen(p1.treatment)]))
    #txt_odorInfo    = p1.odor_info.strip() #focal depth
    txt_odorConc    = str(p1.odor_nr) # ;odor concentration
    #txt_exName      = p1.ex_name.strip()

    if flag.VIEW_batchmode:# THEN begin
        if flag.VIEW_ReportMethod == 10: # then begin ;tiff-ausgabe ohne tiername
#		;einstellung f¸r Ringer-test-Versuch
#		;odorText = txt_treatment+'_' + txt_odor+'_' + txt_VisionTag ;die 3 st¸cke zusammen, mit spacern
#		;einstellung kurze Filme in verschiedenen Fokusebenen
#		;odorText = txt_odorInfo+'_' + txt_odor+'_' + txt_odorConc ;Fokusebene Duft Konzentration
            odorText = txt_odor0+'_'+txt_treatment0
            odorText = txt_odor0+'_'+txt_odorConc
            odorText = odorText[0:maxTextLength]# max text length maxTextLength chars

        if flag.VIEW_ReportMethod in [12, 1200]: # movie file name
            # odortext = p1.experiment[0:8] + '_'+ txt_odor0 +'_'+ txt_odorConc+'_'+ p1.viewlabel
            #odorText = flag.STG_ReportTag + '_' + p1.viewlabel
            #from p1.experiment e.g. 'dbb4f.pst' take only 'dbb4f'
            odorText = str(p1.messungszahl)+ '_' + p1.odor[0:4] +  '_' +p1.experiment.split('.')[0]
            odorText = str(p1.messungszahl)+ '_' + flag["STG_OdorReportFile"]
            
#	endIF
        if flag.VIEW_ReportMethod == 15: ## then begin ;filmausgabe mit tiername
            odorText = txt_odor + '_'+ flag.stg_reporttag +'_'+ str(p1.messungszahl) + '_' + p1.viewlabel
#	endIF
    else:
#	;working in view-gui
        odorText = p1.ex_name[0:6] + '_'+ str(p1.posz) + '_' + str(p1.stimulus_on) #max text length 12 chars
        odorText = odorText[0:maxTextLength]  #)) ;max text length maxTextLength chars

    return odorText
