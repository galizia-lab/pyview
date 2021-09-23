# Welcome to the repository containing the python implementation of VIEW
VIEW is a general purpose tool to analyze calcium imaging data of responses to sensory stimuli. 
Its philosophy is two-dimensional.

Dimension one - data handling: Data is treated in five steps. 

1. load data, 
2. calculate signals - e.g. ratio, movement or bleach correction etc.
3. apply corrections using another data set - e.g. subtract air measurement
4. create additional information - e.g. a map of localities for each glomerulus
5. report about the data in two ways:
    1. analyze data and generate output, interactively - e.g. time traces or false-color coded images.
    2. analyze data and generate output, offline - using a list that controls which datasets to analyze.

Importantly, 5.1 and 5.2 use exactly the same code. 
Each of these steps offers a variety of options controlled by "flags" (e.g. different data formats, movement corrections, definitions for glomerulus location, format of output data). The sequential nature means new modules can be implemented easily.
 
Dimension two - data analysis process: the user has interactive access to the data in order to evaluate it, and interactive access to all flag values, allowing the user to select the appropriate settings. Once the flags are chosen, the user generates a list of all measurements to be evaluated, and thus analyzes the entire dataset with identical settings, allowing for powerful (and correct) statistical analysis. 

VIEW is based on a previous version written in IDL, mostly by Giovanni (1996-2015) with the help of many people, and is now written in Python, mostly by Ajay (2019), again with the help of many people, and including modules from various sources.


For more information about installing and using VIEW, consult the [wiki](https://git.uni-konstanz.de/galizia/idl_python_translate/wikis/home)