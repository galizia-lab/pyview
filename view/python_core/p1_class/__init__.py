from view.idl_translation_core.ViewLoadData import create_raw_data666
from .metadata_related import MetadataDefinition, parse_p1_metadata_from_measurement_list_row
from .filters import apply_filter
from view.python_core.bleach_corr import get_bleach_compensator
from view.python_core.background import get_background_frames
from view.python_core.areas import get_area_for_p1, get_area_for_bleach_correction
from view.python_core.measurement_list.importers import LSMImporter, IngaTif_Importer
from view.python_core.foto import calc_foto1
from view.python_core.io import load_pst, read_lsm, read_tif_2Dor3D, read_single_file_fura_tif, read_lif, read_SingleWavelengthTif_MultiFileInga
from view.python_core.paths import get_existing_raw_data_filename
from view.python_core.stimuli import PulsedStimuliiHandler
from view.python_core.calc_methods import get_calc_method
import pathlib as pl
import pandas as pd
import copy
import numpy as np
from scipy.ndimage import gaussian_filter
import logging
import gc
from abc import ABC, abstractmethod


class P1SingleWavelengthAbstract(ABC):

    @abstractmethod
    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        pass

    @abstractmethod
    def read_data(self, filename: str):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        pass

    def __init__(self):

        super().__init__()
        self.metadata = None  # pandas.Series or dict
        self.extra_metadata = None  # dict
        self.raw1 = None  # numpy.ndarray, format XYT
        self.raw2 = None  # numpy.ndarray, format XYT
        self.foto1 = None  # numpy.ndarray, format XY
        self.foto2 = None  # numpy.ndarray, format XY
        self.sig1 = None  # numpy.ndarray, format XYT
        self.area_mask = None  # numpy.ndarray, format XY

        # an object of PulsedStimuliiHandler or some other subclass of BaseStimuliiHandler
        self.pulsed_stimuli_handler = None

    def __del__(self):

        to_del = [
            "metadata", "extra_metadata", "raw1", "raw2", "foto1", "foto2", "sig1",
            "pulsed_stimuli_handler", "area_mask"
        ]

        for obj in to_del:

            if hasattr(self, obj):
                eval(f"self.{obj}")

        gc.collect()

    def initialize_raw_data_size(self, raw_data_size):
        """
        Add metadata about the dimensions of raw data
        :param sequence raw_data_size: size of raw data
        """

        self.metadata.format_x, self.metadata.format_y, self.metadata.frames = raw_data_size

    def initialize_raw_data(self, raw_data):
        """
        Load raw data and initialize associated metadata
        :param list raw_data: list of raw data
        """

        self.initialize_raw_data_size(raw_data[0].shape)

        self.raw1 = raw_data[0]

        # calculate foto1
        self.foto1 = calc_foto1(self.raw1)

        # Loading Air not implemented

    def get_frame_size(self):
        """
        Return the frame size of this measurement as a 2 member tuple (XY)
        :rtype: tuple
        """

        return self.metadata.format_x, self.metadata.format_y

    def correct_raw_data(self, raw_data, p1_metadata, flags):

        # if the flag replace_init_frames is 2, replace the first two frames with the third
        frames2replace = flags["Data_ReplaceInitFrames"]
        if frames2replace < raw_data.shape[2]:

            temp = raw_data.swapaxes(0, 2)  # convert TYX, otherwise the frame replacement takes more commands
            temp[:frames2replace, :, :] = temp[frames2replace, :, :]
            raw_data = temp.swapaxes(0, 2)  # convert back to XYT
        else:
            logging.getLogger("VIEW").warning(
                f"value of the flag Data_ReplaceInitFrames ({flags['Data_ReplaceInitFrames']}) "
                f"is too large for the number of frames loaded ({raw_data.shape[2]}). Not Replacing any frames!")

        # apply median filter first, then mean filter, depending on flags
        raw_data = apply_filter(matrix_in=raw_data, view_flags=flags, filter_type="median")
        raw_data = apply_filter(matrix_in=raw_data, view_flags=flags, filter_type="mean")

        # apply light scattering compensation using unsharp masking
        # see Pg 376 of Galizia & Vetter(2004).
        # "Optical Methods for Analyzing Odor-Evoked Activity in the Insect Brain."
        # https://doi.org/10.1201/9781420039429.ch13
        smoothfactor = flags["LE_ScatteredLightFactor"]

        if smoothfactor > 0:

            corrected_raw_data = np.empty_like(raw_data)

            smoothradius_um = flags["LE_ScatteredLightRadius"]

            smX = smoothradius_um / p1_metadata.pixelsizex
            smY = smoothradius_um / p1_metadata.pixelsizey
            smoothradius = (smX + smY) / 2.0
            if smX != smY:
                logging.getLogger("VIEW").warning('unequal pixel size not implemented yet - averaging x and y value')

            for frame_ind in range(raw_data.shape[2]):
                current_frame = raw_data[:, :, frame_ind]

                # calculate correction
                correction = current_frame - gaussian_filter(current_frame, smoothradius, mode='nearest')

                # smooth correction so as to not enhance noise
                smoothed_correction = gaussian_filter(correction, smoothradius, mode='nearest')

                # apply correction
                corrected_raw_data[:, :, frame_ind] = current_frame + smoothfactor * smoothed_correction

        else:
            corrected_raw_data = raw_data

        # apply bleach correction depending on flags
        bleach_compensator = get_bleach_compensator(flags=flags, p1_metadata=p1_metadata, movie_size=raw_data.shape)

        area_mask_for_p1 = get_area_for_p1(frame_size=raw_data.shape[:2], flags=flags)

        area_mask_for_bleach_correction = get_area_for_bleach_correction(
            area_mask_for_p1, LE_BleachCutBorder=flags['LE_BleachCutBorder'],
            LE_BleachExcludeArea=flags["LE_BleachExcludeArea"])

        bleach_corrected_raw_data, bleach_fit_params = bleach_compensator.apply(
            stack_xyt=corrected_raw_data, area_mask=area_mask_for_bleach_correction)

        return area_mask_for_p1, bleach_corrected_raw_data, bleach_fit_params

    def load_correct_raw_data(self, p1_metadata, flags):
        """
        Reads data, applies median filters, applies mean filters, applies scatter light correction,
        applies bleach correction and return the resulting data. It also loads area from an area file
        if present, uses it for bleach correction and returns it
        :param pd.Series p1_metadata: metadata
        :param FlagsManager flags:
        :return: filename, area_mask_for_p1, bleach_corrected_raw_data, bleach_fit_params
        filename: absolute path of the file containing the raw data
        area_mask_for_p1: area mask read if an area file was found, else an numpy array of ones
        bleach_corrected_raw_data: processed raw data, as described above
        bleach_fit_params: params used for bleach fitting
        """
        # read raw1
        try:
            logging.getLogger("VIEW").info(f"Reading raw data")
            filename, raw_data = self.read_data_with_defaulting(metadata=p1_metadata, flags=flags)
        except FileNotFoundError as fnfe:
            raise IOError(
                f"Problem loading raw data from dbb1. Please check the measurement row selected in the "
                f"measurement list file. Original Error:\n {str(fnfe)}")

        area_mask_for_p1, bleach_corrected_raw_data, bleach_fit_params = self.correct_raw_data(
            raw_data=raw_data, p1_metadata=p1_metadata, flags=flags
        )

        return filename, area_mask_for_p1, [bleach_corrected_raw_data], bleach_fit_params

    def load_from_metadata(self, p1_metadata: pd.Series, flags, extra_metadata=None):

        # initialize give values of metadata and extra_metadata
        self.metadata = p1_metadata
        if extra_metadata is not None:
            self.extra_metadata = extra_metadata

        # initialize background frames.
        # Needed for movement and bleach correction, in addition to signal calculation
        self.metadata.background_frames = get_background_frames(p1_metadata=p1_metadata, flags=flags)

        # LE_ShrinkFacktor not implemented

        # load and correct raw data
        # self.area_mask is calculated inside self.load_correct_raw_data because it needs frame_size,
        # which can only be known after loading data
        filename, self.area_mask, bleach_corrected_raw_data, bleach_fit_params \
            = self.load_correct_raw_data(p1_metadata=p1_metadata, flags=flags)

        self.metadata.bleachpar = bleach_fit_params

        # initialize raw data
        self.initialize_raw_data(raw_data=bleach_corrected_raw_data)

        # saving the complete filename of raw data for reference
        self.metadata["full_raw_data_path_str"] = filename

        self.pulsed_stimuli_handler = self.metadata["pulsed_stimuli_handler"]
        data_sampling_period = pd.to_timedelta(self.metadata['trial_ticks'], unit='ms')
        self.pulsed_stimuli_handler.initialize_stimulus_offset(flags["mv_correctStimulusOnset"], data_sampling_period)

    def load_without_metadata(self, filenames, flags, sampling_rate=5):
        """
        load raw data in p1 structure directly, without other metadata
        :param sequence filenames: raw data file names, compatible with the flag `LE_loadExp`
        :param FlagManager flags:
        :param sampling_rate: in Hz, number of frames measured per second
        """

        p1_metadata, extra_metadata = self.get_p1_metadata_from_filenames(filenames=filenames)
        assert sampling_rate > 0, f"Invalid sampling rate specified ({sampling_rate})"
        p1_metadata['trial_ticks'] = 1000.0 / sampling_rate
        p1_metadata["frequency"] = sampling_rate

        self.load_from_metadata(p1_metadata=p1_metadata, flags=flags)

    def get_default_extension(self):

        return ".tif"

    def read_data_with_defaulting(self, metadata: pd.Series, flags):
        """
        Tries to find and read data with the extension given by <get_extension>. If file was not found, tries to find
        and read a '.tif.' file in the same indicated path.
        :param pandas.Series metadata:
        :param FlagsManager flags:
        :rtype: tuple
        :return: (filename, raw_data)
            filename: str, path of the file found
            raw_data: np.ndarray
        """
        current_extensions = self.get_extensions()
        default_extension = self.get_default_extension()

        try:
            filename = get_existing_raw_data_filename(flags=flags, dbb=metadata.dbb1, extensions=current_extensions)
            if pl.Path(filename).suffix in current_extensions:
                logging.getLogger("VIEW").info(f"(read_data_with_defaulting 1) Reading raw data from {filename}")
                if ('.txt' in current_extensions) or ('.lif' in current_extensions):
                    #a .lif file containse several measurement, read_data for measu only
                    #similarly a .txt file in INGA multi tiff format
                    return filename, self.read_data(filename, flags.flags['STG_Measu'])
                else:
                    logging.getLogger("VIEW").info(f"(read_data_with_defaulting 1) Cannot read raw data from {filename}")
                    return filename, self.read_data(filename)
            else:
                raise FileNotFoundError()

        except FileNotFoundError as fnfe:
            try:
                filename = get_existing_raw_data_filename(
                    flags=flags, dbb=metadata.dbb1, extensions=[default_extension])
                if pl.Path(filename).suffix == default_extension:
                    logging.getLogger("VIEW").info(f"(read_data_with_defaulting 2) Reading raw data from {filename}")
                    data, _ = read_tif_2Dor3D(filename)
                    return filename, data
                else:
                    logging.getLogger("VIEW").info(f"(read_data_with_defaulting 2) Cannot read raw data from {filename}")
                    raise FileNotFoundError()
            except FileNotFoundError as fnfe:
                raise FileNotFoundError(f"{repr(fnfe)}.\n "
                                        f"Looked for data with extension '{current_extensions}' and "
                                        f"'{default_extension}'")

    def copy(self):

        new_p1 = self.__class__()
        new_p1.metadata = self.metadata.copy()
        new_p1.extra_metadata = self.extra_metadata.copy()
        new_p1.raw1 = self.raw1
        new_p1.foto1 = self.foto1
        new_p1.sig1 = self.sig1
        new_p1.pulsed_stimuli_handler = self.pulsed_stimuli_handler
        new_p1.raw2 = self.raw2
        new_p1.foto2 = self.foto2
        return new_p1

    def calculate_signals(self, flags):

        raw_data = self.get_raw_data()
        assert self.area_mask is not None
        assert self.metadata.background_frames is not None

        calc_method = get_calc_method(flags)
        self.sig1 = calc_method(
            raw_data=raw_data, background_frames=self.metadata.background_frames, area_mask=self.area_mask)

    def get_raw_data(self):

        assert self.raw1 is not None, "Cannot access raw data as they have not yet been loaded. Please" \
                                      "load some raw data using the methods 'load_from_metadata' or " \
                                      "'load_without_metadata'"

        return [self.raw1]

    def get_p1_metadata_from_filenames(self, filenames):
        """
        Create a p1_metadata object only using raw data filenames in <filenames>. Use defaults or guesses
        for metadata not directly deducible from raw data filenames
        :param list filenames: list of raw data file names
        :return: p1_metadata, extra_metadata
        p1_metadata: pandas.Series object,
        extra_metadata: dict
        (see view.python_core.p1_class.metadata_related.parse_p1_metadata_from_measurement_list_row)
        """
        p1_metadata, extra_metadata = Default_P1_Getter().get_p1_metadata_without_measurement_list()
        p1_metadata.dbb1 = filenames[0]
        label = pl.Path(filenames[0]).name.split(".")[0]
        p1_metadata.ex_name = label
        return p1_metadata, extra_metadata
    

