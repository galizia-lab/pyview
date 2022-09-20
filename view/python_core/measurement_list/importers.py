import pathlib as pl
from tillvisionio.vws import VWSDataManager
import pandas as pd
import tifffile
from view.python_core.misc import excel_datetime
import typing
import easygui
import logging
import pprint
import datetime
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
from view.python_core.io import LIFReaderGio


def calculate_dt_from_timing_ms(timing_ms: str) -> float:

    times = timing_ms.strip()
    times = [float(x) for x in times.split(' ')]
    # calculate frame rate as time of (last frame - first frame) / (frames-1)
    dt = (times[-1] - times[0]) / (len(times) - 1)
    return dt


# a function injecting code into the automatic parsing of metadata from vws.log file
def additional_cols_func(s):

    # time & analyze
    try:
        dt = calculate_dt_from_timing_ms(s["Timing_ms"])
        analyze = 1  # since there are at least two frames, and thus a time, I suppose it is worth analyzing
    except Exception as e:
        dt = -1
        analyze = 0

    return {"dt": dt, "Analyze": analyze}


class BaseImporter(ABC):

    def __init__(self, default_values: typing.Mapping):

        super().__init__()
        self.default_values = default_values
        self.associated_extensions = None
        self.associate_file_type = None
        self.LE_loadExp = None
        self.movie_data_extensions = None

    def get_default_row(self):

        return pd.Series(self.default_values)

    def import_metadata(self, raw_data_files, measurement_filter):

        combined_df = pd.DataFrame()

        for fle_ind, fle in enumerate(raw_data_files):

            logging.getLogger("VIEW").info(f"Parsing metadata from {fle}")
            df = self.parse_metadata(fle, fle_ind, measurement_filter)

            combined_df = combined_df.append(df, ignore_index=True)

        return combined_df

    def get_filetype_info_string(self):

        return [f"*{x}" for x in self.associated_extensions] + [self.associate_file_type]

    def ask_for_files(self, default_dir, multiple: bool = True) -> dict:

        default_dir_str = str(pl.Path(default_dir) / "*")
        files_chosen = easygui.fileopenbox(
            title=f"Choose one or more files for LE_loadExp={self.LE_loadExp}",
            filetypes=self.get_filetype_info_string(),
            multiple=multiple,
            default=default_dir_str)
        if files_chosen is None:
            raise IOError("User Abort while choosing files.")
        else:
            assert files_chosen[0].startswith(str(default_dir)), \
                f"The data selected in not in the expected data directory of the current tree:\n" \
                f"{default_dir}. Please copy your data there and try again!"
            animal_tag_raw_data_mapping = self.get_animal_tag_raw_data_mapping(files_chosen)
            logging.getLogger("VIEW").info(
                f"Working on the following animal tags and their corresponding files:\n"
                f"{pprint.pformat(animal_tag_raw_data_mapping)}")
            return animal_tag_raw_data_mapping

    @abstractmethod
    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool]) -> pd.DataFrame:
        """
        Reads and returns the metadata from a metadata file
        :param str fle: path of a metadata file
        :param int fle_ind: integer representing the row order of the measurement associated with <fle>,
        if it is part of a series
        :param Callable measurement_filter: only used for Till Vision setups. See tillvisionio.VWSDataManager.get_all_metadata
        :rtype: pd.DataFrame
        :return: the columns of the DataFrame returned must be a subset of the metadata columns defined in `view/flags_and_metadata_definitions/metadata_definition.csv`
        """

        pass

    @abstractmethod
    def get_animal_tag_raw_data_mapping(self, files_chosen: list) -> dict:
        """
        Parses the animal tag from raw data file names (<file_chosen>). Revises the raw data file names if necessary.
        Returns a one-element dictionary with the animal tag as key and list of (revised) raw data files as value.
        :param list files_chosen: list of raw data file names
        :rtype: dict
        """
        pass

    @abstractmethod
    def get_path_relative_to_data_dir(self, fle):
        """
        Creates a string representing the path of the raw data file <fle> relative to the data directory represented
        by the flag "STG_Datapath" (Eg.: "01_DATA")
        :param fle: path of the raw data file as parsed from the metadata file
        :rtype: str
        """
        pass


