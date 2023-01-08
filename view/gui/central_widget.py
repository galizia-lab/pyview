import gc
import logging
import os
import pathlib as pl
import sys
import traceback
from inspect import currentframe, getframeinfo

import pandas as pd
import yaml
from PyQt5.QtCore import pyqtSlot, QSettings, pyqtSignal, QObject, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox, QHBoxLayout, QGroupBox, QLabel, \
    QPushButton, QFileDialog, QTabWidget
from matplotlib import pyplot as plt

from view.idl_translation_core.ViewOverview import ExportMovie
from view.python_core.flags import FlagsManager
from view.python_core.foto import show_photo, get_foto1_data
from view.python_core.io import read_check_yml_file
from view.python_core.measurement_list import MeasurementList
from view.python_core.misc import get_system_temp_dir
from view.python_core.movies import export_movie
from view.python_core.overviews import pop_show_overview
from view.python_core.p1_class import get_p1
from .ILTIS_transfer_dialog import ILTISTransferDialog
from .application_settings import get_view_qsettings_manager
from .data_manager import DataManager
from .direct_load import DirectDataLoader
from .file_selector_combobox import get_file_selector_combobox_using_settings
from .flags_box import FlagsDisplayChoiceTabs
from .gdm_visualization import GDMViz
from .load_measurement import LoadMeasurementsFromVWSLogWindow, LoadMeasurementsFromListWindow
from .logger import LoggerGroupBox
from .main_function_widgets import MainFunctionAbstract, OverviewGenWidget
from .setup_calcmethod_choice import SetupChoice


