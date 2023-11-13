import logging
from dataclasses import dataclass, field
import pandas as pd
from typing import Dict, Mapping, Sequence
from neo import AnalogSignal
import quantities as pq
import numpy as np


@dataclass
class GDMRow:
    """Class for a gdm row, which a pixel trace with associated metadata"""
    metadata: pd.Series
    time_series: AnalogSignal

    def copy(self):

        return GDMRow(metadata=self.metadata.copy(), time_series=self.time_series.copy())

    @classmethod
    def from_data_and_metadata(
            cls, metadata_dict: Mapping, trace: Sequence=None, sampling_period_ms: float=None,
            starting_time_s: float = 0, units: str = "au"
    ):
        metadata = pd.Series(metadata_dict)
        if trace is not None:
            time_series = AnalogSignal(
                signal=trace, sampling_period=sampling_period_ms * pq.ms, t_start=starting_time_s * pq.s,
                units=units
            )
        else:
            time_series = None

        return cls(metadata=metadata, time_series=time_series)

    def get_ASCII_exportable_format(self):

        signal_metadata = self.metadata.copy()
        signal_metadata["TraceOffset"] = self.time_series.t_start.magnitude
        signal_metadata["Cycle"] = (self.time_series.sampling_period / pq.ms).simplified.magnitude
        signal_metadata["NumFrames"] = self.time_series.shape[0]

        return signal_metadata, self.time_series.magnitude.T[0]

    @classmethod
    def parse_from_csv_df_row(cls, csv_df_row):

        try:
            sampling_period = csv_df_row["Cycle"]
            t_start = csv_df_row["TraceOffset"]
            n_samples = csv_df_row["NumFrames"]

            trace_start_pos = next(iter(i for i, x in enumerate(csv_df_row.index.values) if x == "PlaceHolder")) + 1
            trace = [float(x) for x in csv_df_row.iloc[trace_start_pos: trace_start_pos + n_samples].values]
        except (KeyError, StopIteration) as e:
            sampling_period = None
            t_start = 0
            trace_start_pos = len(csv_df_row)
            trace = None

        return cls.from_data_and_metadata(
            metadata_dict=csv_df_row.iloc[:trace_start_pos],
            sampling_period_ms=sampling_period,
            starting_time_s=t_start,
            trace=trace
        )