class TillImporter(BaseImporter, ABC):

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.associate_file_type = "VWS Log Files"
        self.associated_extensions = [".vws.log"]
        self.movie_data_extensions = [".pst", ".ps"]

    def get_animal_tag_raw_data_mapping(self, files_chosen: list) -> dict:

        if len(files_chosen) == 0:
            return {}
        else:
            dict2return = {}
            for fle in files_chosen:

                fle_path = pl.Path(fle)
                dict2return[fle_path.name.split(".")[0]] = [fle]

            return dict2return

    def get_path_relative_to_data_dir(self, fle):

        for extension in self.movie_data_extensions:
            if fle.endswith(extension):
                fle_path = pl.PureWindowsPath(fle)
                possible_dbb1 = str(pl.Path(fle_path.parts[-2]) / fle_path.stem)
                return 1, str(possible_dbb1)

        else:
            return 0, "wrong extension"

    def convert_vws_names_to_lst_names(self, vws_measurement_series, default_row):
        """
        Convert values from vws.log nomenclaure to internal measurement list nomenclature
        :param vws_measurement_series: pandas.Series
        :param default_row: pandas.Series with default values
        :return: pandas.series
        """

        logging.getLogger("VIEW").info(f'Parsing measurement with label {vws_measurement_series["Label"]}')
        lst_line = default_row.copy()
        lst_line['Measu'] = vws_measurement_series['index'] + 1
        lst_line['Label'] = vws_measurement_series['Label']

        expected_data_file = vws_measurement_series["Location"]
        if expected_data_file[-2:] == 'ps':
            # there is one version of the macro in tillVision that "eats" the last t of the file name
            logging.getLogger("VIEW").warning('adding a t to the .ps file name to make it .pst')
            expected_data_file += 't'

        analyze, dbb1_relative = self.get_path_relative_to_data_dir(expected_data_file)
        if analyze == 0:
            logging.getLogger("VIEW").warning(
                f"Data file {expected_data_file} not found! Setting analyze=0 for this measurement")
        lst_line['DBB1'] = dbb1_relative
        lst_line["Analyze"] = analyze * int(lst_line.get("Analyze", 1))
        lst_line['Cycle'] = vws_measurement_series["dt"]
        lst_line['Lambda'] = vws_measurement_series['MonochromatorWL_nm']
        lst_line['UTC'] = vws_measurement_series['UTCTime']

        return pd.DataFrame(lst_line).T

    def get_mtime(self, utc, first_utc):

        time_since_first_utc = pd.to_timedelta(utc - first_utc, unit="s")
        return str(time_since_first_utc).split(" days ")[1]


class TillImporterOneWavelength(TillImporter):

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.LE_loadExp = 3

    # for till data, metadata is contained in vws.log file
    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool]) -> pd.DataFrame:
        vws_manager = VWSDataManager(fle)
        measurements = vws_manager.get_all_metadata(filter=measurement_filter,
                                                    additional_cols_func=additional_cols_func)
        first_utc = vws_manager.get_earliest_utc()
        this_lst_frame = pd.DataFrame()

        if len(measurements) == 0:
            logging.getLogger("VIEW").warning(
                f"In {fle}: No usable measurements found for given 'measurement_filter' function")

        for measurement_index, measurement_row in measurements.iterrows():
            lst_line = self.convert_vws_names_to_lst_names(vws_measurement_series=measurement_row,
                                                           default_row=self.get_default_row(),
                                                           )
            lst_line["MTime"] = self.get_mtime(utc=lst_line["UTC"][0], first_utc=first_utc)
            this_lst_frame = this_lst_frame.append(lst_line, ignore_index=True)

        return this_lst_frame


class TillImporterTwoWavelength(TillImporter):

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.LE_loadExp = 4

    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool]) -> pd.DataFrame:

        vws_manager = VWSDataManager(fle)
        measurements_wl340_df, measurements_wl380_df \
            = vws_manager.get_metadata_two_wavelengths(wavelengths=(340, 380), filter=measurement_filter,
                                                       additional_cols_func=additional_cols_func)
        first_utc = vws_manager.get_earliest_utc()
        this_lst_frame = pd.DataFrame()

        for (ind1, measurement_wl340), (ind2, measurement_wl380) in zip(measurements_wl340_df.iterrows(),
                                                                        measurements_wl380_df.iterrows()):
            lst_line_wl340 = self.convert_vws_names_to_lst_names(measurement_wl340, self.get_default_row())
            lst_line_wl380 = self.convert_vws_names_to_lst_names(measurement_wl380, self.get_default_row())
            lst_line_wl340["dbb2"] = lst_line_wl380["DBB1"]
            lst_line_wl340["MTime"] = self.get_mtime(utc=lst_line_wl340["UTC"][0], first_utc=first_utc)
            lst_line_wl380["Analyze"] = 0
            lst_line_wl380["MTime"] = self.get_mtime(utc=lst_line_wl380["UTC"][0], first_utc=first_utc)

            this_lst_frame = this_lst_frame.append(lst_line_wl340, ignore_index=True)
            this_lst_frame = this_lst_frame.append(lst_line_wl380, ignore_index=True)

        return this_lst_frame


