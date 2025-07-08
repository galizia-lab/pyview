import logging
from dataclasses import dataclass, field

import pandas as pd
from typing import Dict, Mapping, Sequence
from neo import AnalogSignal
import quantities as pq
import numpy as np
from typing_extensions import Self
from os import PathLike


def parse_data_metadata_from_csv_row(csv_df_row: pd.Series) -> (Sequence[float], pd.Series):

    try:
        place_holder_column_index = get_place_holder_index(csv_df_row.index)
    except StopIteration as se:
        return None, csv_df_row.to_dict()

    try:
        trace_start_pos = place_holder_column_index + 1
        n_samples = csv_df_row.get("NumFrames", None)
        trace = [float(x) for x in csv_df_row.iloc[trace_start_pos: trace_start_pos + n_samples].values]
        return trace, csv_df_row.iloc[:trace_start_pos].to_dict()
    except Exception as e:
        logging.debug(f'Problem creating a trace', exc_info=e)


@dataclass
class GDMRow:
    """Class for a gdm row, which a pixel trace with associated metadata"""
    metadata: pd.Series
    time_series: AnalogSignal

    def copy(self) -> Self:

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
    def parse_from_csv_df_row(
            cls, csv_df_row: pd.Series,
            source_csv_file: str=None, source_csv_row_index: int=None):

        sampling_period = csv_df_row.get("Cycle", None)
        t_start = csv_df_row.get("TraceOffset", 0)


        trace, metadata = parse_data_metadata_from_csv_row(csv_df_row)

        metadata["source_csv_row_index"] = source_csv_row_index
        metadata["source_csv_file"] = source_csv_file

        return cls.from_data_and_metadata(
            metadata_dict=metadata,
            sampling_period_ms=sampling_period,
            starting_time_s=t_start,
            trace=trace
        )

    @classmethod
    def check_read_data_if_missing(cls, gdm_row: Self):
        """
        Checks if `gdm_row` has time_series data in it, if yes, return it. Else create a new GDMRow object by using
        metadata in `gdm_row` and time_series data pointed to by it.
        """

        if gdm_row.time_series is not None:
            # either time series for this row has already been initialized for this GDMRow
            # so do nothing and return
            return gdm_row
        else:
            # time series has not been initialized for this row

            csv_df_row = read_chunks_gdm_csv(
                input_csv=gdm_row.metadata["source_csv_file"],
                only_one_row_at_index=gdm_row.metadata["source_csv_row_index"]).iloc[0, :]

            gdm_row_with_data = cls.parse_from_csv_df_row(csv_df_row)
            gdm_row_with_data.metadata = gdm_row.metadata
            # replace metadata of `gdm_row` in case any metadata was added after loading from csvfile

            return gdm_row_with_data