class CentralWidget(QWidget):
    export_data_signal = pyqtSignal(list, list, pd.DataFrame, int, tuple, tuple, int, name="export data")
    reset_iltis_signal = pyqtSignal(name="reset ILTIS")

    def __init__(self, parent):

        super().__init__(parent)

        # declare windows that might be generated
        self.gdm_viz_window = None
        self.load_measurement_window = None

        self.main_function_widgets = {}
        self.misc_function_buttons = {}
        self.p1s = {}

        self.init_flags()
        self.current_measurement_label = None
        self.init_ui()
        self.measurement_list = None
        self.yml_file = None

        plt.ion()

    def __del__(self):

        del self.gdm_viz_window
        del self.load_measurement_window

    def init_flags(self):

        self.flags = FlagsManager()

    def init_ui(self):

        main_hbox = QHBoxLayout(self)

        main_functions_vboxlayout = QVBoxLayout()

        self.setup_choice_box = SetupChoice(self)
        self.setup_choice_box.update_LE_loadExp_flag_signal.connect(self.flag_update_request_gui)
        self.main_function_widgets["setup choice box"] = self.setup_choice_box
        main_functions_vboxlayout.addWidget(self.setup_choice_box)

        # --------------------------------------------------------------------------------------------------------------
        temp_hbox = QHBoxLayout()
        calcMethod_flags = ["LE_CalcMethod"]
        self.calcMethod_box = MainFunctionAbstract(
            parent=self, button_names={},
            flag_names=calcMethod_flags,
            flag_defaults=[self.flags[f] for f in calcMethod_flags],
            group_name="Choose the method for calculating signals "
                       "(does not affect raw data loading and artifact correction)"
        )
        self.calcMethod_box.flag_update_signal.connect(self.flag_update_request_gui)
        self.main_function_widgets["calc method choice box"] = self.calcMethod_box
        temp_hbox.addWidget(self.calcMethod_box)

        button = QPushButton("Close all matplotlib figures")
        button.clicked.connect(self.close_all_matplotlib_figures)

        temp_hbox.addWidget(button)

        main_functions_vboxlayout.addLayout(temp_hbox)

        # --------------------------------------------------------------------------------------------------------------

        loader_tabs = QTabWidget(self)
        main_functions_vboxlayout.addWidget(loader_tabs)

        direct_loader = DirectDataLoader(self, self.setup_choice_box.get_current_LE_loadExp())
        direct_loader.data_loaded_signal.connect(self.direct_load_finalize)
        self.setup_choice_box.return_LE_loadExp.connect(direct_loader.refresh_layout)

        loader_tabs.addTab(direct_loader, "Direct load from raw file (no pre-requirements)")

        log_load_box = QWidget(self)
        log_load_box_layout = QVBoxLayout(log_load_box)

        new_vws_log_load = QPushButton("Load from new vws log file")
        new_vws_log_load.clicked.connect(self.load_from_new_vws_log)

        log_load_box_layout.addWidget(new_vws_log_load)

        choose_from_current_vws_log = QPushButton("Select from current vws.log")
        choose_from_current_vws_log.clicked.connect(self.choose_row_from_current_vws_log)

        log_load_box_layout.addWidget(choose_from_current_vws_log)

        loader_tabs.addTab(log_load_box, "Direct load from log file (no pre-requirements)")

        list_load_box = QWidget(self)
        list_load_vboxlayout = QVBoxLayout(list_load_box)

        yaml_loader = get_file_selector_combobox_using_settings()(
            groupbox_title="The YML file",
            file_filter="YML File(*.yml)",
            file_type="YML",
            parent=self,
            use_list_in_settings="yml_file_list",
        )

        yaml_loader.return_filename_signal.connect(self.load_yml_flags)

        list_load_vboxlayout.addWidget(yaml_loader)

        loading_hbox = QHBoxLayout()

        list_vbox = QVBoxLayout()

        new_load = QPushButton("Load from new list file")
        new_load.clicked.connect(self.load_from_new_list)

        list_vbox.addWidget(new_load)

        self.main_function_widgets["load_lst"] = new_load

        choose_from_current_list = QPushButton("Select row from current list")
        choose_from_current_list.clicked.connect(self.choose_row_from_current_list)

        self.main_function_widgets["select row from current list"] = choose_from_current_list

        list_vbox.addWidget(choose_from_current_list)

        new_vws_log_load = QPushButton("Load from new vws log file")
        new_vws_log_load.clicked.connect(self.load_from_new_vws_log)

        list_vbox.addWidget(new_vws_log_load)

        self.main_function_widgets["select row from new vws log file"] = new_vws_log_load

        choose_from_current_vws_log = QPushButton("Select from current vws.log")
        choose_from_current_vws_log.clicked.connect(self.choose_row_from_current_vws_log)

        self.main_function_widgets["select row from current vws log file"] = choose_from_current_vws_log

        list_vbox.addWidget(choose_from_current_vws_log)

        quick_load_from_current_lst_box_flags = ["STG_Measu"]

        quick_load_from_current_lst_box = MainFunctionAbstract(parent=self,
                                                               group_name="Quick Load",
                                                               button_names=["Quick Load from current list"],
                                                               flag_names=quick_load_from_current_lst_box_flags,
                                                               flag_defaults=[self.flags[f] for f in
                                                                              quick_load_from_current_lst_box_flags],
                                                               stack_vertically=False)
        loading_hbox.addLayout(list_vbox)

        quick_load_from_current_lst_box.send_data.connect(self.quick_load_from_current_lst)
        quick_load_from_current_lst_box.flag_update_signal.connect(self.flag_update_request_gui)

        self.main_function_widgets["quick load from current list"] = quick_load_from_current_lst_box
        loading_hbox.addWidget(quick_load_from_current_lst_box)

        list_load_vboxlayout.addLayout(loading_hbox)
        selected_list_file_box = QGroupBox("List/VWS.LOG file selected", self)
        self.current_measurement_label = QLabel("None selected yet")
        layout = QHBoxLayout(selected_list_file_box)
        layout.addWidget(self.current_measurement_label)
        self.main_function_widgets["selected list file"] = selected_list_file_box
        list_load_vboxlayout.addWidget(selected_list_file_box)

        loader_tabs.addTab(list_load_box, "List load (pre-requirements: YML File, folder structure, "
                                          "measurement list files)")

        # --------------------------------------------------------------------------------------------------------------
        overview_gdm_hbox = QHBoxLayout()
        gen_overviews_box = OverviewGenWidget(parent=self, current_flags=self.flags)
        gen_overviews_box.send_data.connect(self.generate_overview)
        gen_overviews_box.flag_update_signal.connect(self.flag_update_request_gui)

        self.main_function_widgets["generate_overview"] = gen_overviews_box
        overview_gdm_hbox.addWidget(gen_overviews_box)

        # --------------------------------------------------------------------------------------------------------------
        gdm_viz_box_flags = ["RM_ROITrace"]
        gdm_viz_box = MainFunctionAbstract(
            parent=self, button_names=["Visualize GDM traces"],
            flag_names=gdm_viz_box_flags, flag_defaults=[self.flags[f] for f in gdm_viz_box_flags],
            group_name="Visualize GDM traces", stack_vertically=True
        )
        gdm_viz_box.send_data.connect(self.viz_gdm_traces)
        gdm_viz_box.flag_update_signal.connect(self.flag_update_request_gui)
        self.main_function_widgets["viz_gdm"] = gdm_viz_box
        overview_gdm_hbox.addWidget(gdm_viz_box)

        main_functions_vboxlayout.addLayout(overview_gdm_hbox)

        # --------------------------------------------------------------------------------------------------------------
        misc_functions = QGroupBox("Miscellaneous functions", self)
        misc_functions_hbox = QHBoxLayout(misc_functions)
        save_button = QPushButton("Save movie (legacy)", self)
        save_button.clicked.connect(self.save_movie)
        misc_functions_hbox.addWidget(save_button)
        self.misc_function_buttons["save_movie"] = save_button

        save_movie_new = QPushButton("Save Movie (new)")
        save_movie_new.clicked.connect(self.save_movie_new)
        misc_functions_hbox.addWidget(save_movie_new)
        self.misc_function_buttons["save_movie_new"] = save_movie_new

        button2 = QPushButton("Show foto1")
        button2.clicked.connect(self.show_foto1)
        misc_functions_hbox.addWidget(button2)
        self.misc_function_buttons["show_foto1"] = button2

        button3 = QPushButton("Button3")
        button3.clicked.connect(self.button3_func)
        misc_functions_hbox.addWidget(button3)
        self.misc_function_buttons["button3"] = button3

        main_functions_vboxlayout.addWidget(misc_functions)

        main_hbox.addLayout(main_functions_vboxlayout)

        # --------------------------------------------------------------------------------------------------------------
        # --------------------------------------------------------------------------------------------------------------

        right_vbox = QVBoxLayout()

        self.flag_display_choice = FlagsDisplayChoiceTabs(self, self.flags)

        for subgroup_name, subgroup_page in self.flag_display_choice.subgroup_pages.items():
            subgroup_page.return_flag_signal.connect(self.flag_update_request_gui)

        flags_group_box = QGroupBox("Flags Viewer/Editor/Saver")
        flags_vbox = QVBoxLayout(flags_group_box)
        header_hbox = QHBoxLayout()
        header_hbox.addWidget(QLabel("Tip: Click on flag names for description"))
        wiki_link_button = QPushButton("Go to VIEW WIKI")
        wiki_link_button.clicked.connect(self.go_to_wiki)
        header_hbox.addWidget(wiki_link_button)
        save_button = QPushButton("Write flags to file")
        save_button.clicked.connect(self.write_yml_file)
        header_hbox.addWidget(save_button)
        flags_vbox.addLayout(header_hbox)
        flags_vbox.addWidget(self.flag_display_choice)

        right_vbox.addWidget(flags_group_box)

        # --------------------------------------------------------------------------------------------------------------

        data_manager_group_box = QGroupBox("Data Manager")
        data_manager_vbox = QVBoxLayout(data_manager_group_box)

        flags_values2use = \
            ["LE_loadExp", "LE_CalcMethod", "STG_ReportTag", "STG_Measu"] + self.flags.compound_path_flags

        def temp(x):
            return lambda p1: p1.metadata.get(x, "N/A")

        flags_values2use_dict = {k: k for k in flags_values2use}
        p1_values2use = {
            "Component\nOdors": temp("odor"), "Stimulus": temp("stimulus"), "Stimulus\nConcentration": temp("odor_nr"),
            "No. of pulses in stimuli": lambda p1: p1.metadata["pulsed_stimuli_handler"].stimulus_frame.shape[0],
            "Stimulus pulse start times\nrelative to imaging start (s)":
                lambda p1: [x / pd.Timedelta(seconds=1)
                            for x in p1.metadata["pulsed_stimuli_handler"].get_pulse_start_times()],
            "Stimulus pulse end times\nrelative to imaging start (s)":
                lambda p1: [x / pd.Timedelta(seconds=1)
                            for x in p1.metadata["pulsed_stimuli_handler"].get_pulse_end_times()],
            "Measurement\nLabel": temp("ex_name"), "Raw File Name": temp("full_raw_data_path_str"),
            "No. of frames": temp("frames"),
            "Frames per second": lambda p1: p1.metadata.frequency,
            "No. of Pixels along X": temp("format_x"),
            "No. of Pixels along Y": temp("format_y"),
        }

        self.data_manager = DataManager(
            parent=self, flag_values_to_use=flags_values2use_dict, p1_values_to_use=p1_values2use, label_joiner="_",
            default_label_cols=["STG_Measu", "STG_ReportTag"],
            precedence_order=[
                "STG_ReportTag", "STG_Measu", "Measurement\nLabel",
                "Stimulus", "Stimulus\nConcentration", "Component\nOdors",
                "No. of pulses in stimuli", "Stimulus pulse start times\nrelative to imaging start (s)",
                "Stimulus pulse end times\nrelative to imaging start (s)",
                "No. of frames", "Frames per second", "No. of Pixels along X", "No. of Pixels along Y",
                "LE_loadExp", "LE_CalcMethod"]
        )
        self.data_manager.remove_data_signal.connect(self.remove_data)
        data_manager_vbox.addWidget(self.data_manager.ui_table)

        right_vbox.addWidget(data_manager_group_box)

        # --------------------------------------------------------------------------------------------------------------

        self.log_pte = LoggerGroupBox(self)

        right_vbox.addWidget(self.log_pte)

        main_hbox.addLayout(right_vbox)

        # disable all actions other than YML loader
        self.enable_disable_functions_all(
            enable=False, main_exceptions=["yml loader", "setup choice box", "calc method choice box"])

    def close_all_matplotlib_figures(self):

        plt.close("all")

    def enable_disable_functions_all(self, enable,
                                     main_exceptions=(), misc_exceptions=()):

        for main_function, main_function_widget in self.main_function_widgets.items():
            if main_function not in main_exceptions:
                main_function_widget.setEnabled(enable)

        for misc_button_name, misc_button in self.misc_function_buttons.items():
            if misc_button_name not in misc_exceptions:
                misc_button.setEnabled(enable)

    def enable_disable_functions(self, enable, main_functions=(), misc_functions=()):

        for main_function in main_functions:
            self.main_function_widgets[main_function].setEnabled(enable)

        for misc_button_name in misc_functions:
            self.misc_function_buttons[misc_button_name].setEnabled(enable)

    def get_sample_stim_onoff_values(self):

        sample_p1 = self.p1s[self.data_manager.get_all_internal_labels()[0]]

        dict2return = [sample_p1.metadata.stimulus_on,
                       sample_p1.metadata.stimulus_end,
                       sample_p1.metadata.stim2ON,
                       sample_p1.metadata.stim2OFF]

        return dict2return

    @pyqtSlot(name="respond to data request from iltis")
    def spawn_export_dialog(self):

        if len(self.p1s) == 0:
            QMessageBox.critical(self, "No data loaded!", "Please load some data before transferring data to ILTIS")
        else:
            data_manager_df = self.data_manager.df
            all_metadata_columns = data_manager_df.columns.values.tolist()
            metadata_to_choose_from = set(all_metadata_columns) \
                                      - set(self.data_manager.defaultLabelCols + [self.data_manager.label_col_name])
            metadata_to_choose_from = \
                [x.replace("\n", "---") for x in all_metadata_columns if x in metadata_to_choose_from]

            self.transfer_dialog = ILTISTransferDialog(
                data_loaded_df=data_manager_df, metadata_to_choose_from=metadata_to_choose_from
                )
            self.transfer_dialog.send_data_signal.connect(self.export_data)
            self.transfer_dialog.show()
            self.write_status("Waiting for data selection before transfer to ILTIS")

    def export_data(self, indices, metadata_list_for_label):
        '''
        goes through indices (i.e. the selected measurements to move to ILTIS)
        and copies data (p1.raw1) and signals (p1.sig1) etc. into the variables for ILTIS
        i.e. raw_data_list, signals_list etc.
        '''

        raw_data_list = []
        signals_list = []
        n_frames_list = []

        dm_df = self.data_manager.df.copy()
        metadata_to_send = dm_df.iloc[indices]
        stim_onset = []
        stim_offset = []
        for label, metadata_row in metadata_to_send.iterrows():

            p1 = self.p1s[label]

            stimulus_frames = p1.pulsed_stimuli_handler.get_pulse_start_end_frames(allow_fractional_frames=True)
            if len(stimulus_frames):
                stim_onset, stim_offset = zip(*stimulus_frames)
            else:
                stim_onset = stim_offset = ()

            LE_loadExp = metadata_row["LE_loadExp"]
            le_label = self.data_manager.label_line_edits[label].text()

            # the inverse replacement was done for visualization purposes in self.spawn_export_dialog
            metadata_list_for_label = [x.replace("---", "\n") for x in metadata_list_for_label]
            other_metadata_to_send = metadata_row.loc[metadata_list_for_label].values.tolist()
            label_to_use = self.data_manager.label_joiner.join([le_label] + [str(x) for x in other_metadata_to_send])
            if LE_loadExp == 4:
                label_to_use = f"{label_to_use}_FURA({p1.metadata.lambda_nm} nm/Ratio)"
            metadata_to_send.loc[label, "Label to use"] = label_to_use
            raw_data_list.append(p1.raw1)
            signals_list.append(p1.sig1)
            n_frames_list.append(p1.metadata.frames)

        for path_flag in self.flags.compound_path_flags:
            if path_flag not in self.flags.compound_path_flags_with_defaults:
                metadata_to_send[path_flag] = self.flags[path_flag]

        self.export_data_signal.emit(
            raw_data_list, signals_list,
            metadata_to_send, max(n_frames_list), stim_onset, stim_offset, self.flags["RM_Radius"])

    @pyqtSlot(name="export all data")
    def export_data_all(self):
        """
        sends all data loaded into VIEW to ILTIS using export_data above
        """

        self.export_data(indices=slice(None), metadata_list_for_label=[])

    def write_status(self, msg):

        self.parent().statusBar().showMessage(msg)
        logging.getLogger("VIEW").info(msg)

    @pyqtSlot(str, str, name="flag_update_request_from_gui")
    def flag_update_request_gui(self, flag_name, flag_value):

        if not self.check_update_flags_and_gui({flag_name: flag_value}):
            sender = QObject.sender(self)
            sender.reset_flag(flag_name, self.flags[flag_name])

    def check_apply_gui_limitations(self, flags):

        if "LE_BleachCorrMethod" in flags and flags["LE_BleachCorrMethod"] == "log_pixelwise":
            self.flag_display_choice.block_flags_update_signals(True)
            QMessageBox.warning(
                self, "Unavailable bleach correction setting",
                "Pixelwise bleach correction is not supported in VIEW-GUI. Uniform bleach correction"
                "will be applied instead. "
                "If you want to turn bleach correction off, set the flag LE_BleachCorrMethod to None"
            )
            self.flag_display_choice.block_flags_update_signals(False)

            flags["LE_BleachCorrMethod"] = "log_uniform"

        return flags

    def check_update_flags_and_gui(self, flags):

        flags = self.check_apply_gui_limitations(flags)

        for flag_name, flag_value in flags.items():
            if self.flags.is_flag_known(flag_name):
                this_flag_dict = {flag_name: flag_value}
                self.write_status(f"[working] Updating flag {flag_name} to {flag_value}")
                try:
                    self.flags.update_flags(this_flag_dict)
                except AssertionError as ase:
                    self.flag_display_choice.block_flags_update_signals(True)
                    QMessageBox.critical(self, f"Error setting flag {flag_name} to {flag_value}", str(ase))
                    self.write_status(f"[failure] Updating flag {flag_name} to {flag_value}")
                    self.flag_display_choice.block_flags_update_signals(False)
                    return 0
                except (FileNotFoundError, OSError) as fnfe:
                    self.flag_display_choice.block_flags_update_signals(True)
                    QMessageBox.critical(self, f"Error setting flag {flag_name}",
                                         f"There is a problem with the current folder structure and the path flags "
                                         f"specified. Specifically, the value of the flag {flag_name} is inconsistent."
                                         f"\n------\nHere is the full error message:\n{fnfe}")
                    self.write_status(f"[failure] Updating flag {flag_name} to {flag_value}")
                    self.flag_display_choice.block_flags_update_signals(False)
                    return 0
                self._update_functions_flags(this_flag_dict)
                self.flag_display_choice.set_flags(this_flag_dict)
                self.write_status(f"[success] Updating flag {flag_name} to {flag_value}")
            else:
                self.write_status(f"[info] Ignoring update request for unknown flag {flag_name}")
        return 1

    def _update_functions_flags(self, flags):

        for function_name, box in self.main_function_widgets.items():
            if hasattr(box, "update_flag_defaults"):
                box.update_flag_defaults(flags)

    @pyqtSlot(str, name="load yml flags")
    def load_yml_flags(self, yml_filename):

        self.write_status(f"[working] Reading flags from {yml_filename}")

        try:
            yml_flags = read_check_yml_file(yml_filename, dict)
        except (yaml.YAMLError, AssertionError) as e:
            QMessageBox.critical(self, f"Error parsing YML file!",
                                 f"An error was encountered while parsing {yml_filename}. "
                                 f"Please check its validity.")
            return 0

        # the first time data is loaded via YML file and measurement list files, have fresh flags
        if self.yml_file is None:
            self.init_flags()

        self.yml_file = yml_filename
        # STG_MotherOfAllFolders must be set before STG* flags so that they are properly interpreted
        self.check_update_flags_and_gui({"STG_MotherOfAllFolders": str(pl.Path(yml_filename).parent)})

        # remove to avoid double, possible wrong initialization of this flag
        if "STG_MotherOfAllFolders" in yml_flags:
            del yml_flags["STG_MotherOfAllFolders"]

        self.write_status(f"[success] Reading flags from {yml_filename}")

        self.write_status(f"[working] Initializing flags from {yml_filename}")

        if self.check_update_flags_and_gui(yml_flags):

            # enable all actions
            self.enable_disable_functions(
                enable=True, main_functions=["load_lst", "select row from new vws log file"])

            self.write_status(f"[success] Initializing flags from {yml_filename}")

        else:
            self.write_status(f"[failure] Initializing flags from {yml_filename}")

        self.check_update_flags_and_gui({"VIEW_batchmode": False})
        self.flags.initialize_compound_flags_with_defaults()

        # reset label
        self.current_measurement_label.setText("None selected yet")
        # disable these two functions until a measurement has been loaded from a list
        self.enable_disable_functions(
            enable=False, main_functions=(
                "select row from current list", "quick load from current list",
                "select row from current vws log file"
            )
        )

    @pyqtSlot(name="go to wiki")
    def go_to_wiki(self):
        QDesktopServices.openUrl(QUrl("https://github.com/galizia-lab/pyview/wiki"))


    @pyqtSlot(name="write yml file")
    def write_yml_file(self):

        filename, filters = QFileDialog.getSaveFileName(caption="Select a YML file for saving flags",
                                                        filter="YML File(*.yml)",
                                                        directory=self.get_default_directory(),
                                                        parent=self)

        self.write_status(f"[working] Writing flags to {filename}")
        try:
            self.flags.write_flags_to_yml(filename)
            self.write_status(f"[success] Writing flags to {filename}")
            return
        except Exception as e:

            QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", str(e))

    def get_selected_data_p1(self):

        data_label = self.data_manager.get_selected_data_label()
        return self.p1s[data_label]

    @pyqtSlot(dict, FlagsManager)
    def direct_load_finalize(self, label_p1_mapping, flags_used):

        for label, p1 in label_p1_mapping.items():
            revised_label = self.data_manager.add_data(flags_used, p1, label)
            self.p1s[revised_label] = p1

        self.flags = flags_used
        self.yml_file = None

        self.enable_disable_functions(enable=True, main_functions=["generate_overview"],
                                      misc_functions=self.misc_function_buttons.keys())

    @pyqtSlot(name="launch lst file window")
    def load_from_new_list(self):

        self.load_measurement_window = LoadMeasurementsFromListWindow(
            self.flags["LE_loadExp"], default_directory_path=self.flags["STG_OdorInfoPath"])
        self.load_measurement_window.send_data_signal.connect(self.load_lst_data)
        self.load_measurement_window.show()

        self.write_status("Waiting for selection of measurement from 'Load Measurement' window")

    @pyqtSlot(name="launch vws log file window")
    def load_from_new_vws_log(self):

        data_path = self.flags.get_raw_data_dir_str()
        if not pl.Path(data_path).is_dir():
            data_path = str(pl.Path.home())

        self.load_measurement_window = LoadMeasurementsFromVWSLogWindow(
            self.flags["LE_loadExp"],
            default_directory_path=data_path)
        self.load_measurement_window.send_data_signal.connect(self.load_lst_data)
        self.load_measurement_window.show()

        self.write_status("Waiting for selection of measurement from 'Load Measurement' window")

    @pyqtSlot(MeasurementList, list, name="load lst data")
    def load_lst_data(self, measurement_list, selected_measus):

        self.measurement_list = measurement_list
        lst_or_log_filepath = pl.Path(measurement_list.last_measurement_list_fle)

        # in case of log load, self.measurement_list is not loaded from a list file, but initialized directly from a
        # log file. The value "lst_filename" above points to the VWS.LOG file.
        # During log load, flags may not have been initialized from a YML file. So, I am making sure here,
        # that the flag "STG_Datapath" is set so that data can be correctly loaded
        temp_dir = pl.Path(lst_or_log_filepath).parent / "temp_dir_for_view_analyses"
        flags_to_update = {}
        if lst_or_log_filepath.suffixes == [".vws", ".log"]:
            for flag in self.flags.compound_path_flags:
                try:
                    if not pl.Path(self.flags[flag]).is_dir():
                        temp_dir.mkdir(exist_ok=True)
                        flags_to_update[flag] = str(temp_dir)
                except KeyError as ke:
                    temp_dir.mkdir(exist_ok=True)
                    flags_to_update[flag] = str(temp_dir)

            flags_to_update["STG_Datapath"] = pl.Path(lst_or_log_filepath).parent
            flags_to_update["STG_OdorInfoPath"] = str(temp_dir.parent)
        else:
            flags_to_update = {"STG_OdorInfoPath": str(measurement_list.get_STG_OdorInfoPath())}

        for k, v in flags_to_update.items():
            self.flag_update_request_gui(k, v)

        for measu in selected_measus:
            self.write_status(f"[working] Loading meta data for measu={measu} from {lst_or_log_filepath}.")

            try:
                p1_metadata, extra_metadata = measurement_list.get_p1_metadata_by_measu(measu)
            except AssertionError as ase:
                QMessageBox.critical(self, "Problem getting measurement metadata", str(ase))
                self.write_status(f"Problem getting measurement metadata")
                self.write_status(f"[failure] Loading meta data for measu={measu} from {lst_or_log_filepath}.")
                return

            self.write_status(f"[success] Loading meta data for measu={measu} from {lst_or_log_filepath}.")

            if not self.check_update_flags_and_gui({"STG_Measu": measu,
                                                    "STG_ReportTag": measurement_list.get_STG_ReportTag()
                                                    }):
                return

            self.write_status(f"[success] Loading meta data for measu={measu} from {lst_or_log_filepath}.")

            self.write_status(f"[working] Loading raw data for measu={measu} from {lst_or_log_filepath} with "
                              f"LE_loadExp={self.flags['LE_loadExp']}.")

            try:
                p1 = get_p1(p1_metadata=p1_metadata, flags=self.flags, extra_metadata=extra_metadata)
            except FileNotFoundError as fnfe:
                QMessageBox.critical(self, "File Not Found", str(fnfe))
                self.write_status(f"[failure] Loading measurement data for measu={measu} from {lst_or_log_filepath}.")
                return

            self.write_status(f"[success] Loading raw data for measu={measu} from {lst_or_log_filepath} with "
                              f"LE_loadExp={self.flags['LE_loadExp']}.")

            self.write_status(f"[working] Calculating signal for measu={measu} from {lst_or_log_filepath} with "
                              f"LE_CalcMethod={self.flags['LE_CalcMethod']}.")

            p1.calculate_signals(self.flags)

            self.write_status(f"[success] Calculating signal for measu={measu} from {lst_or_log_filepath} with "
                              f"LE_CalcMethod={self.flags['LE_CalcMethod']}.")

            label = self.flags.get_measurement_label(measurement_row=self.measurement_list.get_row_by_measu(measu))
            revised_label = self.data_manager.add_data(self.flags, p1, label)
            self.p1s[revised_label] = p1

        # update label indicating selected list file
        self.current_measurement_label.setText(str(lst_or_log_filepath))

        # enable all functions
        self.enable_disable_functions_all(enable=True)

    @pyqtSlot(str, dict, name="reload from last lst file")
    def quick_load_from_current_lst(self, button_name, flags):

        if not self.check_update_flags_and_gui(flags):
            return

        if self.measurement_list is None:
            QMessageBox.critical(
                self, "Error finding measurement",
                "A measurement from an LST/settings file has not yet been loaded. "
                "Please load a measurement from an LST/settings file first using the function "
                "'Load measurement from LST/settings file' above")

        measus = self.measurement_list.get_measus()
        measu_user_input = self.flags["STG_Measu"]
        if measu_user_input not in measus:
            QMessageBox.critical(
                self,
                "Measu not found!",
                f"Measu={measu_user_input} is not present in the current measurement list file"
                f"{self.measurement_list.last_measurement_list_fle}")
        try:
            self.load_lst_data(self.measurement_list,
                               [measu_user_input])
            return
        except Exception as e:

            QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", str(e))

    @pyqtSlot(name="choose from current list")
    def choose_row_from_current_list(self):

        if self.measurement_list is None:
            QMessageBox.critical(self, "Error finding measurement",
                                 "A measurement from an LST/settings file has not yet been loaded. "
                                 "Please load a measurement from an LST/settings file first using the function "
                                 "'Load measurement from LST/settings file' above")
        try:
            self.load_measurement_window = LoadMeasurementsFromListWindow(
                self.flags["LE_loadExp"],
                default_directory_path=self.flags["STG_OdorInfoPath"],
                measurement_list=self.measurement_list)
            self.load_measurement_window.lst_file_selector.set_entry(self.measurement_list.last_measurement_list_fle)
            self.load_measurement_window.refresh_display()
            self.load_measurement_window.send_data_signal.connect(self.load_lst_data)
            self.load_measurement_window.show()
            self.write_status("Waiting for selection of measurement from 'Load Measurement' window")
        except Exception as e:

            QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", str(e))

    @pyqtSlot(name="choose from current vws log")
    def choose_row_from_current_vws_log(self):

        if self.measurement_list is None:
            QMessageBox.critical(self, "Error finding measurement",
                                 "A measurement from a VWS.LOG file has not yet been loaded. "
                                 "Please load a measurement from an VWS.LOG file first using the function "
                                 "'Load measurement from VWS.LOG file' above")
        try:
            self.load_measurement_window = LoadMeasurementsFromVWSLogWindow(
                self.flags["LE_loadExp"],
                # does not matter, as value is set in the next command
                default_directory_path=self.flags.get_raw_data_dir_str(),
                measurement_list=self.measurement_list)
            self.load_measurement_window.lst_file_selector.set_entry(self.measurement_list.last_measurement_list_fle)
            self.load_measurement_window.refresh_display()
            self.load_measurement_window.send_data_signal.connect(self.load_lst_data)
            self.load_measurement_window.show()
            self.write_status("Waiting for selection of measurement from 'Load Measurement' window")
        except Exception as e:

            QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", str(e))

    def get_default_directory(self):

        settings = get_view_qsettings_manager()
        current_file_list = settings.value("yml_file_list", type=list)
        if self.yml_file is not None:
            return str(pl.Path(self.yml_file).parent)
        elif len(current_file_list):
            return str(pl.Path(current_file_list[-1]).parent)
        else:
            return os.path.expanduser("~")

    def remove_data(self, label):

        self.reset_iltis_signal.emit()
        del self.p1s[label]
        gc.collect()

    @pyqtSlot(str, dict, bool, bool, name="generate overview")
    def generate_overview(self, button_name, flags, use_all_features, use_all_stimuli):

        if not self.check_update_flags_and_gui(flags):
            return

        self.write_status("[working] Generating overview")

        if button_name == "Generate(new)":

            try:
                pop_show_overview(flags=self.flags, p1=self.get_selected_data_p1(),
                                  label=self.data_manager.get_selected_data_label(),
                                  stimulus_number="all" if use_all_stimuli else None,
                                  feature_number="all" if use_all_features else None)
                self.write_status("[success] Generating overview")
                return
            except NotImplementedError as nie:
                QMessageBox.critical(self, "Not implemented Error",
                                     "Oops, the feature you requested is either invalid or not implemented."
                                     f"\n------\nHere is the full error message:\n{traceback.format_exc()}")

            except Exception as e:
                QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", traceback.format_exc())

        # elif   # left here in case we need to add new buttons
        # remember to write a "[success]...." status and return after successful function call

        self.write_status("[failure] Generating overview")

    def save_movie(self):

        self.write_status("[working] Saving movie")

        ExportMovie(self.flags.to_series(), self.get_selected_data_p1())

        self.write_status("[success] Saving movie")

    def save_movie_new(self):

        self.write_status("[working] Save movie with new method")

        selected_data_label = self.data_manager.get_selected_data_label()
        selected_p1 = self.get_selected_data_p1()

        op_path = pl.Path(self.flags["STG_OdorReportPath"])

        if not op_path.is_dir():
            op_path = pl.Path(get_system_temp_dir())

        op_name_without_extension = op_path / f"{selected_data_label}(manually created)"

        try:

            self.write_status(f"[working] Save movie with new method to {str(op_name_without_extension)}")
            op_name_with_extension = export_movie(p1=selected_p1, flags=self.flags,
                                                  full_filename_without_extension=str(op_name_without_extension))
            QMessageBox.information(self, "Movie saved successfully", f"Output file: {op_name_with_extension}")

            self.write_status(f"[success] Save movie with new method to {str(op_name_with_extension)}")
            return
        except Exception as e:

            exception_formatted = traceback.format_exception(*sys.exc_info())
            QMessageBox.critical(self, f"VIEW encountered an error!", "".join(exception_formatted))

        self.write_status(f"[failure] Save movie with new method")

    def show_foto1(self):

        self.write_status("[working] Show foto1")
        try:
            foto1_data = get_foto1_data(flags=self.flags, p1=self.get_selected_data_p1())
            show_photo(foto1_data)
            self.write_status("[success] Show foto1")
            return
        except Exception as e:

            QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", traceback.format_exc())

        self.write_status("[failure] Show foto1")

    def viz_gdm_traces(self):

        self.write_status("[working] Initializing GDM visualization window")
        try:
            self.gdm_viz_window = GDMViz(p1=self.get_selected_data_p1(), flags=self.flags)
            self.gdm_viz_window.show()
            self.write_status("[success] Initializing GDM visualization window")
            return
        except Exception as e:

            QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", traceback.format_exc())

        self.write_status("[failure] Initializing GDM visualization window")

    def button3_func(self):

        self.write_status("[working] button 3")

        # TODO: Clicking the button "button 3" bring the program here.

        # # --- implementation template ---
        # try:
        #     pass  # VIEW will try to run this code on button press
        #     self.write_status("[success] <add function description>")
        #     return
        # except Exception as e:
        #
        #     QMessageBox.critical(self, f"VIEW encountered a {type(e).__name__}", traceback.format_exc())
        # self.write_status("[success] <add function description>")
        #
        # # ------

        # ---  place holder code, remove after implementation ---
        frameinfo = getframeinfo(currentframe())
        QMessageBox.information(self, "Not implemented yet!", f"To implement this function, add code "
                                                              f"in file {frameinfo.filename} "
                                                              f"at line {frameinfo.lineno}")
        # ------