class LifImporter(BaseImporter):
    """
    importer for Leica Confocal/2-Photon .lif files
    """

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.associate_file_type = "Leica .lif files"  # short text describing raw data files
        self.associated_extensions = [".lif"]  # possible extensions of files containing metadata
        self.movie_data_extensions = [".lif"]  # possible extension of file containing data (calcium imaging movies)
        self.LE_loadExp = 21  # associated value of the flag LE_loadExp

    def get_animal_tag_raw_data_mapping(self, files_chosen: list) -> dict:
        """
        Returns a one-element dictionary with the animal tag as key and list of (revised) raw data files as value.

        Parameters
        ----------
        files_chosen : list
            list of lif files.

        Returns
        -------
        dict
            file names without path.

        """
        if len(files_chosen) == 0:
            return {}
        else:
            dict2return = {}
            for fle in files_chosen:

                fle_path = pl.Path(fle)
                dict2return[fle_path.name] = [fle]

            return dict2return

    def get_path_relative_to_data_dir(self, fle):

        for movie_data_extension in self.movie_data_extensions:
            if fle.endswith(movie_data_extension):
                fle_path = pl.PureWindowsPath(fle)
                return 1, str(fle_path.stem)
        else:
            return 0, -1

    def convert_lif_metadata_to_lst_row(self, fle, measu, lif_metadata_single, default_row):
        """
        Convert values from  lif metadata to .lst nomenclature
        for a particular measurement
        """
        
        lst_line = default_row.copy()

        lst_line["Label"] = lif_metadata_single["Label"]
        lst_line["Cycle"] = lif_metadata_single["Cycle"]
        lst_line["Lambda"] = lif_metadata_single["Lambda"]

        lst_line["PxSzX"] = lif_metadata_single["PxSzX"]
        lst_line["PxSzY"] = lif_metadata_single["PxSzX"]  # y-size

        analyze, dbb1_relative = self.get_path_relative_to_data_dir(fle)
        lst_line["DBB1"] = dbb1_relative
        lst_line["Analyze"] = analyze
        lst_line["Measu"] = measu

        lst_line['SampFreq'] = lif_metadata_single["SampFreq"]
        lst_line['FrameSizeX'] = lif_metadata_single["FrameSizeX"]
        lst_line['FrameSizeY'] = lif_metadata_single["FrameSizeY"]
        lst_line['NumFrames'] = lif_metadata_single["NumFrames"]
        lst_line['Comment'] = lif_metadata_single["Comment"]

        lst_line["UTC"] = lif_metadata_single["UTC"]
        lst_line["MTime"] = lif_metadata_single["MTime"]

        return pd.DataFrame(lst_line).T

    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool] = True) -> pd.DataFrame:
        lif_reader = LIFReaderGio(fle)
        all_lif_metadata = lif_reader.load_all_metadata()

        this_lst_frame = pd.DataFrame()

        # iterate all measurements
        for fle_ind, lst_row in all_lif_metadata.iterrows():

            if lst_row["NumFrames"] > 1:

                lst_line = self.convert_lif_metadata_to_lst_row(
                    fle, fle_ind, lst_row,
                    default_row=self.get_default_row()
                )

                this_lst_frame = this_lst_frame.append(lst_line, ignore_index=True)

        return this_lst_frame


