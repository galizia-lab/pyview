 
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

Optical imaging experiments, including calcium imaging experiments, can have long durations, in particular if performed in vivo. Typically, they consist of many measurements with different experimental settings (stimulus type and intensity, pharmacological treatments, animal age or genotype, to name but a few). The resulting data needs pre-processing of various kinds, depending on the system that is being investigated (e.g. olfactory or visual system, or animal species), the activity reporter used (e.g. GCamP, FURA), and the optical properties of the setup (e.g. 2-photon imaging, widefield imaging; single wavelength or ratiometric imaging). Bleaching and baseline correction, movement correction, scattered light correction are necessary, selection of appropriate regions of interest, and exclusion or areas that are not neurons are among the most important steps here. Adjusting parameters for data treatment can be tedious, and necessitates interactive visualization and iterative experimentation by the researcher. 

Conversely, statistical analysis across experimental animals, and across experimental parameters (e.g. different stimuli for sensory systems, or different animal groups), necessitate that all datasets are treated in an identical way. Therefore, data generation for statistical analysis should be done not using an interactive mode, but rather using batch processing, with identical parameter settings across all datasets and nonetheless using the same code as during GUI experimentation.
	
# Scope and Alternatives
Several packages for analysis of calcium imaging data have been developed in recent years [@Pnevmatikakis_2019]. These include CaImAn [@Giovannucci_2019], Suite2p (<www.suite2p.org/>), CALIMA [@Radstake_2019], SIMA (<https://github.com/losonczylab/sima>), MOCO [@Dubbs_2016], Toolbox-Romano [@Romano_2017], OpenFluo [@Dupuy_2009], ILTIS (<https://github.com/grg2rsr/ILTIS>), ImageBee [@Strauch_2013] and plug-ins to Fiji [@Schindelin_2012]. Each is specialized in its own way: movement correction, selection of regions of interests or interactive visualization. However, most labs still program their batch-processing with flexibly selected parameters ad-hoc for each experiment, necessitating high-level programming expertise in a biological lab. Here we propose a modular approach, that is also able to include existing packages into the pipeline (e.g. ILTIS, which is already included), and available to use also for labs without expertise in computer programming.

# Architecture: Software
PyView relies heavily on several existing tools and packages in Python, incorporating their strengths into a general and extendable framework. All of them have been listed in the file “setup.py” at the root of PyView repository at GitHub (<https://github.com/galizia-lab/pyview>)

PyView has been structured for good readability, modularity, testability and extensibility. It consists primarily of three parts:

## PyView-Core
This contains all the classes, functions and definitions that form the core of PyView.

## PyView-GUI
This is a GUI written in PyQt5 with which users can use the functionalities implemented in PyView-core: configure parameters, save configuration files, load data, create representative images and movies, and export processed data into CSV files for further analysis. 

## ILTIS
ILTIS (<https://github.com/grg2rsr/ILTIS>) is a stand-alone package used for interactive calcium imaging data visualization, a fork(<https://github.com/galizia-lab/ILTIS>) of which has been integrated into PyView-GUI. This allows interactive visualization of imaging data and inspecting individual image frames or pixelwise time traces. ILTIS can also be used to manually segment images and save the results into files.

# Architecture: Data processing
The basic idea is to analyze data in two steps: 
1. load and interactively play with the data in PyVIEW-GUI to find analysis parameters suitable for a set of experimental conditions 
2. non-interactive batch processing using scripts based on PyVIEW-Core to generate images, movies, spreadsheets of time traces, etc. 

Details on the architecture are explained in the WIKI as a tutorial: <https://github.com/galizia-lab/pyview/wiki/Tutorial>


# Future development
The package will be further developed on a continuous basis. Input from the community is welcome, in particular to implement reading new data formats, and to export data to other packages.

The next version of PyView will leverage CaImAn [@Giovannucci_2019] for correcting movement artifacts, for automatically estimating spatial footprints and temporal activity of neural sources. PyView will also incorporate rNMF [@Soelter_2014; @Strauch_2013] for source segmentation and SimpleElastix [@Marstal_2016] for correcting anisotropic movement artifacts. Since PyView can integrate multiple pipelines into itself, it will also be useful to compare their outcomes. A similar approach has been taken in electrophysiology by spikeinterface (<https://open-ephys.org/spikeinterface>), which allows different spike sorting algorithms to be compared on a single dataset [@Buccino_2020]. Guides for running unit tests on existing modules as well as contributing new modules are provided in section “Developer Guide” of the PyView Wiki (<https://github.com/galizia-lab/PyView/wiki/Developer-Guide>).

# Strengths
Among the strengths of this package, we note the following: PyView is free and completely open source, and built with Python and various Python libraries that are equally free and available. The package is modular and easily extendable – our hope is that it will grow thanks to the input of many labs across the world. It is built to incorporate existing and future tools.

Furthermore, PyView can be used with only little computer knowledge, and programming knowledge is not necessary. Thus, it is suitable for experimenters with all levels of programming experience, and can be used by biology or medical science undergraduates. Similarly, it can be used as a data analysis tool in teaching classes that focus on the biological result, and be fruitfully used to teach the difference between “few animals interactive data analysis” and “many animals statistical analysis with standardized settings”.

Thanks to the necessity to structure the data in appropriate folders, and to list all choices in dedicated parameter files (.yml files), data analysis choices remain transparent and explicit to the user. 

# Limitations and caveats
In the current version, all data that is analyzed in PyView GUI is loaded into memory, creating problems for very large data sets. In most cases, this does not create problems in batch analysis mode, where single measurements are analyzed sequentially. 

The power of the program lies in its flexibility, and that the user has extensive choices to control how data is treated, which output is generated, and how it is formatted – this comes at a price: there are many parameters to be set. Even though we tried to name these parameters in an intuitive way, we note that beginners are often overwhelmed. 

# Use cases and Input Data formats
@L_dke_2018 recorded odor responses in Drosophila brains and used ILTIS for selecting ROIs, and a previous version of PyView (VIEW, written in IDL® language) for data analysis. Odor responses in eight different olfactory receptor populations where characterized for a large panel of odorants and mixtures in Drosophila using the calcium reporter GCamP, and VIEW was used to quantify the data [@M_nch_2017]. In fact, VIEW had been developed over more than two decades [@Galizia_1999; @Sachse_1999], and put to fruit in analyzing olfactory coding in the insect brain [@Galizia_2014; @M_nch_2016; @Paoli_2021]. However, it was difficult to share among labs due to the proprietary nature of the language used (IDL®). These studies motivated us to create a new version of the analysis pipeline, with improved features, and written in a language that is freely available (Python): PyView as presented here.

Currently the following data formats can be loaded into PyView: Till Photonics files (TillVision), generic TIFF files/OME files (<https://www.openmicroscopy.org/ome-files>) with metadata (as created, for example, by Till Photonics LiveAcquisition software), Zeiss confocal/2-photon data, Leica confocal/2-photon data (.lif). Example datasets for all implemented formats have been published at <https://doi.gin.g-node.org/10.12751/g-node.4c44i5>. Readers for other formats are easy to implement.

# Conclusions
PyView provides a flexible package for optical imaging data analysis, affording rigorous data treatment using identical settings across collections of many measurements. 

# Acknowledgments
Thanks for providing sample data sets, testing the software, and giving useful advice go to all members of the Galizia lab, in particular to Alja Lüdke, Hanna Schnell, Marco Stucchi, Marco Paoli, Inga Petelski, Sercan Sayin, Paul Szyszka. Datasets were also provided by Bente Berg and Xi Chu from NTNU Trondheim, and by Martin Giurfa, Marco Paoli, and Maria Gabriela de Brito Sanchez from the Centre de Recherches sur la Cognition Animale, Toulouse. Funded by the Federal Ministry of Education and Research (BMBF) and the Baden-Württemberg Ministry of Science as part of the Excellence Strategy of the German Federal and State Governments

# References
