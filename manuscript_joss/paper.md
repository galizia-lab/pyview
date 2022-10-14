 
---
title: 'PyView: A general purpose tool for analyzing calcium imaging data'
tags:
  - Python
  - Neuroscience
  - Calcium imaging
authors:
  - name: Ajayrama Kumaraswamy 
    orcid: 0000-0001-7928-877X
    affiliation: 1
  - name: Georg Raiser
    orcid: 0000-0002-9716-3513
    affiliation: 2
  - name: C Giovanni Galizia
    orcid: 0000-0001-8292-6031
    corresponding: true
    affiliation: 1
affiliations:
  - name: University of Konstanz, Department of Biology, Universitatsstr. 10, D-78457 Konstanz 
    index: 1
  - name: Champalimaud Centre for the Unknown, Avenida de Brasília, 1400-038 Lisboa, Portugal 
    index: 2

date: 25 September 2022
bibliography: paper.bib
---

# Summary

Optical imaging allows to record network activity in many neurons simultaneously, yielding a direct access to network activity in the brain [@G_bel_2007]. The development of transgenic animals that express genetically encoded calcium reporters, such as GCamP, has further increased the possibilities to study neural networks, other reporters, suitable for measuring membrane potential or specific second messengers are being developed in several labs [@Sepehri_Rad_2017]. All of these techniques use changes in fluorescent light to quantitatively capture changes in neuron physiology, and all necessitate high-level image analysis tools in order to analyze the physiological data in a quantitative and consistent way [@Giovanni_Galizia_2004]. 
Here, we propose a software for optical imaging analysis: PyView (<https://github.com/galizia-lab/pyview>). PyView splits data treatment into two steps: a powerful GUI for interactive data analysis, with flexible selection of evaluation parameters, and a second step for batch processing, yielding time traces, 2D images or 3D movies across all experimental measurements with identical parameter settings. The program is modular, and easy to expand with tools for dedicated analyses and/or experimental questions. The program is open source, written in python, and can be expanded to act as a wrapper for other programs that address single steps in a data analysis pipeline. 
Information about example workflows, galleries of examples outputs, and guides for installing, using and developing PyView are organized in a wiki (<https://github.com/galizia-lab/PyView/wiki>)

# Statement of need

Optical imaging experiments, including calcium imaging experiments, can have long durations, in particular if performed in vivo. Typically, they consist of many measurements with different experimental settings (stimulus type and intensity, pharmacological treatments, animal age or genotype, to name but a few). The resulting data needs pre-processing of various kinds, depending on the system that is being investigated (e.g. olfactory or visual system, or animal species), the activity reporter used (e.g. GCamP, FURA), and the optical properties of the setup (e.g. 2-photon imaging, widefield imaging; single wavelength or ratiometric imaging). Bleaching and baseline correction, movement correction, scattered light correction are necessary, selection of appropriate regions of interest, and exclusion or areas that are not neurons are among the most important steps here. Adjusting parameters for data treatment can be tedious, and necessitates interactive visualization by the researcher. 
Conversely, statistical analysis across experimental animals, and across experimental parameters (e.g. different stimuli for sensory systems, or different animal groups), necessitate that all datasets are treated in an identical way. Therefore, data generation for statistical analysis should be done not using an interactive mode, but rather using batch processing, with equal parameter settings across all datasets. 
PyView has been developed with the following primary aims in mind:

 - Enable experimenters to easily, quickly and interactively assess the quality of calcium imaging data by visualizing raw data along with prospective estimates of neural activity inferred from the raw data. 
 - Interactively find the most suitable processing steps and parameters for removing artifacts in raw data and estimating activity levels. Save the steps and parameters to files in a standardized format (.yml files). 
 - Apply the same processing steps with the same parameters to all data acquired in a line of investigation in a non-interactive way using scripts. 
 - Create publication-ready visualizations: images and movies of individual recordings with many kinds of annotations, and HTMLs containing multiple images organized in a grid. 
 - Export the processed data to CSV or MAT files in a standardized format for further investigation with external tools. 
 - Avoid multi-tool, multi-step processing, by allowing to act as wrapper for other software packages. 
 - Interactively create regions-of-interest (ROIs) of diverse shapes and save them to files, which could be used later for identifying neural substrates, for specifying brain regions where processing should focus, and to export corresponding time traces. 
 - Organize raw data, metadata, files containing ROIs, ad-hoc images and all other files related to a line of investigation in a standardized folder structure, with clear separation of original data and processed/interpreted data.
	
# Scope and Alternatives
Several packages for analysis of calcium imaging data have been developed in recent years [@Pnevmatikakis_2019]. These include CaImAn [@Giovannucci_2019], Suite2p (<www.suite2p.org/>), CALIMA [@Radstake_2019], SIMA (<https://github.com/losonczylab/sima>), MOCO [@Dubbs_2016], Toolbox-Romano [@Romano_2017], OpenFluo [@Dupuy_2009], ILTIS (<https://github.com/grg2rsr/ILTIS>), ImageBee [@Strauch_2013] and plug-ins to Fiji [@Schindelin_2012]. Each is specialized in its own way: movement correction, selection of regions of interests or interactive visualization. However, most labs still program their batch-processing with flexibly selected parameters ad-hoc for each experiment, necessitating high-level programming expertise in a biological lab. Here we propose a modular approach, that is also able to include existing packages into the pipeline (e.g. ILTIS, which is already included), and available to use also for labs without expertise in computer programming.

# Architecture: Software
PyView relies heavily on several existing tools and packages in Python, incorporating their strengths into a general and extendable framework. All of them have been listed in the file “setup.py” at the root of PyView repository at GitHub (<https://github.com/galizia-lab/pyview>)

PyView has been structured for good readability, modularity, testability and extensibility. It consists primarily of three parts:

## PyView-core
This contains all the classes, functions and definitions that form the core of PyView.

## PyView-GUI
This is a GUI written in PyQt5 with which users can use the functionalities implemented in PyView-core: configure parameters, save configuration files, load data, create representative images and movies, and export processed data into CSV files for further analysis. 

## Iltis
PyView leverages ILTIS (<https://github.com/grg2rsr/ILTIS>) for interactively visualizing data loaded with PyView-GUI, for manual segmentation and for saving resulting segmentations to files.

# Architecture: data processing
Data processing with PyView is modular, and users can adapt and change each module to adjust for their needs. We will also continue developing the package. 

Specifically, users control data processing steps of PyView through a set of configuration files: all experimental information is collected in a spreadsheet file (e.g. data file name, stimulus type and timing, time information, treatment information), all parameters are collected in .yml files (e.g. baseline correction information, filter settings), area information is stored in two files (one for “in brain” area, one for regions-of-interest), and batch analysis is controlled by a python command file with its dedicated .yml file. 
The analysis steps are:

## 1. Load Data:

Create spreadsheets of experimental metadata indicating stimulus timing, stimulus quality, stimulus duration, pharmacological treatment, animal age, etc. PyView contains modules for extracting machine-readable metadata stored alongside calcium imaging data. These can be leveraged by adopting example scripts provided with PyView (<https://github.com/galizia-lab/pyview/tree/master/log2list_examples>) to create spreadsheets of metadata. Based on their experiments, researchers can decide the exact set of metadata to be extracted, which can be refined manually as needed.
Raw data and metadata formats vary across imaging setups. Therefore, PyView can load data from different sources. Currently implemented formats are Till Photonics files (TillVision), .tif files with metadata (as created, for example, by Till Photonics LiveAcquisition software), Zeiss confocal/2-photon data, Leica confocal/2-photon data (.lif). Example datasets for all implemented formats are available at <https://doi.gin.g-node.org/10.12751/g-node.4c44i5>. Readers for other formats are easy to implement.

## 2. Filter/adjust loaded data

Perform bleach correction, baseline correction and/or apply spatial and/or temporal median or gaussian filters, or apply digital filters to the data. The key point here is: all filters are controlled by parameters that are stored in a dedicated .yml file, and thus in the later batch mode all measurements/animals will be treated with the identical filter, in order to ensure statistical consistency. 

## 3. Perform higher level data processing

Calculate ΔF/F for single wavelength dyes or ratios for ratiometric dyes, with dedicated settings (e.g. which frames to use as reference for ΔF/F calculation). Perform additional calculations such as subtracting different datasets (e.g. stimulus – background).

## 4. Interactive data analysis

Visualize and investigate of time traces using ILTIS. ILTIS (<https://github.com/grg2rsr/ILTIS>) is a stand-alone package used for interactive calcium imaging data visualization, a fork (<https://github.com/galizia-lab/ILTIS>) of which has been integrated into the PyView GUI interface. Several measurements can be loaded simultaneously. The user can transfer one or many datasets from PyView into ILTIS within the same GUI, and use ILTIS to visualize time traces and activity movies. Within ILTIS, the user can generate ROIs and save them into .roi files. The user can generate an .area file to include only brain area into the data analysis. Within the PyView GUI, the user can inspect different options for estimating response magnitude (max response, delta response, single time-point response, relative response), for generating false-color coded images (select color tables, adjust minima/maxima adaptively or use fixed thresholds), for generating movies (show stimulus timing, show elapsed seconds, select window border width). All parameters chosen can be written to a .yml file with a single click, to be used in batch file analysis later. 

## 5. Generate master files for batch analysis

Importantly, PyView in GUI mode, and PyView in batch mode share the same code. This affords the user with a powerful tool to select the best parameters in an interactive session, and then run all data in a consistent manner with identical data treatment across datasets. 
The user generates a python master file which uses the same .yml file as PyView in GUI mode, and an additional .yml file with specific settings (e.g. to generate two batches of false-color coded images, one with individual scaling, one with global scaling). 
Three outputs are available:
 
 - overviews: relevant parameters are the calculation of activity parameter (“CTV”, for curve-to-value, where activity in a time course is evaluated by, e.g., area-under-the-curve, maximum offset, or value at a given time point), settings for false color limits, false color table. The output is a html-file with a tapestry of single false-color coded image for each measurement. These images are also saved as single image files, ready to be included in a publication.
 - time-traces with response-magnitude values and metadata. These are spreadsheets that contain, for each ROI and each measurement, the calculated time trace and all relevant metadata (stimulus, pharmacological treatment, animal tag, time information etc.) as well as response magnitude (calculated as selected). 
 - movies, yielding a single movie (in the format chosen by the user) for each measurement, with the color and filter settings as selected in the PyView-GUI.


## 6. Do statistics

The spreadsheet with time traces for each ROI can then be analyzed with standard statistics packages (e.g. compare response magnitude between two different pharmacological treatments, by running a test on column “response” with parameter “pharmacological treatment” and subjects “animal”). Users can use any standard statistics package of their choice to perform solid statistics (R, S, Python, SPSS…), or apply machine learning algorithms and classifiers to the extracted numerical data. This allows for qualitative and quantitative evaluation of intra-animal and inter-animal hypotheses.

# Future development
The package will be further developed on a continuous basis. Input from the community is welcome, in particular to implement reading new data formats, and to export data to other packages.
The next version of PyView will leverage CaImAn [@Giovannucci_2019] for correcting movement artifacts, for automatically estimating spatial footprints and temporal activity of neural sources. PyView will also incorporate rNMF [@Soelter_2014; @Strauch_2013] for source segmentation and SimpleElastix [@Marstal_2016] for correcting anisotropic movement artifacts. Because PyView can integrate multiple pipelines, it will also be useful to compare their outcomes. A similar approach has been taken in electrophysiology by spikeinterface (<https://open-ephys.org/spikeinterface>), which allows different spike sorting algorithms to be compared on a single dataset [@Buccino_2020]. Guides for running unit tests on existing modules as well as contributing new modules are provided in section “Developer Guide” of the PyView Wiki (<https://github.com/galizia-lab/PyView/wiki/Developer-Guide>).

# Strengths
Among the strengths of this package, we note the following: PyView is free and completely open source, and built with Python and various Python libraries that are equally free and available. The package is modular and easily extendable – our hope is that it will grow thanks to the input of many labs across the world. It is built to incorporate existing and future tools.
Furthermore, PyView can be used with only little computer knowledge, and programming knowledge is not necessary. Thus, it is suitable for experimenters with all levels of programming experience, and can be used by biology or medical science undergraduates. Similarly, it can be used as a data analysis tool in teaching classes that focus on the biological result, and be fruitfully used to teach the difference between “few animals interactive data analysis” and “many animals statistical analysis with standardized settings”.
Thanks to the necessity to structure the data in appropriate folders, and to list all choices in dedicated parameter files (.yml files), data analysis choices remain transparent and explicit to the user. 

# Limitations and caveats
In the current version, all data that is analyzed in PyView GUI is loaded into memory, creating problems for very large data sets. In most cases, this does not create problems in batch analysis mode, where single measurements are analyzed sequentially. 
The power of the program lies in its flexibility, and that the user has extensive choices to control how data is treated, which output is generated, and how it is formatted – this comes at a price: there are many parameters to be set. Even though we tried to name these parameters in an intuitive way, we note that beginners are often overwhelmed. 

# Use cases
@L_dke_2018 recorded odor responses in Drosophila brains and used ILTIS for selecting ROIs, and a previous version of PyView (VIEW, written in IDL® language) for data analysis. Odor responses in eight different olfactory receptor populations where characterized for a large panel of odorants and mixtures in Drosophila using the calcium reporter GCamP, and VIEW was used to quantify the data [@M_nch_2017]. In fact, VIEW had been developed over more than two decades [@Galizia_1999; @Sachse_1999], and put to fruit in analyzing olfactory coding in the insect brain [@Galizia_2014; @M_nch_2016; @Paoli_2021]. However, it was difficult to share among labs due to the proprietary nature of the language used (IDL®). These studies motivated us to create a new version of the analysis pipeline, with improved features, and written in a language that is freely available (Python): PyView as presented here.

# Conclusions
PyView provides a flexible package for optical imaging data analysis, affording rigorous data treatment using identical settings across collections of many measurements. PyView includes plenty of parameters to load data in a uniform way (filter settings, signal calculation, baseline and bleaching corrections) and to generate uniform output, such as movies, false-color coded images, time traces and response magnitude quantification. The user has full control of layout parameters (border color and size, labels, stimulus representation in the movie, etc.). 

# Acknowledgments
Thanks for providing sample data sets, testing the software, and giving useful advice go to all members of the Galizia lab, in particular to Alja Lüdke, Hanna Schnell, Marco Stucchi, Marco Paoli, Inga Petelski, Sercan Sayin, Paul Szyszka. Datasets were also provided by Bente Berg and Xi Chu from NTNU Trondheim, and by Martin Giurfa, Marco Paoli, and Maria Gabriela de Brito Sanchez from the Centre de Recherches sur la Cognition Animale, Toulouse. Funded by the Federal Ministry of Education and Research (BMBF) and the Baden-Württemberg Ministry of Science as part of the Excellence Strategy of the German Federal and State Governments

# References