class LSMImporter(BaseImporter):

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.associate_file_type = "Zeiss LSM files"  # short text describing raw data files
        self.associated_extensions = [".lsm"]  # possible extensions of files containing metadata
        self.movie_data_extensions = [".lsm"]  # possible extension of file containing data (calcium imaging movies)
        self.LE_loadExp = 20  # associated value of the flag LE_loadExp

    def get_path_relative_to_data_dir(self, fle):

        for movie_data_extension in self.movie_data_extensions:
            if fle.endswith(movie_data_extension):
                fle_path = pl.PureWindowsPath(fle)
                return 1, str(pl.Path(fle_path.parts[-3]) / fle_path.parts[-2] / fle_path.stem)
        else:
            return 0, -1

    def convert_lsm_metadata_to_lst_row(self, measu, fle, lsm_metadata, default_row):
        """
        Convert values from lsm_metadata to .lst nomenclature
        :param lsm_metadata: dict, like the one returned by tifffile.TiffFile.lsm_metadata
        :param default_row: pandas.Series, with default values
        :return: pandas.Series
        """

        lst_line = default_row.copy()
        lst_line["Label"] = lsm_metadata["ScanInformation"]["Name"]
        # converting from seconds to milliseconds
        lst_line["Cycle"] = lsm_metadata["TimeIntervall"] * 1000
        lst_line["Lambda"] = lsm_metadata["ScanInformation"]["Tracks"][0]["IlluminationChannels"][0]["Wavelength"]
        lst_line['UTC'] = excel_datetime(lsm_metadata["ScanInformation"]["Sample0time"]).timestamp()
        # convert from meters to micrometers
        lst_line["PxSzX"] = lsm_metadata["VoxelSizeX"] / 1e-6
        lst_line["PxSzY"] = lsm_metadata["VoxelSizeY"] / 1e-6

        analyze, dbb1_relative = self.get_path_relative_to_data_dir(fle)
        lst_line["DBB1"] = dbb1_relative
        lst_line["Analyze"] = analyze
        lst_line["Measu"] = measu

        return pd.DataFrame(lst_line).T

    # for till data, a single raw data file is a .lsm file
    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool] = True) -> pd.DataFrame:

        lsm_metadata = tifffile.TiffFile(fle).lsm_metadata

        lst_row = self.convert_lsm_metadata_to_lst_row(measu=fle_ind + 1,
                                                       fle=fle,
                                                       lsm_metadata=lsm_metadata,
                                                       default_row=self.get_default_row())

        return lst_row



class P1SingleWavelengthTIFMultiFileImporter(BaseImporter):
    # added Sept2022 to import single wavelength stored in separate tif files for each frame
    # data from Inga/Einat

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.associate_file_type = "Single Wavelength multi-frame Tif files"  # short text describing raw data files
        self.associated_extensions = [".txt"]  # possible extensions of files containing metadata
        self.movie_data_extensions = [".tif"]  # possible extension of file containing data (calcium imaging movies)
        self.LE_loadExp = 32  # associated value of the flag LE_loadExp


    def convert_metadata_to_lst_row(self, measu, fle, meta_info, default_row):
        """
        Convert values from meta_info to .lst nomenclature
        :param meta_info['PsSzX']: dict, like the one returned by tifffile.TiffFile.lsm_metadata
        :param default_row: pandas.Series, with default values
        :return: pandas.Series
        """

        lst_line = default_row.copy()
        lst_line["Label"] = meta_info['Label']
        # converting from seconds to milliseconds
        lst_line["Cycle"] = meta_info['GDMfreq'] 
        lst_line["Lambda"] = meta_info['Lambda'] 
        lst_line['UTC'] = meta_info['UTCTime'] 
        # convert from meters to micrometers
        lst_line["PxSzX"] = meta_info['PsSzX']
        lst_line["PxSzY"] = meta_info['PsSzY']

        analyze, dbb1_relative = self.get_path_relative_to_data_dir(fle)
        lst_line["DBB1"] = meta_info['dbb1']
        lst_line["dbb2"] = meta_info['dbb2']
        lst_line["Analyze"] = analyze
        lst_line["Measu"] = measu