class P1SingleWavelengthTIF(P1SingleWavelengthAbstract):
    
    def __init__(self):
        
        super().__init__()
    
    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".tif"]
    
    def read_data(self, filename: str):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        data, _ = read_tif_2Dor3D(filename)
        return data


class P1SingleWavelength_multiTIFInga(P1SingleWavelengthAbstract):
    '''
    Measurement XYT is stored in separate Tiff file for each frame/timepoint
    '''
    
    def __init__(self):
        
        super().__init__()
    
    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".txt", "/protocol.txt"] #this is the filename of Inga's information about the data
    
    def read_data(self, filename: str, measu: int):
        """
        read and return data in <filename_list>. Data is expected to be a numpy.ndarray of format XYT
        :param list filename_list: absolute path of raw data files for each frame on file system
        :rtype: numpy.ndarray
        """
        if measu is None:
            measu = 0 # default to the first measurement
            print('p1_class/__init__.py: P1SintleWavelength_multiTIFInga.read_data defaulted to measurement 0')
        
        data = read_SingleWavelengthTif_MultiFileInga(filename, measu)
        return data

    def get_p1_metadata_from_filename(self, filename, measu):
        """
        Create a p1_metadata object from Inga's .txt file that is written with the data for each experiment
        filename is this .txt file
        
        Create a p1_metadata object only using raw data filenames in <filenames>. Use defaults or guesses
        for metadata not directly deducible from raw data filenames
        :param list filenames: list of raw data file names
        :return: p1_metadata, extra_metadata
        p1_metadata: pandas.Series object,
        extra_metadata: dict
        (see view.python_core.p1_class.metadata_related.parse_p1_metadata_from_measurement_list_row)
        """

        Inga_Importer = IngaTif_Importer(default_values=MetadataDefinition().get_default_row())
        # selection of the first row is required as this function returns a one-row DataFrame
        rows = Inga_Importer.parse_metadata(fle=filename, fle_ind=measu)
        row = rows['Measu'] == measu # select teh row for this measurement
        # revise index names to be lower case
        row.rename(index={x: x.lower() for x in row.index.values}, inplace=True)
        
        p1_metadata, extra_metadata = parse_p1_metadata_from_measurement_list_row(row)
        p1_metadata.ex_name = p1_metadata.label

        return p1_metadata, extra_metadata