@dataclass
class GDMFile:
    """Class for a collection fo GDMRow objects, with CSV (and other) IO interfaces"""
    metadata_df: pd.DataFrame = field(default_factory=pd.DataFrame)
    data_dict: Dict = field(default_factory=dict)

    def copy(self) -> Self:

        return GDMFile(metadata_df=self.metadata_df.copy(), data_dict={k: v.copy() for k, v in self.data_dict.items()})

    def __getitem__(self, item) -> GDMRow:
        return GDMRow(time_series=self.data_dict[item], metadata=self.metadata_df.loc[item])

    def __eq__(self, other):

        if not isinstance(other, type(self)):
            return False

        def clean_generate_as_str(df):

            df_copy = df.copy()
            del df_copy["source_csv_file"]
            del df_copy["source_csv_row_index"]
            # delete these two metadata column added internally to keep track of csv file and row index

            return df_copy.astype(str)

        cleaned_str_rep_self_metadata = clean_generate_as_str(self.metadata_df)
        cleaned_str_rep_other_metadata = clean_generate_as_str(other.metadata_df)
        # using string representations above using `astype` to avoid potential issues due to type mismatches

        if not cleaned_str_rep_self_metadata.equals(cleaned_str_rep_other_metadata):

            return False

        for ind in self.metadata_df.index.values:
            if not ind in other.data_dict:
                return False

            as_self = self.data_dict[ind]
            as_other = other.data_dict[ind]
            if as_self.t_start != as_other.t_start or as_self.sampling_rate != as_other.sampling_rate:
                return False

            if not np.isclose(as_self.magnitude, as_other.magnitude).all():
                return False

        return True


    def indices_iterator(self):
        return iter(self.data_dict.keys())

    def get_trace(self, index) -> AnalogSignal:

        return self.data_dict[index]

    def subset_based_on_indices(self, indices) -> Self:
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

    def subset_based_on_callable(self, metadata_filter) -> Self:
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
    def load_from_csv(cls, csv_file, metadata_only=False) -> Self:
        """
        Load data and metadata from a csv file
        :param csv_file: absolute path of CSV file on file system
        :param bool metadata_only: whether to only read metadata, i.e., skip reading data
        :return: object of class GDMFile
        """
        gdm_file = cls()
        
        csv_df = read_chunks_gdm_csv(csv_file, metadata_only=metadata_only)

        for i, row in csv_df.iterrows():
            gdm_row = GDMRow.parse_from_csv_df_row(row, source_csv_file=csv_file, source_csv_row_index= i + 1)
            gdm_file.append_gdm_row(gdm_row)

        return gdm_file

    def check_load_data_if_missing(self, indices_to_check: Sequence[int]= None):
        """
        Loads data for each row in the sequence `indices_to_check` if available and not loaded
        (probably because GDMFile was loaded in "metadata_only" mode).
        :param Sequence[ind] indices_to_check: data will be loaded rows corresponding to these indices; if None,
                                               data will be loaded for all rows
        """

        if indices_to_check is None:
            indices_to_check = self.data_dict.keys()

        for ind in indices_to_check:

            if self.data_dict[ind] is None:

                gdm_row_with_time_series = GDMRow.check_read_data_if_missing(self[ind])
                self.data_dict[ind] = gdm_row_with_time_series.time_series


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

        del metadata_df["source_csv_file"]
        del metadata_df["source_csv_row_index"]
        # delete these two metadata column added internally to keep track of csv file and row index


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

    def get_data_as_numpy2D(self) -> np.ndarray:
        """

        If all data have the same length, return them as a 2D numpy array containing one time series per row
        :rtype: numpy.ndarray
        """
        if len(self.metadata_df["NumFrames"].unique()) == 1:
            return np.array([x.magnitude for x in self.data_dict.values()])[:, :, 0]
        else:
            raise ValueError("GDMFile has data of different lengths. Cannot create a numpy array")

    def _get_data_as_numpy2D_align_starts(self) -> np.ndarray:
        """
        Aligns data of all rows at their first data points and fills nans to the end so as to create a return a 2D
        numpy.ndarray
        :rtype: numpy.ndarray
        :returns: numpy.ndarray of the same number of rows as self and number of columns equal to the length of row with
        the longest data
        """

        max_len = self.metadata_df["NumFrames"].max()
        padded_arrays = np.full((self.metadata_df.shape[0], max_len), np.nan)

        for ind, analog_signal in enumerate(self.data_dict.values()):
            padded_arrays[ind, :analog_signal.shape[0]] = analog_signal.magnitude.T

        return padded_arrays

    def collapse_GDM_data_only(self, collapse_using="nanmedian", temporal_alignment="align_starts") -> np.ndarray:
        """
        Temporally aligns the data of rows based on the parameter "temporal_alignment" and
        then applies a function based on the parameter "collapse_using" to reduce the data of all rows into one
        numpy ndarray
        :rtype: numpy.ndarray
        :returns: data of all rows collapsed into a single numpy array
        """
        if temporal_alignment == 'align_starts':
            gdm_data_aligned = self._get_data_as_numpy2D_align_starts()
        else:
            raise NotImplementedError(
                f"A value of {temporal_alignment} was specified for 'temporal_alignment', which is implemented.")

        if collapse_using == "nanmedian":
            return np.nanmedian(gdm_data_aligned, axis=0)
        else:
            raise NotImplementedError(
                f"A value of {collapse_using} was specified for 'collapse_using', which is implemented.")


    def collapse_GDM(self, groupby: list, collapse_using: str, temporal_alignment: str) -> Self:
        """
        Groups rows based on the metadata in the parameter `groupby`. For each group, checks if all rows have the
        same sampling rate, else raises and error. Else aligns the data in the rows based on the parameter
        `temporal_alignment` and collapses the data into a single time series based on the parameter `collapse_using`.
        The metadata of each group is collapsed by retaining indentical metadata in a group while replacing
        non-identical metadata with "unequal values".
        :param list groupby: list of column values for grouping where each group then gets collapsed/reduced
        :param str collapse_using: string, see documentation of `collapse_GDM_data_only`
        :param str temporal_alignment: string, see documentation of `collapse_GDM_data_only`
        :rtype: GDMFile
        :returns: a GDMFile object with one row per unique combination of metadata specified in `groupby`
        """

        def collapse_metadata_column(metadata_column: pd.Series):

            # if all values in the column are equal
            if metadata_column.eq(metadata_column.values[0]).all():
                return metadata_column.values[0]
            else:
                return "unequal_values"

        collapsed_gdm_file = GDMFile()

        for grouping_indices, group_metadata_df in self.metadata_df.groupby(groupby):
            collapsed_metadata = group_metadata_df.apply(collapse_metadata_column, axis=0)
            if "Animal" in collapsed_metadata:
                collapsed_metadata["Animal"] = f"{collapse_using}-{temporal_alignment}"
            if "TraceOffset" in collapsed_metadata:
                collapsed_metadata["TraceOffset"] = 0.0
            all_sampling_rates = [self.data_dict[x].sampling_rate for x in group_metadata_df.index.values]

            if not all(all_sampling_rates[0] == x for x in all_sampling_rates):
                raise ValueError(
                    f"When grouping based on {groupby}, for the group with values {grouping_indices}, found"
                    f"time traces with unequal sampling rates ({all_sampling_rates})")
            else:
                temp_gdm_file = GDMFile()
                temp_gdm_file.metadata_df["NumFrames"] = group_metadata_df["NumFrames"].copy()
                temp_gdm_file.data_dict = {k: self.data_dict[k] for k in group_metadata_df.index.values}
                collapsed_data = temp_gdm_file.collapse_GDM_data_only(
                    collapse_using=collapse_using, temporal_alignment=temporal_alignment)
                collapsed_metadata["NumFrames"] = collapsed_data.shape[0]
                collapsed_gdm_row = GDMRow.from_data_and_metadata(
                    metadata_dict=collapsed_metadata, trace=collapsed_data,
                    sampling_period_ms= (1 / all_sampling_rates[0]) / (1 * pq.ms)
                )
                collapsed_gdm_file.append_gdm_row(collapsed_gdm_row)

        return collapsed_gdm_file