#additional info
        lst_line["ExposureTime_ms"] = meta_info['ExposureTime_ms']
        lst_line["AcquisitionDate"] = meta_info['AcquisitionDate']
        lst_line["Binning"] = meta_info['Binning']
        lst_line["StartTime"] = meta_info['StartTime']


        return pd.DataFrame(lst_line).T

    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool] = True) -> pd.DataFrame:
        # load metadata from a .txt file, format defined by Inga, 2022
        
        
        meta_dict = read_metadata_txt_file(fle)
        # contains plenty of metadata

        
        
        tif_file=pl.Path(fle)
        with tifffile.TiffFile(tif_file) as tif:
                metadata   = tif.imagej_metadata
                # imagej_metadata does not work any more or never worked on stack - read metadata from first frame
                if metadata is None:
                    metadata = tif.pages[0].description
    
        # extract XML tree from metadata into root
        root = ET.fromstring(metadata)
        # define namespace for OME data
        # this uses xTree OME syntax
        # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element
        ns = {
            "d": "http://www.openmicroscopy.org/Schemas/OME/2013-06"    
        }
        # now get all infos that we put into settings file
        meta_info = root.find("./d:Image/d:Pixels", ns).attrib
      # so far, this works with TillPhotonics .tif files for dual wavelengths (as saved in Trondheim group)
        # recognized by int(meta_info['SizeC']) == 2
        # saved sigle wavelength files have SizeC == 1
        # those settings that do noot exist there, are excluded for now
    
        
  # result is a dictionary, for example:
     #        {'ID': 'Pixels:1-0',
     # 'DimensionOrder': 'XYTZC',
     # 'Type': 'uint16',
     # 'SizeX': '1392',
     # 'SizeY': '1040',
     # 'SizeZ': '1',
     # 'SizeC': '1',
     # 'SizeT': '160',
     # 'PhysicalSizeX': '6.45',
     # 'PhysicalSizeY': '6.45',
     # 'PhysicalSizeZ': '1000',
     # 'SignificantBits': '14'}
        # acquisition date as string, e.g. '2021-09-19T16:49:28'
        AcquisitionDate = root.find("./d:Image/d:AcquisitionDate", ns).text
        meta_info.update({'AcquisitionDate':AcquisitionDate})


    # columns in .settings that need to be filled here:
    # get the tif file, including the last directory
        this_filename = tif_file.parts
        dbb = this_filename[-2] +'/'+ this_filename[-1]
        meta_info.update({'dbb1':dbb})
        meta_info.update({'Label':this_filename[-1]})
        # PxSzX
        # replace the Andor name "PhysicalSizeX' with the Galizia name PsSzX
        meta_info['PsSzX'] = meta_info.pop('PhysicalSizeX')
        meta_info['PsSzY'] = meta_info.pop('PhysicalSizeY')
    # When was this measurement taken?
    # first get the time when the measurement was started: first frame
        first_frame = 1
        num_frames = int(meta_info['SizeT'])
        last_frame = num_frames * int(meta_info['SizeC'])
        root_text_first_frame = "./d:Image/d:Pixels/d:Plane["+str(first_frame)+"]"
        root_text_last_frame  = "./d:Image/d:Pixels/d:Plane["+str(last_frame)+"]"
        time_frame1 = root.find(root_text_first_frame, ns).attrib["DeltaT"]
        time_frame_last = root.find(root_text_last_frame, ns).attrib["DeltaT"]
        # frame interval. Since this is dual wavelength, 
        # take time from first to last, and divide by dimension T
        GDMfreq = (float(time_frame_last) - float(time_frame1)) / num_frames
        GDMfreq = round(GDMfreq*1000) # unit is ms, rounded
        meta_info.update({'GDMfreq':str(GDMfreq)})

        measurementtime = datetime.datetime.fromisoformat(AcquisitionDate)
    # now add the time of the first frame, since measurement start time ie equal for all measurements in one loop
        measurementtime_delta = datetime.timedelta(seconds=float(time_frame1))
        measurementtime = measurementtime + measurementtime_delta
        # StartTime, e.g. 10:05:04
        StartTime = measurementtime.strftime('%H:%M:%S')
        meta_info.update({'StartTime':StartTime})
        # UTC, e.g. 1623229504.482
        UTC = measurementtime.timestamp()
        meta_info.update({'UTCTime':UTC})


# from here, information that is not available in .tif for saved ratios
        if int(meta_info['SizeC']) == 2:
            meta_info.update({'dbb2':dbb}) # copy filename also into column dbb2, since it is dual wavelength
            # binning info, e.g. '1x1'
            Binning = root.find("./d:Image/d:Pixels/d:Channel/d:DetectorSettings", ns).attrib["Binning"]
            meta_info.update({'Binning':Binning})
        # this format is for two-wavelength recording,
        # so I take exposure time for frame 3 and 4
        # just in case the very first one would be strange
            ExposureTime_ms = float(root.find("./d:Image/d:Pixels/d:Plane[3]", ns).attrib["ExposureTime"])
            ExposureTime_ms_340 = int(1000*ExposureTime_ms) # value in Andor is in seconds
            ExposureTime_ms = float(root.find("./d:Image/d:Pixels/d:Plane[4]", ns).attrib["ExposureTime"])
            ExposureTime_ms_380 = int(1000*ExposureTime_ms) # value in Andor is in seconds
            ExposureTimeStr = str(ExposureTime_ms_340)+'/'+str(ExposureTime_ms_380)
            meta_info.update({'ExposureTime_ms':ExposureTimeStr})
            meta_info.update({'Lambda':"340/380"}) #most likely this is FURA 
            
            
        else: #single wavelength, ie. SizeC==1
            meta_info.update({'dbb2':'none'}) # copy filename also into column dbb2, since it is dual wavelength
            meta_info.update({'ExposureTime_ms':'unknown'})
            meta_info.update({'Binning':'unknown'})
            meta_info.update({'Lambda':"ratio of 340/380"}) #most likely this is ready made ratio 
        