class P1SingleWavelengthLIF(P1SingleWavelengthAbstract):
    """
    Load Leica .lif file data
    """
    
    def __init__(self):
        
        super().__init__()
    
    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".lif"]
    
    def read_data(self, filename: str, measu: int):
        """
        read and return data in <filename>, image <measu>. 
        Data is expected to be a .lif file
        :param str filename: absolute path of lif data file on file system
        : param int measu: leica image number in the lif file
        :rtype: numpy.ndarray
        """
        data = read_lif(filename, measu)
        return data


class P1SingleWavelengthTill(P1SingleWavelengthAbstract):

    def __init__(self):

        super().__init__()

    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".pst", ".ps"]

    def read_data(self, filename):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        return load_pst(filename)


class P1SingleWavelengthLSM(P1SingleWavelengthAbstract):

    def __init__(self):

        super().__init__()

    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".lsm"]

    def read_data(self, filename):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        return read_lsm(filename)

    def get_p1_metadata_from_filenames(self, filenames):
        """
        Create a p1_metadata object only using raw data filenames in <filenames>. Use defaults or guesses
        for metadata not directly deducible from raw data filenames
        :param list filenames: list of raw data file names
        :return: p1_metadata, extra_metadata
        p1_metadata: pandas.Series object,
        extra_metadata: dict
        (see view.python_core.p1_class.metadata_related.parse_p1_metadata_from_measurement_list_row)
        """

        lsm_importer = LSMImporter(default_values=MetadataDefinition().get_default_row())
        # selection of the first row is required as this function returns a one-row DataFrame
        row = lsm_importer.parse_metadata(fle=filenames[0], fle_ind=-2).iloc[0]
        # revise index names to be lower case
        # row.rename(index={x: x.lower() for x in row.index.values}, inplace=True)
        p1_metadata, extra_metadata = parse_p1_metadata_from_measurement_list_row(row)
        p1_metadata.dbb1 = filenames[0]
        label = pl.Path(filenames[0]).name.split(".")[0]
        p1_metadata.ex_name = label

        return p1_metadata, extra_metadata


