This folder contains custom files for Inga Petelski, in the Konstanz Insect research group, 2023.

You can use or adapt the files, no problems.

In particular, create_tapestry_inga.py may be interesting for many users. 
To explain this, a bit of background:

Normally, in generating tapestries, the user selects a "Measu" value. 
However, in this dataset, the task was to generate tapestries 
with the same order of displayed measurements for each experiment/animal,
even though the order of odorant delivery was randomized.
Therefore, instead of ordering tapestries by "Measu" value,
here, the tapestry is ordered by odour. (Any column may be used)
The catch here is: measurements need to be unique within one experiment. 
If the same odorant is given twice in the experiment, you'll need to use another column. 

Code in the .yml file within the 05_PROGS folder:

  # values from the column "Measu" of the measurement list for this animal
  measus: ['HEX3','HEX3','ZHAE2','ZHAE2','OC3L2']
  # if measu_order_column is set to 'Stimulus', measus needs to contain entries from that column
  # similarly, measu_order_column can be set to any column of the list file
  # however, the values for measus need to be unique: if there are two rows (measurements) with the same value
  # the program will stop
  measu_order_column: 'Odour'