##example for meta_info now: 
 #    {'ID': 'Pixels:1-0',
 # 'DimensionOrder': 'XYCTZ',
 # 'Type': 'uint16',
 # 'SizeX': '336',
 # 'SizeY': '256',
 # 'SizeZ': '1',
 # 'SizeC': '2',
 # 'SizeT': '100',
 # 'PhysicalSizeZ': '1000',
 # 'SignificantBits': '16',
 # 'AcquisitionDate': '2019-08-14T14:44:29',
 # 'Binning': '4x4',
 # 'GDMfreq': '34',
 # 'ExposureTime_ms': '13',
 # 'dbb': '190815_h2_El/A_3.tif',
 # 'Label': 'A_3.tif',
 # 'PsSzX': '1.3',
 # 'PsSzY': '1.3',
 # 'StartTime': '14:44:29',
 # 'UTCTime': 1565786669.06601}

        lst_row = self.convert_metadata_to_lst_row(measu=fle_ind + 1,
                                                       fle=fle,
                                                       meta_info=meta_info,
                                                       default_row=self.get_default_row())
        return lst_row



    def get_animal_tag_raw_data_mapping(self, files_chosen: list) -> dict:

        if len(files_chosen) == 0:
            return {}
        else:
            parents = [pl.Path(fle).parent for fle in files_chosen]
            assert all(x == parents[0] for x in parents), f"Tif files specified for constructing measurement " \
                                                          f"list file do no belong to the same directory: " \
                                                          f"{files_chosen}"
            return {parents[0].parent.name: files_chosen}


    def get_path_relative_to_data_dir(self, fle):

        for movie_data_extension in self.movie_data_extensions:
            if fle.endswith(movie_data_extension):
                fle_path = pl.PureWindowsPath(fle)
                return 1, str(pl.Path(fle_path.parts[-3]) / fle_path.parts[-2] / fle_path.stem)
        else:
            return 0, -1




class P1DualWavelengthTIFSingleFileImporter(BaseImporter):
    # added Dec2021, to import single tiff file with dual wavelength as used in Trondheim
    # or also single wavelength (e.g. Ratio) tif files
    # init in view uses read_single_file_fura_tif(filename)

    def __init__(self, default_values: typing.Mapping):

        super().__init__(default_values)
        self.associate_file_type = "Dual Wavelength Tif files"  # short text describing raw data files
        self.associated_extensions = [".tif"]  # possible extensions of files containing metadata
        self.movie_data_extensions = [".tif"]  # possible extension of file containing data (calcium imaging movies)
        self.LE_loadExp = 35  # associated value of the flag LE_loadExp

    def get_path_relative_to_data_dir(self, fle):

        for movie_data_extension in self.movie_data_extensions:
            if fle.endswith(movie_data_extension):
                fle_path = pl.PureWindowsPath(fle)
                return 1, str(pl.Path(fle_path.parts[-3]) / fle_path.parts[-2] / fle_path.stem)
        else:
            return 0, -1

    def convert_metadata_to_lst_row(self, measu, fle, meta_info, default_row):
        """
        Convert values from meta_info to .lst nomenclature
        :param meta_info['PsSzX']: dict, like the one returned by tifffile.TiffFile.lsm_metadata
        :param default_row: pandas.Series, with default values
        :return: pandas.Series
        """

        lst_line = default_row.copy()
        lst_line["Label"] = meta_info['Label']
        # converting from seconds to milliseconds
        lst_line["Cycle"] = meta_info['GDMfreq'] 
        lst_line["Lambda"] = meta_info['Lambda'] 
        lst_line['UTC'] = meta_info['UTCTime'] 
        # convert from meters to micrometers
        lst_line["PxSzX"] = meta_info['PsSzX']
        lst_line["PxSzY"] = meta_info['PsSzY']

        analyze, dbb1_relative = self.get_path_relative_to_data_dir(fle)
        lst_line["DBB1"] = meta_info['dbb1']
        lst_line["dbb2"] = meta_info['dbb2']
        lst_line["Analyze"] = analyze
        lst_line["Measu"] = measu