class P1DualWavelengthAbstract(P1SingleWavelengthAbstract, ABC):

    @abstractmethod
    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        pass

    @abstractmethod
    def read_data(self, filename: str):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        pass

    @abstractmethod
    def get_p1_metadata_from_filenames(self, filenames):
        """
        Create a p1_metadata object only using raw data filenames in <filenames>. Use defaults or guesses
        for metadata not directly deducible from raw data filenames
        :param list filenames: list of raw data file names
        :return: p1_metadata, extra_metadata
        p1_metadata: pandas.Series object,
        extra_metadata: dict
        (see view.python_core.p1_class.metadata_related.parse_p1_metadata_from_measurement_list_row)
        """
        pass

    def __init__(self):

        super().__init__()

    def initialize_raw_data(self, raw_data):
        """
        Load raw data and initialize associated metadata
        :param list raw_data: list of raw data
        """

        self.raw1, self.raw2 = raw_data

        self.initialize_raw_data_size(self.raw1.shape)

        # calculate foto1
        self.foto1 = calc_foto1(self.raw1)

        # calculate foto2
        self.foto2 = calc_foto1(self.raw2)

        # Loading Air not implemented

    def get_raw_data(self):
        assert self.raw1 is not None and self.raw2 is not None, \
            "Cannot calculate signals as raw data has bot yet been loaded. Please" \
            "load some raw data using the methods 'load_from_metadata' or " \
            "'load_without_metadata'"

        return [self.raw1, self.raw2]