@dataclass
class GDMFile:
    """Class for a collection fo GDMRow objects, with CSV (and other) IO interfaces"""
    metadata_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    data_dict: Dict = field(default_factory=dict)

    def copy(self):

        return GDMFile(metadata_df=self.metadata_df.copy(), data_dict={k: v.copy() for k, v in self.data_dict.items()})

    def __getitem__(self, item):
        return GDMRow(time_series=self.data_dict[item], metadata=self.metadata_df.loc[item])

    def indices_iterator(self):
        return iter(self.data_dict.keys())

    def get_trace(self, index):

        return self.data_dict[index]

    def subset_based_on_indices(self, indices):
        """
        Return a new GDMFile object with only those metadata and time series whose index is in indices
        :param Sequence indices: sequence of indices
        :return: GDMFile
        """
        assert all(x in self.data_dict for x in indices), "Not all indices specified are in the current GDMFile"
        gdm_file = __class__()
        gdm_file.metadata_df = self.metadata_df.loc[indices, :]
        gdm_file.data_dict = {k: v for k, v in self.data_dict.items() if k in indices}

        return gdm_file

    def subset_based_on_callable(self, metadata_filter):
        """
        Return a new GDMFile object with only those metadata and time series whose index is in indices
        :param Callable metadata_filter: a callable that can be used to select rows of metadata df
        :return: GDMFile
        """

        gdm_file = __class__()

        gdm_file.metadata_df = self.metadata_df.loc[metadata_filter, :]
        gdm_file.data_dict = {k: v for k, v in self.data_dict.items() if k in gdm_file.metadata_df.index.values}

        return gdm_file

    def append_from_a_gdm_file(self, gdm_file):
        # switch off warning "A value is trying to be set on a copy of a slice from a DataFrame"
        pd.options.mode.chained_assignment = None  # default='warn'
        
        if self.metadata_df.shape[0] == 0:
            self.metadata_df = gdm_file.metadata_df
            self.data_dict = gdm_file.data_dict
        else:
            current_max_ind = self.metadata_df.index.values.max()
            for enum_ind, (ind, metadata_row) in enumerate(gdm_file.metadata_df.iterrows()):
                new_ind = current_max_ind + enum_ind + 1
                self.metadata_df.loc[new_ind] = metadata_row
                self.data_dict[new_ind] = gdm_file.data_dict[ind]

    def append_gdm_row(self, gdm_row):

        new_index = self.metadata_df.shape[0]
        if new_index == 0:
            self.metadata_df = pd.DataFrame(gdm_row.metadata).T
            self.metadata_df.index = [0]  # set index to 0 for the first row
        else:
            self.metadata_df.loc[new_index] = gdm_row.metadata
        self.data_dict[new_index] = gdm_row.time_series

    @classmethod
    def load_from_csv(cls, csv_file, metadata_only=False):
        """
        Load data and metadata from a csv file
        :param csv_file: absolute path of CSV file on file system
        :param bool metadata_only: whether to only read metadata, i.e., skip reading data
        :return: object of class GDMFile
        """
        gdm_file = cls()
        
        csv_df = read_chunks_gdm_csv(csv_file, metadata_only=metadata_only)

        for i, row in csv_df.iterrows():
            gdm_file.append_gdm_row(GDMRow.parse_from_csv_df_row(row))

        return gdm_file

    def write_to_csv(self, filename):

        metadata_df = pd.DataFrame()
        trace_df = pd.DataFrame()
        for gdm_ind in self.data_dict:

            gdm_row = self.__getitem__(gdm_ind)

            metadata_row, trace = gdm_row.get_ASCII_exportable_format()
            frame_values_s = pd.Series({f"Frame{k}": v for k, v in enumerate(trace)})
            # metadata_df = metadata_df.append(pd.DataFrame(metadata_row).T, ignore_index=True) # .append will be deprecated
            # trace_df = trace_df.append(pd.DataFrame(frame_values_s).T, ignore_index=True)
            metadata_df = pd.concat([metadata_df, pd.DataFrame(metadata_row).T], ignore_index=True)
            trace_df = pd.concat([trace_df,pd.DataFrame(frame_values_s).T], ignore_index=True)

        metadata_df["PlaceHolder"] = "Trace begins->"
        columns_before_trace = \
            ["StimONms", "StimLen", "Odour", "Stimulus", "OConc", "Cycle", "GloTag", "Measu", "Animal", "PlaceHolder"]
        metadata_df = metadata_df[
            [x for x in metadata_df.columns if x not in columns_before_trace] +
            [x for x in columns_before_trace if x in metadata_df.columns]
        ]
        df = pd.concat([metadata_df, trace_df], axis=1, sort=False)

        df.to_csv(filename, sep=';', header=True, index=False)
        logging.getLogger("VIEW").info(f"Finished writing {filename}")

    def get_data_as_numpy2D(self):
        """

        If all data have the same length, return them as a 2D numpy array containing one time series per row
        :rtype: numpy.ndarray
        """
        if len(self.metadata_df["NumFrames"].unique()) == 1:
            return np.array([x.magnitude for x in self.data_dict.values()])[:, :, 0]
        else:
            raise ValueError("GDMFile has data of different lengths. Cannot create a numpy array")


def read_chunks_gdm_csv(input_csv, metadata_only=False):
    """
    Read a csv containing gdm and FID chunks, parsing date and time columns properly
    :param str input_csv: path to the input csv
    :param bool metadata_only: whether to only read metadata, i.e., skip reading data
    :return: pandas.DataFrame
    """

    print(f"Reading {input_csv}")
    
    if metadata_only:
        gdm_df = pd.read_csv(input_csv, sep=";", nrows=1, header=0)
        columns2read = []
        for x in gdm_df.columns:
            if x == "PlaceHolder":
                break
            else:
                columns2read.append(x)

        gdm_df = pd.read_csv(input_csv, sep=";", usecols=columns2read)
    else:
        gdm_df = pd.read_csv(input_csv, sep=";")

    def revise_line(line):
        if "_" in line:
            return line.split("_")[0]
        else:
            return line
    if "line" in gdm_df.columns:
        gdm_df["line"] = gdm_df["line"].apply(revise_line)

    return gdm_df


def parse_stim_info(gdm_row_metadata, sort=True):

    stimulus_components = eval(gdm_row_metadata["Odour"])
    if type(gdm_row_metadata["StimONms"]) is str:
        stimulus_times = eval(gdm_row_metadata["StimONms"])
    else:
        stimulus_times = gdm_row_metadata["StimONms"]

    if type(gdm_row_metadata["StimLen"]) is str:
        stimulus_durations = eval(gdm_row_metadata["StimLen"])
    else:
        stimulus_durations = gdm_row_metadata["StimLen"]

    if type(stimulus_components) is str:
        stimulus_times = stimulus_times,
        stimulus_components = stimulus_components,
        stimulus_durations = stimulus_durations,

    if sort:
        arg_sort = np.argsort(stimulus_times)
        stimulus_times = [stimulus_times[x] for x in arg_sort]
        stimulus_components = [stimulus_components[x] for x in arg_sort]
        stimulus_durations = [stimulus_durations[x] for x in arg_sort]

    return stimulus_components, stimulus_times, stimulus_durations