#additional info
        lst_line["ExposureTime_ms"] = meta_info['ExposureTime_ms']
        lst_line["AcquisitionDate"] = meta_info['AcquisitionDate']
        lst_line["Binning"] = meta_info['Binning']
        lst_line["StartTime"] = meta_info['StartTime']


        return pd.DataFrame(lst_line).T

    # for till data, a single raw data file 
    def parse_metadata(self, fle: str, fle_ind: int,
                       measurement_filter: typing.Callable[[pd.Series], bool] = True) -> pd.DataFrame:
        # load metadata
        
        
        tif_file=pl.Path(fle)
        with tifffile.TiffFile(tif_file) as tif:
                metadata   = tif.imagej_metadata
                # imagej_metadata does not work any more or never worked on stack - read metadata from first frame
                if metadata is None:
                    metadata = tif.pages[0].description
    
        # extract XML tree from metadata into root
        root = ET.fromstring(metadata)
        # define namespace for OME data
        # this uses xTree OME syntax
        # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element
        ns = {
            "d": "http://www.openmicroscopy.org/Schemas/OME/2013-06"    
        }
        # now get all infos that we put into settings file
        meta_info = root.find("./d:Image/d:Pixels", ns).attrib
      # so far, this works with TillPhotonics .tif files for dual wavelengths (as saved in Trondheim group)
        # recognized by int(meta_info['SizeC']) == 2
        # saved sigle wavelength files have SizeC == 1
        # those settings that do noot exist there, are excluded for now
    
        
  # result is a dictionary, for example:
     #        {'ID': 'Pixels:1-0',
     # 'DimensionOrder': 'XYTZC',
     # 'Type': 'uint16',
     # 'SizeX': '1392',
     # 'SizeY': '1040',
     # 'SizeZ': '1',
     # 'SizeC': '1',
     # 'SizeT': '160',
     # 'PhysicalSizeX': '6.45',
     # 'PhysicalSizeY': '6.45',
     # 'PhysicalSizeZ': '1000',
     # 'SignificantBits': '14'}
        # acquisition date as string, e.g. '2021-09-19T16:49:28'
        AcquisitionDate = root.find("./d:Image/d:AcquisitionDate", ns).text
        meta_info.update({'AcquisitionDate':AcquisitionDate})


    # columns in .settings that need to be filled here:
    # get the tif file, including the last directory
        this_filename = tif_file.parts
        dbb = this_filename[-2] +'/'+ this_filename[-1]
        meta_info.update({'dbb1':dbb})
        meta_info.update({'Label':this_filename[-1]})
        # PxSzX
        # replace the Andor name "PhysicalSizeX' with the Galizia name PsSzX
        meta_info['PsSzX'] = meta_info.pop('PhysicalSizeX')
        meta_info['PsSzY'] = meta_info.pop('PhysicalSizeY')
    # When was this measurement taken?
    # first get the time when the measurement was started: first frame
        first_frame = 1
        num_frames = int(meta_info['SizeT'])
        last_frame = num_frames * int(meta_info['SizeC'])
        root_text_first_frame = "./d:Image/d:Pixels/d:Plane["+str(first_frame)+"]"
        root_text_last_frame  = "./d:Image/d:Pixels/d:Plane["+str(last_frame)+"]"
        time_frame1 = root.find(root_text_first_frame, ns).attrib["DeltaT"]
        time_frame_last = root.find(root_text_last_frame, ns).attrib["DeltaT"]
        # frame interval. Since this is dual wavelength, 
        # take time from first to last, and divide by dimension T
        GDMfreq = (float(time_frame_last) - float(time_frame1)) / num_frames
        GDMfreq = round(GDMfreq*1000) # unit is ms, rounded
        meta_info.update({'GDMfreq':str(GDMfreq)})

        measurementtime = datetime.datetime.fromisoformat(AcquisitionDate)
    # now add the time of the first frame, since measurement start time ie equal for all measurements in one loop
        measurementtime_delta = datetime.timedelta(seconds=float(time_frame1))
        measurementtime = measurementtime + measurementtime_delta
        # StartTime, e.g. 10:05:04
        StartTime = measurementtime.strftime('%H:%M:%S')
        meta_info.update({'StartTime':StartTime})
        # UTC, e.g. 1623229504.482
        UTC = measurementtime.timestamp()
        meta_info.update({'UTCTime':UTC})