class P1DualWavelengthTIFTwoFiles(P1DualWavelengthAbstract):

    def __init__(self):

        super().__init__()

    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".tif"]

    def read_data(self, filename: str):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        data, _ = read_tif_2Dor3D(filename)
        return data

    def load_correct_raw_data(self, p1_metadata, flags):
        """
        Reads data, applies median filters, applies mean filters, applies scatter light correction,
        applies bleach correction and return the resulting data. It also loads area from an area file
        if present, uses it for bleach correction and returns it
        :param pd.Series p1_metadata: metadata
        :param FlagsManager flags:
        :return: filename, area_mask_for_p1, bleach_corrected_raw_data, bleach_fit_params
        filename: absolute path of the file containing the raw data
        area_mask_for_p1: area mask read if an area file was found, else an numpy array of ones
        bleach_corrected_raw_data: processed raw data, as described above
        bleach_fit_params: params used for bleach fitting
        """

        # read and correct raw1
        filename1, area_mask, [bleach_corrected_raw_data1], bleach_fit_params1 \
            = super().load_correct_raw_data(p1_metadata=p1_metadata, flags=flags)

        # read raw2
        metadata_copy = copy.copy(self.metadata)
        metadata_copy.dbb1 = metadata_copy.dbb2

        filename2, area_mask, [bleach_corrected_raw_data2], bleach_fit_params2 \
            = super().load_correct_raw_data(p1_metadata=metadata_copy, flags=flags)

        # make sure the shapes of data belonging to the two wavelength match
        assert bleach_corrected_raw_data1.shape == bleach_corrected_raw_data2.shape, \
            f"Shapes of the movie data of the two wavelengths do not match: " \
            f"{bleach_corrected_raw_data1.shape}, {bleach_corrected_raw_data2.shape}"

        return \
            filename1, area_mask, [bleach_corrected_raw_data1, bleach_corrected_raw_data2], \
            [bleach_fit_params1, bleach_fit_params2]

    def get_p1_metadata_from_filenames(self, filenames):
        """
        Create a p1_metadata object only using raw data filenames in <filenames>. Use defaults or guesses
        for metadata not directly deducible from raw data filenames
        :param list filenames: list of raw data file names
        :return: p1_metadata, extra_metadata
        p1_metadata: pandas.Series object,
        extra_metadata: dict
        (see view.python_core.p1_class.metadata_related.parse_p1_metadata_from_measurement_list_row)
        """

        dbb1_filename, dbb2_filename = filenames

        p1_metadata, extra_metadata = Default_P1_Getter().get_p1_metadata_without_measurement_list()

        p1_metadata.dbb1 = dbb1_filename
        p1_metadata.dbb2 = dbb2_filename

        dbb1_stem = pl.Path(dbb1_filename).name.split(".")[0]
        dbb2_stem = pl.Path(dbb2_filename).name.split(".")[0]
        label = f"{dbb1_stem}_{dbb2_stem}"
        p1_metadata.ex_name = label

        return p1_metadata, extra_metadata