def read_chunks_gdm_csv(
        input_csv: PathLike, metadata_only: bool=False, only_one_row_at_index: int=None
    ):
    """
    Read a csv containing gdm and FID chunks, parsing date and time columns properly
    :param str input_csv: path to the input csv
    :param bool metadata_only: whether to only read metadata, i.e., skip reading data
    :param int only_one_row_at_index: read only one row at the given index
    :return: pandas.DataFrame
    """

    print(f"Reading {input_csv}")

    # read column headers (first line of csv)
    headers_df = pd.read_csv(input_csv, sep=";", nrows=1, header=0)
    try:
        place_holder_column_index = get_place_holder_index(headers_df.columns)
    except StopIteration as ste:
        raise f'Could not read {input_csv} as no column with header "PlaceHolder" was found'

    basic_kwargs = dict(sep=";", header=0)

    if only_one_row_at_index:
        basic_kwargs["skiprows"] = range(1, only_one_row_at_index)
        basic_kwargs["nrows"] = 1

    if metadata_only:
        gdm_df = pd.read_csv(
            input_csv, **basic_kwargs, usecols=range(place_holder_column_index)
        )
    else:
        gdm_df = pd.read_csv(input_csv, **basic_kwargs)

    def revise_line(line):
        if "_" in line:
            return line.split("_")[0]
        else:
            return line
    if "line" in gdm_df.columns:
        gdm_df["line"] = gdm_df["line"].apply(revise_line)

    return gdm_df

def get_place_holder_index(headers):

    return next(i for i, x in enumerate(headers) if x == "PlaceHolder")



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