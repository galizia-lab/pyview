import pandas as pd
import numpy as np

from .gdm_data_classes import GDMFile, GDMRow
from view.python_core.overviews.ctv_handlers import PixelWiseCTVHandler
from view.python_core.p1_class import MetadataDefinition
from view.python_core.rois.roi_io import get_roi_io_class


def apply_mask_to_data(roi_data_dict, data_xyt, area=None):

    data_txy = np.moveaxis(data_xyt, [0, 1, 2], [1, 2, 0])
    roi_label_traces_dict = {}
    for label, roi_data in roi_data_dict.items():
        if area is not None:
            weighted_mask_xy = roi_data.get_weighted_mask_considering_area(area)
        else:
            weighted_mask_xy = roi_data.get_weighted_mask(data_xyt.shape[:2])

        # weighted_mask_xy will add up to 1
        # multiply each frame with the mask and sum over each frame
        roi_label_traces_dict[label] = (data_txy * weighted_mask_xy).sum(axis=(1, 2))

    return roi_label_traces_dict


def get_roi_gdm_traces_dict(p1, flags, roi_data_dict):

    if flags["GDM_withinArea"]:
        return apply_mask_to_data(data_xyt=p1.sig1, roi_data_dict=roi_data_dict, area=p1.area_mask)
    else:
        return apply_mask_to_data(data_xyt=p1.sig1, roi_data_dict=roi_data_dict)


def get_glodatamix_row_boiler_plate(p1, animal_name=None):

    meta_def = MetadataDefinition()
    list_column_p1_metadata_mapping = meta_def.get_list_column_p1_metadata_mapping()
    default_p1_metadata = meta_def.get_default_row()

    # add all non-default metadata from p1.metadata to GDM metadata
    temp = {
        k: p1.metadata[v] for k, v in list_column_p1_metadata_mapping.items()
        if pd.notnull(v) and (p1.metadata[v] != default_p1_metadata[k])
    }

    # add extra metadata in p1 to GDM metadata
    temp.update(p1.extra_metadata)

    metadata_boiler_plate = pd.Series(data=temp)

    # add animal name
    if animal_name is not None:
        metadata_boiler_plate["Animal"] = animal_name
    else:
        metadata_boiler_plate["Animal"] = "not set"

    # add stimulus timing information
    stim_starts_ms = [
        x / np.timedelta64(1, 'ms')
        for x in p1.pulsed_stimuli_handler.get_pulse_start_times()]
    metadata_boiler_plate["StimONms"] = str(stim_starts_ms)[1:-1]
    
    stim_durations_ms = [
        x / np.timedelta64(1, 'ms')
        for x in p1.pulsed_stimuli_handler.get_pulse_durations()]
    metadata_boiler_plate["StimLen"] = str(stim_durations_ms)[1:-1]

    return metadata_boiler_plate


def create_gdm_file_basic(
        common_metadata: pd.Series, roi_label_gdm_traces_dict: dict, sampling_period_ms: int, trace_onset: float=0,
        roi_descriptions: dict = None, roi_label_additional_metadata: dict = None
):
    gdm_file = GDMFile()

    for roi_label, gdm_trace in roi_label_gdm_traces_dict.items():

        metadata_boiler_plate = common_metadata.copy()

        metadata_boiler_plate['GloTag'] = roi_label

        if roi_descriptions is not None:
            metadata_boiler_plate['GloInfo'] = roi_descriptions[roi_label]

        if roi_label_additional_metadata is not None:
            # the alternative implementation using series.update not working for some reason
            for k, v in roi_label_additional_metadata.get(roi_label, {}).items():
                metadata_boiler_plate[k] = v

        gdm_row = \
            GDMRow.from_data_and_metadata(
                metadata_dict=metadata_boiler_plate, trace=gdm_trace,
                sampling_period_ms=sampling_period_ms, starting_time_s=trace_onset)

        gdm_file.append_gdm_row(gdm_row)

    return gdm_file


