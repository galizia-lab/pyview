# Welcome to the repository containing the python implementation of PyView
PyView is a general purpose tool to analyze calcium imaging data of responses to sensory stimuli. 

It provides **a powerful GUI** to interactively visualize, analyse and assess the quality of imaging stacks; and flexibly select steps and parameters for removing artifacts and for estimating neural activity levels. The GUI is based on the core functions and classes of PyView that can be used for **identical batch processing**, i.e. running all experimental measurements through the processing steps selected above using one single set of parameters to produce time traces, 2D images or 3D movies 

# Getting started
## Installation
### Quick guide
(assuming you have anaconda installed)
- create a conda environment using [conda_py310_linux.yml](https://github.com/galizia-lab/pyview/blob/master/conda_py310_linux.yml) or [conda_py310_mac_win.yml](https://github.com/galizia-lab/pyview/blob/master/conda_py310_mac_win.yml)
- Take note tag of the latest release of PyView from [here](https://github.com/galizia-lab/pyview/releases).
- Install PyView using `pip install git+https://git@github.com/galizia-lab/pyview.git@<tag name>`

### Detailed guides
Please consult [this page](https://github.com/galizia-lab/pyview/wiki/Installation-and-updating) on our wiki for detailed guides on installation and updating as normal users and as developers.

## Starting PyView-GUI
1. Open a terminal/Powershell and activate the environment created for PyView). For example `conda activate view_py310`
2. Try launching PyView with the command "view". 

## Tutorial
A quick hands-on tour of the GUI and batch processing capabilities of PyView is provided by [View_Tutoral.pdf](https://github.com/galizia-lab/pyview/blob/master/synthetic_data/VIEW_Tutorial.pdf), using a synthetic dataset. Before you begin, make sure to
copy the folder "synthetic_data" into a place of your system where you keep data. (If you installed as a developer, the folder is part of the your local clone of the source code of PyView. If you installed as a simple user, get a ZIP or TARBALL of the source code of the lastest release of PyView [here](https://github.com/galizia-lab/pyview/releases)).


## More Resources and documentation
- [Our Wiki](https://github.com/galizia-lab/pyview/wiki)
- [Our JOSS Paper]()

# License
BSD 3 Clause, see file LICENSE-BSD-3-CLAUSE

# Issues
If you find bugs, have questions about its usage, or have ideas for new features, please check the Issues tab first for related Issues before creating a new issue. For bugs and errors, please paste the error you have encountered, mention your operating system and clearly state the steps to reproduce the error. Attach sample data if it is needed to reproduce the error. Thank You!

# Contributing
Please consult [this page on the wiki](https://github.com/galizia-lab/pyview/wiki/Developer-Guide) for a Developer Guide. Pull requests corresponding to well documented issues in this repository are welcome!


# Citing
Please consider citing our [JOSS paper]() if PyView was useful for your research, investigations or other intellectual work.