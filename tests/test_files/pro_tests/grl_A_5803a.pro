
pro grl_A_5803a
common data
common CFD
common CFDconst
common Vars

;butanol
;scalemax =
;scalemin =

;overall
scalemax = 23.1
scalemin = -3.0


flag[rm_newcolumn]=1
subloop,'3';  Long00
flag[rm_newcolumn]=0
subloop,'5';  Long01

flag[rm_newcolumn]=1
subloop,'7';  Long02
flag[rm_newcolumn]=0
subloop,'9';  Long03
subloop,'10';  Long04
subloop,'11';  Long05
subloop,'12';  Long06
subloop,'13';  Long07
subloop,'14';  Long08
subloop,'15';  Long09


flag[rm_newcolumn]=1
subloop,'19';  Long10
flag[rm_newcolumn]=0
subloop,'21';  Long11
subloop,'22';  Long12
subloop,'23';  Long13
subloop,'24';  Long14
subloop,'25';  Long15
subloop,'26';  Long16
subloop,'27';  Long17


end