class FullTraceGDMGenerator(object):

    def __init__(self, p1, flags, additional_metadata=None):
        """
        :param p1:
        :param flags:
        :param int trace_onset: offset of the measurement in seconds
        :param dict additional_metadata: any additional metadata about this measurement to be added to GDMs
        """
        self.roi_data_dict, self.roi_file = get_roi_io_class(flags["RM_ROITrace"]).read(
            flags=flags, measurement_label=p1.metadata.ex_name)

        self.roi_descriptions = \
            {k: v.get_text_description(frame_size=p1.get_frame_size())
             for k, v in self.roi_data_dict.items()}

        self.roi_label_gdm_traces_dict = get_roi_gdm_traces_dict(p1=p1, flags=flags, roi_data_dict=self.roi_data_dict)

        self.metadata_boiler_plate = get_glodatamix_row_boiler_plate(
            p1=p1, animal_name=flags["STG_ReportTag"])

        if additional_metadata is not None:
            for k, v in additional_metadata.items():
                self.metadata_boiler_plate[k] = v

        self.sampling_period_ms = p1.metadata["trial_ticks"]

        self.ctv_handler_obj = PixelWiseCTVHandler(flags=flags, p1=p1)
        self.ctv_name = f"CTV_{flags['CTV_Method']}"

        self.pulsed_stimuli_handler = p1.pulsed_stimuli_handler

    def calc_ctv(self, trace):

        try:
            ctv_value = self.ctv_handler_obj.apply_pixel(trace)
        except (IndexError, AssertionError) as err:
            ctv_value = np.nan

        return ctv_value

    def get_gdm_file(self):

        roi_label_additional_metadata = {}
        for roi_label, trace in self.roi_label_gdm_traces_dict.items():

            roi_label_additional_metadata[roi_label] = {self.ctv_name: self.calc_ctv(trace)}

        return create_gdm_file_basic(
            common_metadata=self.metadata_boiler_plate,
            sampling_period_ms=self.sampling_period_ms,
            roi_label_gdm_traces_dict=self.roi_label_gdm_traces_dict,
            roi_descriptions=self.roi_descriptions,
            roi_label_additional_metadata=roi_label_additional_metadata
        )


class ChunksOnlyGDMGenerator(FullTraceGDMGenerator):

    def __init__(self, p1, flags, additional_metadata=None):

        super().__init__(p1, flags, additional_metadata)

        self.gdm_chunkPostStim = flags['GDM_chunkPostStim']
        self.gdm_chunkPreStim = flags["GDM_chunkPreStim"]

    def get_gdm_file(self, write_ctv=True):

        gdm_file_all = GDMFile()

        # for every stimulus
        for ind, (odor, conc, start_td, end_td, sampling_period_td) in \
                self.pulsed_stimuli_handler.stimulus_frame.iterrows():
            
            start_sec = start_td.total_seconds()
            end_sec = end_td.total_seconds()

            chunk_start_td = start_td - pd.to_timedelta(self.gdm_chunkPreStim, "s")
            chunk_end_td = end_td + pd.to_timedelta(self.gdm_chunkPostStim, "s")

            chunk_slice_start_ind = np.round(chunk_start_td / sampling_period_td).astype(int)
            chunk_slice_end_ind = np.round(chunk_end_td / sampling_period_td).astype(int)

            chunk_slice_start_ind = max(0, chunk_slice_start_ind)

            chunk_start_quantized_ms = chunk_slice_start_ind * self.sampling_period_ms

            common_metadata = self.metadata_boiler_plate.copy()
            common_metadata["StimLen"] = (end_sec - start_sec) * 1000  # in ms
            # this is relative to chunk start
            common_metadata["StimONms"] = start_sec * 1000 - chunk_start_quantized_ms  # in ms
            common_metadata["Odour"] = odor
            common_metadata["OConc"] = conc

            roi_label_chunk_dict = {}
            roi_label_additional_metadata = {}
            # for every ROI
            for roi_label, gdm_trace in self.roi_label_gdm_traces_dict.items():

                chunk_slice_end_ind = min(gdm_trace.shape[0], chunk_slice_end_ind)

                chunk = gdm_trace[chunk_slice_start_ind: chunk_slice_end_ind + 1]
                roi_label_chunk_dict[roi_label] = chunk

                roi_label_additional_metadata[roi_label] = {self.ctv_name: self.calc_ctv(chunk)}

            gdm_file_this_stim = create_gdm_file_basic(
                common_metadata=common_metadata,
                sampling_period_ms=self.sampling_period_ms,
                roi_label_gdm_traces_dict=roi_label_chunk_dict,
                roi_descriptions=self.roi_descriptions,
                roi_label_additional_metadata=roi_label_additional_metadata,
                # metadata field for arbitrary delay in measurement
                # here used to indicate chunk start time relative to trace start
                trace_onset=chunk_start_quantized_ms / 1000  # in seconds
            )

            gdm_file_all.append_from_a_gdm_file(gdm_file_this_stim)

        return gdm_file_all


def get_gdm_file(p1, flags):
    
    if flags["GDM_outputType"] == "full_traces":
        
        return FullTraceGDMGenerator(p1=p1, flags=flags).get_gdm_file()
    
    elif flags["GDM_outputType"] == "chunks_only":

        return ChunksOnlyGDMGenerator(p1=p1, flags=flags).get_gdm_file()

    else:

        raise NotImplementedError