class P1DualWavelengthTill(P1DualWavelengthTIFTwoFiles):

    def __init__(self):
        super().__init__()

    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".pst", ".ps"]

    def read_data(self, filename):
        """
        read and return data in <filename>. Data is expected to be a numpy.ndarray of format XYT
        :param str filename: absolute path of raw data file on file system
        :rtype: numpy.ndarray
        """
        return load_pst(filename)


class P1SingleWavelength666(P1SingleWavelengthAbstract):

    def __init__(self, peaksignal=10):

        super().__init__()
        self.peaksignal = peaksignal

    def read_data_with_defaulting(self, metadata: pd.Series, flags):
        """
        Creates fake data 666 and returns it with a fake filename
        :param pandas.Series metadata:
        :param FlagsManager flags:
        :rtype: tuple
        :return: (filename, raw_data)
            filename: str, path of the file found
            raw_data: np.ndarray
        """

        raw_data666 = create_raw_data666(p1_metadata=metadata, peaksignal=self.peaksignal)

        return str(pl.Path(flags["STG_Datapath"]) / f"{metadata.dbb1}.fake"), raw_data666

    def load_without_metadata(self, filenames, flags, sampling_rate=5):
        """
        load raw data in p1 structure directly, without other metadata
        :param sequence filenames: raw data file names, compatible with the flag `LE_loadExp`
        :param FlagManager flags:
        :param sampling_rate: unused, hardcoded below
        """

        # for all other cases, it is better to not override the current method and instead override
        # get_p1_metadata_from_filenames. However, I am overriding the current method as an exception as
        # I need to make sure that stimulus information gets added, without which "loading", i.e., creating synthetic
        # data would fail.

        label = pl.Path(filenames[0]).name.split(".")[0]
        fake_measurement_list_row = MetadataDefinition().get_default_row()
        fake_measurement_list_row.update(
            {
                    "DBB1": label,
                    "Label": label,
                    # need to add stimulus information here as it is later needed when loading data, i.e., in this
                    # case, creating synthetic data
                    "StimON": 25,
                    "StimOFF": 35,
                    "Stim2ON": 65,
                    "Stim2OFF": 75
                }
            )

        p1_metadata, extra_metadata = parse_p1_metadata_from_measurement_list_row(fake_measurement_list_row)

        self.load_from_metadata(p1_metadata=p1_metadata, flags=flags, extra_metadata=extra_metadata)

    def read_data(self, filename: str):

        raise NotImplementedError

    def get_extensions(self):

        raise NotImplementedError


