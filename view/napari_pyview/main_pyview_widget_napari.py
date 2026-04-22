from typing import TYPE_CHECKING

from view.gui.flags_box import FlagsMainWidget
from view.gui.setup_calcmethod_choice import SetupChoice
from view.napari_pyview.napari_utils.layer_utils import add_roi_datas_to_napari
from view.python_core.flags import FlagsManager

if TYPE_CHECKING:
    import napari

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import rgb2hex
from qtpy.QtCore import Signal
from qtpy.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from view.gui.central_widget import CentralWidget
from view.gui.data_manager import DataManager
from view.gui.direct_load import DirectDataLoader
from view.gui.loader_widgets import ListLoadWidget, LogLoadWidget
from view.gui.logger import LoggerGroupBox
from view.gui.main_function_widgets import (
    MainFunctionAbstract,
    OverviewGenWidget,
)
from view.napari_pyview.iltis_window_napari import ILTISWindowNapari
from view.python_core.rois.roi_io import get_roi_io_class
from view.python_core.utils.colors import interpret_flag_SO_MV_colortable


class NapariPyViewWidget(CentralWidget):
    export_data_to_iltis_signal = Signal(
        list, list, pd.DataFrame, int, tuple, tuple, int, name="export data"
    )
    reset_iltis_signal = Signal(name="reset ILTIS")

    def __init__(
        self, napari_viewer: "napari.viewer.Viewer" = None, parent=None
    ):
        super().__init__(parent)
        # among others, calls init_ui(), initializes Flags, self.p1s, self.measurement_list, etc

        self.napari_viewer = napari_viewer
        self.iltis_window = None

    def init_ui(self):
        # Create a single VBox layout for the main widget

        contents_widget = QWidget(self)
        contents_vbox = QVBoxLayout(contents_widget)

        # --------------------------------------------------------------------------------------------------------------
        # Instantiate setup choice box for LE_loadExp
        self.setup_choice_box = SetupChoice()
        self.setup_choice_box.update_LE_loadExp_flag_signal.connect(
            self.flag_update_request_gui
        )
        self.main_function_widgets["setup choice box"] = self.setup_choice_box
        contents_vbox.addWidget(self.setup_choice_box)

        # --------------------------------------------------------------------------------------------------------------
        # Instantiate the calcMethod_box for LE_calcMethod, button for closing all matplotlib figures in one shot.
        temp_hbox = QHBoxLayout()
        calcMethod_flags = ["LE_CalcMethod"]
        self.calcMethod_box = MainFunctionAbstract(
            button_names={},
            flag_names=calcMethod_flags,
            flag_defaults=[self.flags[f] for f in calcMethod_flags],
            group_name="Choose the method for calculating signals\n",
            # "(does not affect raw data loading and artifact correction)"
        )
        self.calcMethod_box.flag_update_signal.connect(
            self.flag_update_request_gui
        )
        self.main_function_widgets["calc method choice box"] = (
            self.calcMethod_box
        )
        temp_hbox.addWidget(self.calcMethod_box)

        button = QPushButton("Close all\nmatplotlib figures")
        button.clicked.connect(self.close_all_matplotlib_figures)

        temp_hbox.addWidget(button)

        contents_vbox.addLayout(temp_hbox)

        # --------------------------------------------------------------------------------------------------------------
        # Instantiate loader_tabs
        loader_tabs = QTabWidget(self)
        contents_vbox.addWidget(loader_tabs)

        direct_loader = DirectDataLoader(
            self, self.setup_choice_box.get_current_LE_loadExp()
        )
        direct_loader.data_loaded_signal.connect(self.direct_load_finalize)
        self.setup_choice_box.return_LE_loadExp.connect(
            direct_loader.refresh_layout
        )
        loader_tabs.addTab(
            direct_loader, "Direct load from raw file (no pre-requirements)"
        )

        log_load_widget = LogLoadWidget(self)
        log_load_widget.new_vws_log_load.clicked.connect(
            self.load_from_new_vws_log
        )
        log_load_widget.choose_from_current_vws_log.clicked.connect(
            self.choose_row_from_current_vws_log
        )
        loader_tabs.addTab(
            log_load_widget, "Direct load from log file (no pre-requirements)"
        )

        list_load_widget = ListLoadWidget(self, self.flags.flags)
        list_load_widget.new_load.clicked.connect(self.load_from_new_list)
        list_load_widget.choose_from_current_list.clicked.connect(
            self.choose_row_from_current_list
        )
        list_load_widget.new_vws_log_load.clicked.connect(
            self.load_from_new_vws_log
        )
        list_load_widget.choose_from_current_vws_log.clicked.connect(
            self.choose_row_from_current_vws_log
        )
        list_load_widget.yaml_loader.return_filename_signal.connect(
            self.load_yml_flags
        )
        list_load_widget.quick_load_from_current_lst_box.send_data.connect(
            self.quick_load_from_current_lst
        )
        list_load_widget.quick_load_from_current_lst_box.flag_update_signal.connect(
            self.flag_update_request_gui
        )
        self.main_function_widgets["load_lst"] = list_load_widget.new_load
        self.main_function_widgets["select row from current list"] = (
            list_load_widget.choose_from_current_list
        )
        self.main_function_widgets["select row from new vws log file"] = (
            list_load_widget.new_vws_log_load
        )
        self.main_function_widgets["select row from current vws log file"] = (
            list_load_widget.choose_from_current_vws_log
        )
        self.main_function_widgets["quick load from current list"] = (
            list_load_widget.quick_load_from_current_lst_box
        )
        self.main_function_widgets["selected list file"] = (
            list_load_widget.selected_list_file_box
        )
        self.current_measurement_label = (
            list_load_widget.current_measurement_label
        )
        loader_tabs.addTab(
            list_load_widget,
            "List load (pre-requirements: YML File, folder structure, "
            "measurement list files)",
        )

        # --------------------------------------------------------------------------------------------------------------
        # Instantiate data_manager_group_box
        data_manager_group_box = QGroupBox("Data Manager", self)
        data_manager_vbox = QVBoxLayout(data_manager_group_box)

        flags_values2use = [
            "LE_loadExp",
            "LE_CalcMethod",
            "STG_ReportTag",
            "STG_Measu",
        ] + self.flags.compound_path_flags

        def temp(x):
            return lambda p1: p1.metadata.get(x, "N/A")

        flags_values2use_dict = {k: k for k in flags_values2use}
        p1_values2use = {
            "Component\nOdors": temp("odor"),
            "Stimulus": temp("stimulus"),
            "Stimulus\nConcentration": temp("odor_nr"),
            "No. of pulses in stimuli": lambda p1: p1.metadata[
                "pulsed_stimuli_handler"
            ].stimulus_frame.shape[0],
            "Stimulus pulse start times\nrelative to imaging start (s)": lambda p1: [
                x / pd.Timedelta(seconds=1)
                for x in p1.metadata[
                    "pulsed_stimuli_handler"
                ].get_pulse_start_times()
            ],
            "Stimulus pulse end times\nrelative to imaging start (s)": lambda p1: [
                x / pd.Timedelta(seconds=1)
                for x in p1.metadata[
                    "pulsed_stimuli_handler"
                ].get_pulse_end_times()
            ],
            "Measurement\nLabel": temp("ex_name"),
            "Raw File Name": temp("full_raw_data_path_str"),
            "No. of frames": temp("frames"),
            "Frames per second": lambda p1: p1.metadata.frequency,
            "No. of Pixels along X": temp("format_x"),
            "No. of Pixels along Y": temp("format_y"),
        }

        # --------------------------------------------------------------------------------------------------------------
        # Instantiate Data Manager
        self.data_manager = DataManager(
            parent=None,
            flag_values_to_use=flags_values2use_dict,
            p1_values_to_use=p1_values2use,
            label_joiner="_",
            default_label_cols=["STG_Measu", "STG_ReportTag"],
            precedence_order=[
                "STG_ReportTag",
                "STG_Measu",
                "Measurement\nLabel",
                "Stimulus",
                "Stimulus\nConcentration",
                "Component\nOdors",
                "No. of pulses in stimuli",
                "Stimulus pulse start times\nrelative to imaging start (s)",
                "Stimulus pulse end times\nrelative to imaging start (s)",
                "No. of frames",
                "Frames per second",
                "No. of Pixels along X",
                "No. of Pixels along Y",
                "LE_loadExp",
                "LE_CalcMethod",
            ],
        )

        # set height of data manager table to be a multiple of header height (multiple determined heuristically)
        header_height = self.data_manager.ui_table.horizontalHeader().height()
        self.data_manager.ui_table.setFixedHeight(header_height * 10)

        self.data_manager.remove_data_signal.connect(self.remove_data)
        data_manager_vbox.addWidget(self.data_manager.ui_table)

        contents_vbox.addWidget(data_manager_group_box)

        # --------------------------------------------------------------------------------------------------------------
        # Instantiate log_pte
        self.log_pte = LoggerGroupBox()
        contents_vbox.addWidget(self.log_pte)

        # --------------------------------------------------------------------------------------------------------------
        # ILTIS related
        iltis_functions_widget = QGroupBox("ILTIS-Related Functions", self)
        iltis_functions_vbox = QVBoxLayout(iltis_functions_widget)
        open_button = QPushButton("Open ILTIS and\nlaunch transfer dialog")
        open_button.clicked.connect(self.open_iltis_launch_transfer_dialog)
        iltis_functions_vbox.addWidget(open_button)

        self.iltis_close_button = QPushButton(
            "Close ILTIS and\ndelete all data"
        )
        iltis_functions_vbox.addWidget(self.iltis_close_button)

        contents_vbox.addWidget(iltis_functions_widget)
        self.main_function_widgets["ILTIS functions"] = iltis_functions_widget

        # --------------------------------------------------------------------------------------------------------------

        # Napari Related
        napari_functions_widget = QGroupBox("Napari-Related Functions", self)
        napari_functions_vbox = QVBoxLayout(napari_functions_widget)

        transfer_data_button = QPushButton("Transfer data to Napari")
        transfer_data_button.clicked.connect(
            self.spawn_dialog_napari_data_transfer
        )
        napari_functions_vbox.addWidget(transfer_data_button)

        load_rois_button = QPushButton("Load ROIs and add to Napari")
        load_rois_button.clicked.connect(self.load_rois_and_add_to_napari)
        napari_functions_vbox.addWidget(load_rois_button)

        contents_vbox.addWidget(napari_functions_widget)
        self.main_function_widgets["Napari functions"] = (
            napari_functions_widget
        )

        # --------------------------------------------------------------------------------------------------------------
        self.flags_widget = FlagsMainWidget(flags=self.flags)

        for (
            _subgroup_name,
            subgroup_page,
        ) in self.flags_widget.flag_display_choice.subgroup_pages.items():
            subgroup_page.return_flag_signal.connect(
                self.flag_update_request_gui
            )

        self.flags_widget.wiki_link_button.clicked.connect(self.go_to_wiki)
        self.flags_widget.save_button.clicked.connect(self.write_yml_file)

        contents_vbox.addWidget(self.flags_widget)

        # --------------------------------------------------------------------------------------------------------------

        gen_overviews_box = OverviewGenWidget(
            parent=contents_widget, current_flags=self.flags
        )
        gen_overviews_box.send_data.connect(self.generate_overview)
        gen_overviews_box.flag_update_signal.connect(
            self.flag_update_request_gui
        )

        self.main_function_widgets["generate_overview"] = gen_overviews_box
        contents_vbox.addWidget(gen_overviews_box)

        gdm_viz_box_flags = ["RM_ROITrace"]
        gdm_viz_box = MainFunctionAbstract(
            parent=contents_widget,
            button_names=["Visualize GDM traces"],
            flag_names=gdm_viz_box_flags,
            flag_defaults=[self.flags[f] for f in gdm_viz_box_flags],
            group_name="Visualize GDM traces",
            stack_vertically=True,
        )
        gdm_viz_box.send_data.connect(self.viz_gdm_traces)
        gdm_viz_box.flag_update_signal.connect(self.flag_update_request_gui)
        self.main_function_widgets["viz_gdm"] = gdm_viz_box
        contents_vbox.addWidget(gdm_viz_box)

        # --------------------------------------------------------------------------------------------------------------
        misc_functions = QGroupBox("Miscellaneous functions", self)
        misc_functions_vbox = QVBoxLayout(misc_functions)
        save_button = QPushButton("Save movie (legacy)")
        save_button.clicked.connect(self.save_movie)
        misc_functions_vbox.addWidget(save_button)
        self.misc_function_buttons["save_movie"] = save_button

        save_movie_new = QPushButton("Save Movie (new)")
        save_movie_new.clicked.connect(self.save_movie_new)
        misc_functions_vbox.addWidget(save_movie_new)
        self.misc_function_buttons["save_movie_new"] = save_movie_new

        button2 = QPushButton("Show foto1")
        button2.clicked.connect(self.show_foto1)
        misc_functions_vbox.addWidget(button2)
        self.misc_function_buttons["show_foto1"] = button2

        button3 = QPushButton("Button3")
        button3.clicked.connect(self.button3_func)
        misc_functions_vbox.addWidget(button3)
        self.misc_function_buttons["button3"] = button3

        contents_vbox.addWidget(misc_functions)

        # --------------------------------------------------------------------------------------------------------------

        scroll_area = QScrollArea()
        scroll_area.setWidget(contents_widget)
        scroll_area.setWidgetResizable(
            True
        )  # Critical for scrollbars to appear

        main_vbox = QVBoxLayout(self)
        main_vbox.addWidget(scroll_area)

        # --------------------------------------------------------------------------------------------------------------

        # Disable all actions other than YML loader
        self.enable_disable_functions_all(
            enable=False,
            main_exceptions=[
                "yml loader",
                "setup choice box",
                "calc method choice box",
            ],
        )

    def write_status(self, msg):

        # TODO set status message in napari

        self.log_info(msg)

    def open_iltis_launch_transfer_dialog(self):

        self.iltis_window = ILTISWindowNapari(self)
        self.iltis_window.show()
        self.iltis_window.iltis_main_shell.import_action.triggered.connect(
            self.spawn_export_dialog
        )
        self.iltis_window.iltis_main_shell.import_action_quick.triggered.connect(
            self.export_data_to_iltis_all
        )
        self.export_data_to_iltis_signal.connect(
            self.iltis_window.iltis_main_shell.import_data
        )
        self.reset_iltis_signal.connect(
            self.iltis_window.iltis_main_shell.reset
        )
        self.iltis_close_button.clicked.connect(self.iltis_window.close)

        self.iltis_window.iltis_main_shell.import_action.trigger()

    def spawn_dialog_napari_data_transfer(self):

        transfer_dialog = self.spawn_export_dialog()
        if transfer_dialog is not None:
            transfer_dialog.send_data_signal.connect(
                self.export_data_to_napari
            )
            transfer_dialog.setWindowTitle("Import Data to Napari")

    def export_data_to_napari(self, indices, metadata_list_for_label):

        if self.napari_viewer is None:
            QMessageBox.critical(
                self,
                "Napari not found!",
                "The plugin was started without a napari viewer."
                " Please start the plugin from within napari.",
            )

        (
            metadata_to_send,
            raw_data_list,
            signals_list,
            n_frames_list,
            stim_onset,
            stim_offset,
        ) = self.get_data_for_iltis_export(indices, metadata_list_for_label)

        for path_flag in self.flags.compound_path_flags:
            if path_flag not in self.flags.compound_path_flags_with_defaults:
                metadata_to_send[path_flag] = self.flags[path_flag]

        for ind, raw_data in enumerate(raw_data_list):
            # convert from format XYT to TXY
            raw_data_TYX = raw_data.swapaxes(0, 2)

            # flip Y axis to match napari convention
            raw_data_TYX_Y_flipped = np.flip(raw_data_TYX, axis=1)

            metadata_row = metadata_to_send.iloc[ind]
            name = metadata_row["Label to use"]
            self.napari_viewer.add_image(
                data=raw_data_TYX_Y_flipped,
                name=name,
                metadata=metadata_row.to_dict(),
            )

    def load_rois_and_add_to_napari(self):
        """
        Load ROIs from file based on RM_ROITrace flag and add them to Napari as shapes.
        """
        if self.napari_viewer is None:
            QMessageBox.critical(
                self,
                "Napari not found!",
                "The plugin was started without a napari viewer."
                " Please start the plugin from within napari.",
            )
            return

        # Get the current measurement label from the data manager
        current_measurement_label = self.current_measurement_label.text()
        if not current_measurement_label:
            QMessageBox.warning(
                self,
                "No measurement selected",
                "Please select a measurement first.",
            )
            return

        # Get ROI IO class based on RM_ROITrace flag
        roi_io_class = get_roi_io_class(RM_ROITrace=self.flags["RM_ROITrace"])

        # Load ROI data
        roi_data_dict, roi_file = roi_io_class.read(
            self.flags, current_measurement_label
        )

        # Get edge color from SO_fgColor flag
        _, _, edge_color = interpret_flag_SO_MV_colortable(
            self.flags["SO_MV_colortable"],
            bg_color=self.flags["SO_bgColor"],
            fg_color=self.flags["SO_fgColor"],
        )

        # Convert matplotlib color to hex format
        edge_color_napari = rgb2hex(edge_color[:3])

        # Use the converter to add ROIs to napari with custom parameters
        selected_p1_metadata = self.get_selected_data_p1().metadata
        add_roi_datas_to_napari(
            self.napari_viewer,
            roi_data_dict,
            frame_size=(
                selected_p1_metadata.format_y,
                selected_p1_metadata.format_x,
            ),
            edge_color=edge_color_napari,
            edge_width=1,
        )

        self.log_info(
            f"Successfully loaded {len(roi_data_dict)} ROIs from {roi_file}"
        )

    def direct_load_finalize(
        self, label_p1_mapping: dict, flags_used: FlagsManager
    ):

        super().direct_load_finalize(label_p1_mapping, flags_used)
        self.enable_disable_functions(
            enable=True, main_functions=("ILTIS functions", "Napari functions")
        )

    def closeEvent(self, event=None):

        plt.close("all")
        event.accept()