# from here, information that is not available in .tif for saved ratios
        if int(meta_info['SizeC']) == 2:
            meta_info.update({'dbb2':dbb}) # copy filename also into column dbb2, since it is dual wavelength
            # binning info, e.g. '1x1'
            Binning = root.find("./d:Image/d:Pixels/d:Channel/d:DetectorSettings", ns).attrib["Binning"]
            meta_info.update({'Binning':Binning})
        # this format is for two-wavelength recording,
        # so I take exposure time for frame 3 and 4
        # just in case the very first one would be strange
            ExposureTime_ms = float(root.find("./d:Image/d:Pixels/d:Plane[3]", ns).attrib["ExposureTime"])
            ExposureTime_ms_340 = int(1000*ExposureTime_ms) # value in Andor is in seconds
            ExposureTime_ms = float(root.find("./d:Image/d:Pixels/d:Plane[4]", ns).attrib["ExposureTime"])
            ExposureTime_ms_380 = int(1000*ExposureTime_ms) # value in Andor is in seconds
            ExposureTimeStr = str(ExposureTime_ms_340)+'/'+str(ExposureTime_ms_380)
            meta_info.update({'ExposureTime_ms':ExposureTimeStr})
            meta_info.update({'Lambda':"340/380"}) #most likely this is FURA 
            
            
        else: #single wavelength, ie. SizeC==1
            meta_info.update({'dbb2':'none'}) # copy filename also into column dbb2, since it is dual wavelength
            meta_info.update({'ExposureTime_ms':'unknown'})
            meta_info.update({'Binning':'unknown'})
            meta_info.update({'Lambda':"ratio of 340/380"}) #most likely this is ready made ratio 
        
##example for meta_info now: 
 #    {'ID': 'Pixels:1-0',
 # 'DimensionOrder': 'XYCTZ',
 # 'Type': 'uint16',
 # 'SizeX': '336',
 # 'SizeY': '256',
 # 'SizeZ': '1',
 # 'SizeC': '2',
 # 'SizeT': '100',
 # 'PhysicalSizeZ': '1000',
 # 'SignificantBits': '16',
 # 'AcquisitionDate': '2019-08-14T14:44:29',
 # 'Binning': '4x4',
 # 'GDMfreq': '34',
 # 'ExposureTime_ms': '13',
 # 'dbb': '190815_h2_El/A_3.tif',
 # 'Label': 'A_3.tif',
 # 'PsSzX': '1.3',
 # 'PsSzY': '1.3',
 # 'StartTime': '14:44:29',
 # 'UTCTime': 1565786669.06601}

        lst_row = self.convert_metadata_to_lst_row(measu=fle_ind + 1,
                                                       fle=fle,
                                                       meta_info=meta_info,
                                                       default_row=self.get_default_row())
        return lst_row



    def get_animal_tag_raw_data_mapping(self, files_chosen: list) -> dict:

        if len(files_chosen) == 0:
            return {}
        else:
            parents = [pl.Path(fle).parent for fle in files_chosen]
            assert all(x == parents[0] for x in parents), f"Tif files specified for constructing measurement " \
                                                          f"list file do no belong to the same directory: " \
                                                          f"{files_chosen}"
            return {parents[0].parent.name: files_chosen}


def get_importer_class(LE_loadExp):

    if LE_loadExp == 3:

        return TillImporterOneWavelength

    elif LE_loadExp == 4:

        return TillImporterTwoWavelength

    elif LE_loadExp == 20:

        return LSMImporter
    
    elif LE_loadExp == 21:

        return LifImporter
    
    elif LE_loadExp == 32:
        # single wavelength TIFF, each frame stored separately

        return P1SingleWavelengthTIFMultiFileImporter 
        # works also for ratio files, not yet tested for other single file tif formats

    elif LE_loadExp == 33:
        # single wavelength TIFF

        return P1DualWavelengthTIFSingleFileImporter 
        # works also for ratio files, not yet tested for other single file tif formats

    elif LE_loadExp == 35:

        return P1DualWavelengthTIFSingleFileImporter

    else:

        raise NotImplementedError


def get_setup_extension(LE_loadExp):
    """
    returns the file extension of raw data file of the setup specified by <LE_loadExp>
    :param int LE_loadExp: value of the flag of the same name
    :rtype: list
    """
    importer_class = get_importer_class(LE_loadExp)
    return importer_class({}).movie_data_extension