class P1SingleWavelength676(P1SingleWavelength666):

    def __init__(self, peaksignal):

        super().__init__(peaksignal)

    def read_data_with_defaulting(self, metadata: pd.Series, flags):
        """
        Creates fake data 666, restrict it to 10x10x10 and returns it with a fake filename
        :param pandas.Series metadata:
        :param FlagsManager flags:
        :rtype: tuple
        :return: (filename, raw_data)
            filename: str, path of the file found
            raw_data: np.ndarray
        """

        raw_data666 = create_raw_data666(p1_metadata=metadata, peaksignal=self.peaksignal)

        return str(pl.Path(flags["STG_Datapath"]) / f"{metadata.dbb1}.fake"), raw_data666[:50, :50, :50]

    def read_data(self, filename: str):
        raise NotImplementedError

    def get_extensions(self):
        raise NotImplementedError


class P1DualWavelengthTIFSingleFile(P1DualWavelengthAbstract):
    #created Dec 2021 for Till Trondheim Data: 340 & 380 in one file

    def __init__(self):

        super().__init__()

    def get_extensions(self):
        """
        list of allowed file extensions. E.g.: [".tif"]
        :rtype: list
        """
        return [".tif"]

    def read_data(self, filename: str):
        """
        read and return data in <filename>.
        :param str filename: absolute path of raw data file on file system
        :rtype: tuple
        :returns: data_340, data_380
        data_340: 340nm data as an numpy.ndarray, format XYT
        data_380: 340nm data as an numpy.ndarray, format XYT
        """
        return read_single_file_fura_tif(filename)

    def load_correct_raw_data(self, p1_metadata, flags):
        """
        Reads data, applies median filters, applies mean filters, applies scatter light correction,
        applies bleach correction and return the resulting data. It also loads area from an area file
        if present, uses it for bleach correction and returns it
        :param pd.Series p1_metadata: metadata
        :param FlagsManager flags:
        :return: filename, area_mask_for_p1, bleach_corrected_raw_data, bleach_fit_params
        filename: absolute path of the file containing the raw data
        area_mask_for_p1: area mask read if an area file was found, else an numpy array of ones
        bleach_corrected_raw_data: processed raw data, as described above
        bleach_fit_params: params used for bleach fitting
        """

        # read raw data
        try:
            logging.getLogger("VIEW").info(f"Reading raw data from ")
            filename, raw_data = self.read_data_with_defaulting(metadata=p1_metadata, flags=flags)
        except FileNotFoundError as fnfe:
            raise IOError(
                f"Problem loading raw data from dbb1. Please check the measurement row selected in the "
                f"measurement list file. Original Error:\n {str(fnfe)}")

        area_mask_for_p1, bleach_corrected_raw_data_340, bleach_fit_params_340 = self.correct_raw_data(
            raw_data=raw_data[0], p1_metadata=p1_metadata, flags=flags
        )

        area_mask_for_p1, bleach_corrected_raw_data_380, bleach_fit_params_380 = self.correct_raw_data(
            raw_data=raw_data[1], p1_metadata=p1_metadata, flags=flags
        )

        return \
            filename, area_mask_for_p1, \
            [bleach_corrected_raw_data_340, bleach_corrected_raw_data_380], \
            [bleach_fit_params_340, bleach_fit_params_380]

    def get_p1_metadata_from_filenames(self, filenames):
        """
        Create a p1_metadata object only using raw data filenames in <filenames>. Use defaults or guesses
        for metadata not directly deducible from raw data filenames
        :param list filenames: list of raw data file names
        :return: p1_metadata, extra_metadata
        p1_metadata: pandas.Series object,
        extra_metadata: dict
        (see view.python_core.p1_class.metadata_related.parse_p1_metadata_from_measurement_list_row)
        """

        p1_metadata, extra_metadata = Default_P1_Getter().get_p1_metadata_without_measurement_list()
        p1_metadata.dbb1 = filenames[0]
        label = pl.Path(filenames[0]).name.split(".")[0]
        p1_metadata.ex_name = label
        p1_metadata.lambda_nm = "380, 340"
        return p1_metadata, extra_metadata


