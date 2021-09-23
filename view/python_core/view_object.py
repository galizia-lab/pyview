import logging
import pathlib as pl
import shutil
import sys
import tempfile
import time

from pkg_resources import get_distribution
from .flags import FlagsManager
from view.python_core.gdm_generation import get_roi_gdm_traces_dict, get_gdm_file
from .measurement_list import MeasurementList
from .measurement_list.importers import get_setup_extension
from .movies import export_movie
from .overviews import generate_overview_image, generate_overview_image_for_output
from .overviews.ctv_handlers import get_ctv_handler
from .p1_class import get_empty_p1, get_p1
from .rois.roi_io import get_roi_io_class
import gc


class VIEW(object):

    def __init__(self, flags=None, terminal_output_verbose=True):
        """
        Initializes a VIEW object with default flags
        """
        self.flags = FlagsManager()
        if flags is not None:
            self.flags.update_flags({"STG_MotherOfAllFolders": flags["STG_MotherOfAllFolders"]})
            self.flags.update_flags({k: v for k, v in flags.items() if k not in ["STG_MotherOfAllFolders"]})

        self.flags.update_flags({"VIEW_batchmode": True})
        self.measurement_list = None
        self.p1 = None
        self.log_file = self.setup_logging(terminal_output_verbose)
        logging.getLogger("VIEW").info(
            f"VIEW object initialized for offline use. Version: {get_distribution('view').version}")

    def __del__(self):

        del self.flags
        self.delete_data()

    def delete_data(self):

        try:
            self.p1.__del__()
            del self.measurement_list
        except AttributeError as ae:
            pass

        self.p1 = None
        self.measurement_list = None
        gc.collect()

    def setup_logging(self, terminal_output_verbose):

        my_logger = logging.getLogger("VIEW")
        my_logger.propagate = False
        my_logger.setLevel(level=logging.INFO)

        if not my_logger.hasHandlers():

            temp_dir = tempfile.gettempdir()
            view_log_dir_path = pl.Path(temp_dir) / "VIEW_logs"
            view_log_dir_path.mkdir(exist_ok=True)
            log_file_path = view_log_dir_path / f"VIEW_started_at_{time.strftime('%Y-%m-%d-%H-%M-%S')}.log"
            formatter = logging.Formatter("%(asctime)s [VIEW] [%(levelname)-5.5s] %(message)s")

            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(level=logging.INFO)
            file_handler.setFormatter(formatter)
            my_logger.addHandler(file_handler)

            if terminal_output_verbose:
                stream_handler = logging.StreamHandler(sys.stdout)
                stream_handler.setLevel(level=logging.DEBUG)
                stream_handler.setFormatter(formatter)
                my_logger.addHandler(stream_handler)

            log_file = str(log_file_path)

        else:

            file_handler = [x for x in my_logger.handlers if isinstance(x, logging.FileHandler)][0]
            log_file = file_handler.baseFilename

        return log_file

    def update_flags(self, flags):
        """
        Updates VIEW flags with <flags>
        :param flags: dict, keys are flag names, values are flag values
        :return: None
        """
        self.flags.update_flags(flags)

    def update_flags_from_ymlfile(self, yml_filename):
        """
        Updates VIEW flags with flags from YML file
        :param yml_filename: str, path on file system to a YML flags file
        :return: None
        """
        self.flags.read_flags_from_yml(yml_filename)
        self.flags.update_flags({"VIEW_batchmode": True})

    def initialize_animal(self, animal):
        """
        Initializes the flag "STG_ReportTag" to <animal>. Tries to find and load the measurement list file
        for the animal <animal>. Raises FileNotFoundError if not found.
        :param animal: string, name/tag of the animal
        """

        self.flags.update_flags({
            "STG_ReportTag": animal
        })

        lst_file = self.flags.get_existing_lst_file()

        if lst_file is None:
            raise FileNotFoundError(f"Could not find a list file for animal={animal} "
                                    f"in {self.flags['STG_OdorInfoPath']}")

        self.measurement_list = MeasurementList.create_from_lst_file(
            lst_fle=lst_file, LE_loadExp=self.flags["LE_loadExp"])

    def initialize_animal_from_list_file(self, list_file):
        """
        Extracts the stem of the list file name and uses it as animal name ("STG_ReportTag"). Initializes the specified
        animal list
        :param list_file:
        """

        self.measurement_list = MeasurementList.create_from_lst_file(
            lst_fle=list_file, LE_loadExp=self.flags["LE_loadExp"])

        assert self.measurement_list.animal_name is not None, "Something went wrong!"
        self.flags.update_flags({"STG_ReportTag": self.measurement_list.animal_name})

    def get_current_animal(self):

        self.check_if_animal_is_initialized()

        return self.flags['STG_ReportTag']

    def check_if_animal_is_initialized(self):
        """
        Raises an error if no animal has been initialized
        """

        if self.measurement_list is not None:
            measurement_list_name = pl.Path(self.measurement_list.last_measurement_list_fle).name
            if measurement_list_name.startswith(f"{self.flags['STG_ReportTag']}."):
                return  # all good

        raise ValueError("No animal initialized, "
                         "please initialize first VIEW with an animal using the method 'initialize_animal'")

    def get_measus_for_current_animal(self, analyze_values_to_use=None):
        """
        Returns a list of "measu" values for the currently initialized animal, for which the corresponding entry in the
        column 'Analyze' is one among <analyze_to_use>. If <analyze_values_accepted> is None,
        then all measus for the animal are returned
        :return: list of int
        """

        self.check_if_animal_is_initialized()
        return self.measurement_list.get_measus(analyze_values_accepted=analyze_values_to_use)

    def get_measu_label_for_current_animal(self, measu):
        """
        Returns the measurement label for the measurement corresponding to <measu> based of current flag settings.
        :raises: AssertionError if animal is not initialized
        :return: str, measurent label
        """

        self.check_if_animal_is_initialized()
        return self.flags.get_measurement_label(measurement_row=self.measurement_list.get_row_by_measu(measu))

    def load_measurement_data_from_current_animal(self, measu):
        """
        Loads the measurement from current animal with the specified <measu>
        :param measu: int
        :return: str, label of the measurement as specified by the flag "LE_labelColumns"
        """

        self.check_if_animal_is_initialized()

        self.flags.update_flags({"STG_Measu": measu})

        measu_label, self.p1 = self.measurement_list.load_data(flags=self.flags, measu=measu)

        return measu_label

    def calculate_signals(self):
        """
        Calculates signals using the raw data currently loaded and using current flag values. Raises an ValueError if
        no raw data has been loaded
        :returns: None
        """

        if self.p1 is not None:
            self.p1.calculate_signals(self.flags)
        else:
            raise ValueError("No raw data has been loaded. Load some raw data and try calculating signals again!")

    def load_measurement_data(self, animal, measu):
        """
        Loads the measurement with the specified <measu> for the specified animal.
        :param animal: str, name of the animal, (usually name of the list file/vws file without extension)
        :param measu: int
        :return: str, label of the measurement as specified by the flag "LE_labelColumns"
        """

        # self.measurement_list can be not None only if an animal had been initialized and
        # when an animal has been initialized, flag 'STG_ReportTag' gets set
        if not(self.measurement_list is not None and self.flags["STG_ReportTag"] == animal):
            self.initialize_animal(animal)

        return self.load_measurement_data_from_current_animal(measu)

    def load_measurement_data_without_list_file(
            self, raw_data_files, sampling_rate, LE_loadExp, animal='unspecified_animal'):
        """
        Load data into VIEW directly from raw data files without needing measurement list files
        :param sequence raw_data_files: list of raw data files. Must be compatible with the flag `LE_loadExp`
        :param float sampling_rate: in Hz, number of frames measured per second
        :param LE_loadExp: value of the flag of the same name, please see its documentation
        :param str animal: optional animal tag
        """

        self.flags.update_flags({"LE_loadExp": LE_loadExp})

        self.p1 = get_empty_p1(LE_loadExp=self.flags["LE_loadExp"])

        # needed for looking if a usable area file exists
        self.flags.update_flags({'STG_ReportTag': animal})

        self.p1.load_without_metadata(filenames=raw_data_files, flags=self.flags, sampling_rate=sampling_rate)

    def export_movie_for_current_measurement(self):
        """
        Export a movie with the current flag settings and for the measurement data currently loaded
        :return: str, path of the movie output file written or output directory for when mv_exportFormat='single_tif'
        """

        if self.p1.sig1 is None:
            self.calculate_signals()

        movie_dir_path = pl.Path(self.flags.get_op_movie_dir())
        movie_dir_path.mkdir(parents=True, exist_ok=True)
        measurement_row = self.measurement_list.get_row_by_measu(self.flags["STG_Measu"])
        user_spec_label = self.flags.get_measurement_label(measurement_row)
        op_filepath_stem = str(movie_dir_path / user_spec_label)

        if self.p1.sig1 is None:
            self.calculate_signals()
        return export_movie(flags=self.flags, p1=self.p1,
                            full_filename_without_extension=op_filepath_stem)

    def get_roi_info_for_current_animal(self):
        """
        Reads and returns ROI information for the current animal
        :return: roi_data_dict, roi_file
        roi_data_dict: dict with roi labels as keys and roi data objects as values
        roi_file: str, file from which ROI information was taken
        """

        roi_data_dict, roi_file = get_roi_io_class(self.flags["RM_ROITrace"]).read(flags=self.flags)

        return roi_data_dict, roi_file

    def get_gdm_file_for_current_measurement(self, roi_data_dict=None):
        """
        Creates and returns a GDMFile object containing a list of GDMRow object, each of which contains metadata and
        the time trace associated with a ROI.
        If <roi_data_dict> is None, ROIs are interpreted using the flags RM_ROITrace
        :param dict roi_data_dict: dict with roi labels as keys and roi data objects as values
        :return: roi_data_dict, gdm_file
        roi_data_dict: a dictionary with ROI labels as keys and ROI data objects as values
        gdm_file: view.python_core.gdm_generation.gdm_data_classes.GDMFile object
        """

        roi_label_gdm_traces_dict, roi_data_dict = self.get_roi_gdm_traces_dict(roi_data_dict)

        gdm_file = get_gdm_file(p1=self.p1, flags=self.flags)

        return gdm_file, roi_data_dict
    
    def get_roi_gdm_traces_dict(self, roi_data_dict=None):
        """
        Returns a dictionary of roi labels and corresponding time traces as numpy arrays.
        If <roi_data_dict> is None, ROIs are interpreted using the flags RM_ROITrace
        :param dict roi_data_dict: dict with roi labels as keys and roi data objects as values
        :return: roi_data_dict, gdm_file
        roi_data_dict: a dictionary with ROI labels as keys and ROI data objects as values
        roi_label_gdm_traces_dict: a dictionary with ROI labels as keys and corresponding time traces as values
        """

        if self.p1.sig1 is None:
            self.calculate_signals()

        if roi_data_dict is None:
            roi_data_dict, roi_file = get_roi_io_class(self.flags["RM_ROITrace"]).read(
                flags=self.flags, measurement_label=self.p1.metadata.ex_name)
        
        roi_label_gdm_traces_dict = get_roi_gdm_traces_dict(p1=self.p1, flags=self.flags, roi_data_dict=roi_data_dict)

        return roi_label_gdm_traces_dict, roi_data_dict

    def generate_ctv_response_frame_for_current_measurement(self):
        """
        Reduce 3D signal into 2D response frame by applying CTV function as defined by flags
        :return: response_frame, 2D numpy.ndarray
        """

        if self.p1.sig1 is None:
            self.calculate_signals()

        ctv_handler = get_ctv_handler(flags=self.flags, p1=self.p1)

        return ctv_handler.apply(self.p1.sig1)

    def generate_overview_for_current_measurement(self):
        """
        Generate an overview of the measurement data currently loaded based on current flags and returns it
        :return: overview_frame, data_limits, overview_generator_used
        overview_frame: 2D numpy.ndarray, the overview image in XY format with origin at bottom left
        data_limits: tuple, the lower and upper limits of data in overview image
        overview_generator_used: OverviewColorizerAnnotator object used to generate overview
        """

        if self.p1.sig1 is None:
            self.calculate_signals()
        return generate_overview_image(flags=self.flags, p1=self.p1)

    def generate_overview_for_output_for_current_measurement(self):
        """
        Generates overview frame and transforms it so that it can be readily used either for plt.imshow or for
        saving with tifffile.imsave
        :return: overview_frame, data_limits
        overview_frame: 2D numpy.ndarray, the overview image in YX format with origin at top right
        data_limits: tuple, the lower and upper limits of data in overview image
        """

        if self.p1.sig1 is None:
            self.calculate_signals()
        return generate_overview_image_for_output(flags=self.flags, p1=self.p1)

    def backup_files(self, files, target_directory):
        """
        Copies all files in <files> to the target directory, inserting "last_used" before suffix
        :param files: list of strings, each pointing to a file on the file system
        :param target_directory: str, pointing to a directory on the file system
        """

        for file in files:
            file_path = pl.Path(file)
            target_filename = f"{file_path.stem}_last_used{file_path.suffix}"
            target_file = pl.Path(target_directory) / target_filename
            logging.getLogger("VIEW").info(f"Backing up {file} to {target_file}")
            shutil.copy(file, str(target_file))

    def backup_script_flags_configs_for_GDMs(self, files):
        """
        Copies all files in <files> to the traces output folder of the animal currently initialized
        :param files: list of strings, each pointing to a file on the file system
        """

        target_directory = self.flags.get_animal_op_dir()

        self.backup_files(files + [self.log_file], target_directory)

    def backup_script_flags_configs_for_movies(self, files):
        """
        Copies all files in <files> to the movies output folder of the animal currently initialized
        :param files: list of strings, each pointing to a file on the file system
        """

        target_directory = self.flags.get_op_movie_dir()

        self.backup_files(files + [self.log_file], target_directory)

    def backup_script_flags_configs_for_tapestries(self, files):
        """
        Copies all files in <files> to the tapestries output folder for the animal <animal>
        :param files: list of strings, each pointing to a file on the file system
        """

        # view_obj = cls()
        # view_obj.update_flags_from_ymlfile(yml_file)
        # view_obj.initialize_animal(animal)
        #
        target_directory = self.flags.get_op_tapestries_dir()
        #
        # # logging does not write anything if the created object is not returned?? Manually writing version
        # with open(view_obj.log_file_obj.name, 'w') as fh:
        #     fh.write(f"VIEW object initialized for offline use. Version: {get_distribution('view').version}")

        self.backup_files(files + [self.log_file], target_directory)

    def get_current_setup_extension(self):

        return get_setup_extension(self.flags["LE_loadExp"])

    def get_measu_label(self, measu):

        return self.flags.get_measurement_label(measurement_row=self.measurement_list.get_row_by_measu(measu))

    def backup_script_flags_configs_for_processed_data_output(self, files, format_name):
        """
        Copies all files in <files> to the output folder for processed data for format in `format_name`.
        :param files: list of strings, each pointing to a file on the file system
        """

        target_directory = self.flags.get_processed_data_op_path(format_name)

        self.backup_files(files + [self.log_file], target_directory)
