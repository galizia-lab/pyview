'''
Add a trace to the top left of the window, assuming no interesting data is there.
Created June 2025, galizia.
MS trace to be added


'''

import numpy as np
from scipy.interpolate import interp1d
import pathlib as pl
import pandas as pd


def add_MS_trace(data_in: np.ndarray, p1_metadata, flags, p1_extra_metadata):
    # raw_data is in format XYT
    # flags has info about where the MS data is
    # todo: apply also to FID data using fidor
    
    #ms data is:
    ms_data_file = pl.Path(flags['STG_MotherOfAllFolders']) / p1_extra_metadata['filepath'] #this starts at 01_DATA
    if ms_data_file.exists():
        ms_data_df = pd.read_csv(ms_data_file, header=2)
        # data is in the second column, time in first
        ms_data = ms_data_df.iloc[:,1].values
        ms_time = ms_data_df.iloc[:,0].values
        # time is in minutes, and decimal values (I hope), convert to ms
        ms_time = ms_time * (60*1000)

        # Input parameters
        #t_ms = p1_extra_metadata['FIDfreq']   # how many ms per imaging frame
        t_movie = p1_metadata.trial_ticks    # how many ms per movie frame
        x_size = 15        # Patch size to be inserted into movie

        # Time vectors
        num_movie_frames = data_in.shape[2] # time points in imaging data
        #ms_time = np.arange(len(ms_data)) * t_ms
        movie_time = np.arange(num_movie_frames) * t_movie

        # Step 1: Resample ms_data using interpolation
        #interp_func = interp1d(ms_time, ms_data, kind='linear', bounds_error=False, fill_value=np.nan)
        #ms_resampled = interp_func(movie_time)
        # simpler: piecewise linear interpolation
        ms_resampled = np.interp(movie_time, ms_time, ms_data, left=np.nan, right=np.nan)

        # Step 1b: Fill NaNs (where movie_time exceeds x_time) with mean of x
        mean_x = np.nanmean(ms_data)
        ms_resampled = np.where(np.isnan(ms_resampled), mean_x, ms_resampled)

        # Step 2: Scale x_resampled to 20%-80% quantiles of data_in
        q20, q80 = np.quantile(data_in, [0.2, 0.8])
        x_min, x_max = np.min(ms_resampled), np.max(ms_resampled)
        ms_scaled = (ms_resampled - x_min) / (x_max - x_min)  # Normalize to [0,1]
        ms_scaled = ms_scaled * (q80 - q20) + q20             # Scale to [q20, q80]

        # Step 3: Copy into upper-left corner of each frame
        for t in range(num_movie_frames):
            data_in[:x_size, :x_size, t] = ms_scaled[t]
    else:
        # file does not exist, do nothing
        pass

    # data_in now contains the injected signal

    return data_in



