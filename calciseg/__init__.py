'''
CalciSeg: Calcium Imaging Segmentation Tool
Based on Jannick Günzel's CalciSeg 
written in MATLAB.
This is a Python adaptation integrated into the pyView framework.
This module provides the main class for CalciSeg operations.
Written by: Giovanni Galizia, with AI help.
November 2025

calciseg/
│
├── __init__.py
├── core.py
├── voronoi.py
├── utils.py
└── io.py     (optional later)

├── corr.py       # correlation-based segmentation
├── ica.py        # rICA segmentation
├── refine.py     # region merging, cleaning
├── stats.py      # region statistics





'''

from .voronoi import segment_voronoi