def get_empty_p1(LE_loadExp, odor_conc=None):

    if LE_loadExp == 3:
        empty_obj = P1SingleWavelengthTill()
    elif LE_loadExp == 4:
        empty_obj = P1DualWavelengthTill()
    elif LE_loadExp == 20:
        empty_obj = P1SingleWavelengthLSM()
    elif LE_loadExp == 21:
        empty_obj = P1SingleWavelengthLIF()
    elif LE_loadExp == 32:
        empty_obj = P1SingleWavelength_multiTIFInga()
    elif LE_loadExp == 33:
        empty_obj = P1SingleWavelengthTIF()
    elif LE_loadExp == 34:
        empty_obj = P1DualWavelengthTIFTwoFiles()
    elif LE_loadExp == 35:
        empty_obj = P1DualWavelengthTIFSingleFile()
    elif LE_loadExp == 665: # synthetic data set, response negative, fixed response magnitude
        empty_obj = P1SingleWavelength666(peaksignal=-10)
    elif LE_loadExp == 666: # synthetic data set, response magnitude taken from list
        empty_obj = P1SingleWavelength666(peaksignal=odor_conc)
    elif LE_loadExp == 667: # synthetic data set, response positive, fixed response magnitude
        empty_obj = P1SingleWavelength666(peaksignal=10)
    elif LE_loadExp == 676: # synthetic data set 666, clipped
        empty_obj = P1SingleWavelength676(peaksignal=10)
    else:
        raise NotImplementedError

    return empty_obj


def get_p1(p1_metadata, flags, extra_metadata):

    empty_obj = get_empty_p1(flags["LE_loadExp"], p1_metadata.get("odor_nr", None))
    empty_obj.load_from_metadata(p1_metadata, flags, extra_metadata)
    return empty_obj


class Default_P1_Getter():

    def __init__(self):

        super().__init__()
        self._metadata_def = MetadataDefinition()

    def get_p1_metadata_without_measurement_list(self):
        """
        returns an pandas.Series object with all default values.
        :return: metadata of p1 object with all defaults
        :rtype: pandas.Series
        """

        default_row = self._metadata_def.get_default_row()
        default_p1_metadata, default_extra_metadata = parse_p1_metadata_from_measurement_list_row(default_row)
        default_p1_metadata.pulsed_stimuli_handler = PulsedStimuliiHandler()
        return default_p1_metadata, default_extra_metadata

    def get_fake_p1_from_raw(self, raw1, raw2=None):
        """
        returns a p1 object with default values and values related to raw data
        """

        fake_p1 = P1SingleWavelengthTIF()
        fake_p1.metadata, fake_p1.extra_metadata = self.get_p1_metadata_without_measurement_list()
        fake_p1.metadata.format_x, fake_p1.metadata.format_y, fake_p1.metadata.frames = raw1.shape
        fake_p1.raw1 = raw1
        fake_p1.pulsed_stimuli_handler = fake_p1.metadata["pulsed_stimuli_handler"]

        fake_p1.foto1 = calc_foto1(raw1)

        if raw2 is not None and raw1.shape == raw2.shape:
            fake_p1.raw2 = raw2
            fake_p1.foto2 = calc_foto1(raw2)

        return fake_p1
