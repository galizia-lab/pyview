import copy
from iltis.Main import Main as ILTISMain
from iltis.io.IOtools import save_tstack
from iltis.Objects.Data_Object import Data_Object, Metadata_Object
from iltis.Widgets.Options_Control_Widget import SingleValueWidget
from iltis.Objects.ROIs_Object import myPolyLineROI, myCircleROI
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QMessageBox
import numpy as np
import pandas as pd
from .save_area_file_dialog import SaveAreaFileDialog, SaveCircleROIsFileDialog, SaveAllROIsFileDialog
from .orphan_functions import convert_iltisROI2VIEWROI
from view.python_core.rois.roi_io import ILTISTextROIFileIO
import logging
import pathlib as pl


class ILTISMainShell(ILTISMain):

    def __init__(self, verbose=False):

        super().__init__(verbose)

        menu_bar = self.MainWindow.menuBar()

        # otherwise, Qt will try to integrate into the native menubar on MAC, which causes issues
        menu_bar.setNativeMenuBar(False)

        view_menu = menu_bar.addMenu("&VIEW-Related")

        self.import_action_quick = view_menu.addAction("Quickly import all data from VIEW")

        self.import_action = view_menu.addAction("Selectively import data from VIEW")

        self.save_cirle_rois_action = view_menu.addAction("Save circle ROIS as .roi for VIEW")
        self.save_cirle_rois_action.triggered.connect(self.spawn_save_circle_rois_dialog)
        self.save_cirle_rois_action.setEnabled(False)

        self.save_rois_action = view_menu.addAction("Save all ROI types as .roi for VIEW")
        self.save_rois_action.triggered.connect(self.spawn_save_all_rois_dialog)
        self.save_rois_action.setEnabled(False)

        self.save_area_action = view_menu.addAction("Save Polygon ROIs as AREA for VIEW")
        self.save_area_action.triggered.connect(self.spawn_save_area_dialog)
        self.save_area_action.setEnabled(False)

        self.quick_save_area_action = view_menu.addAction("Quick save AREA for VIEW (using selected data and ROIs)")
        self.quick_save_area_action.triggered.connect(self.quick_save_area)
        self.quick_save_area_action.setEnabled(False)

        self.dialogs = []

        self.metadata = None

    # this is used to reset ILTIs from VIEW if required
    @pyqtSlot(name="reset")
    def reset(self, restore_options=True):

        # save some options for restoration
        # some options in the tab "Preprocessing" change the data, hence are not saved and restored
        # when loading new data
        roi_options_to_save = ["view", "ROI", "export"]

        try:
            roi_options = {x: copy.copy(getattr(self.Options, x)) for x in roi_options_to_save}
        # if the Options object is initialized but default options have not yet been loaded
        except AttributeError as ae:
            roi_options = {}

        # clear ILTIS data and history
        self.ROIs.reset()
        self.Signals.resetSignal.emit()
        self.Options.__init__(self)

        if restore_options:
            # restore options; placed here because (1) load_default_options() uses Data.nFrames and Metadata.paths
            # (2) since load_default_options() need to be called before initing Option_Control (see below)
            [setattr(self.Options, k, v) for k, v in roi_options.items()]
            try:
                self.MainWindow.roi_type_widget.layout().itemAt(1).widget().set_value(roi_options["ROI"]["type"])
            except KeyError as ke:
                pass

        # parts of iltis.Objects.IO_Object.IO_Object.load_data

        # Data object creation
        self.Data = Data_Object()
        self.Data.Metadata = Metadata_Object(self.Data)

        self.metadata = None

        self.MainWindow.ToolBar.setEnabled(False)

        # disable some actions from menubar
        self.save_cirle_rois_action.setEnabled(False)
        self.save_rois_action.setEnabled(False)
        self.save_area_action.setEnabled(False)
        self.quick_save_area_action.setEnabled(False)

        self.MainWindow.roi_type_widget.setEnabled(False)

        return roi_options

    @pyqtSlot(list, list, pd.DataFrame, int, tuple, tuple, int, name="import data")
    def import_data(self, raw_data_list, signal_list, metadata, n_frames, stim_onset, stim_offset, default_radius):
        """
        Writes raw data, (df/f) signal data and trials names into the data structures iltis.
        In principle replicates iltis.Objects.IO_Object.IO_Object.init_data for writing raw data
        and initializing assoicated UI. Then writes df/f signal and calls
        iltis.Widgets.MainWindow_Widget.MainWindow_Widget.toggle_dFF
        :param raw_data_list: iterable of numpy.ndarrays of dimension 3
        :param signal_list: iterable of numpy.ndarray of dimension 3, same size as raw_data_list
        :param metadata: pandas.Dataframe, indices are unique label for each measurement, columns are
        metadata, must have the columns "Label to use", the entries of which will be used as data labels in ILTIS.
        Columns must also contain flags of the subgroup "paths". Must contain a column "Raw Data File"
        which contains the full paths of the raw data files
        :param n_frames: int, maximium number of frames among all raw data in raw_data_list
        :param stim_onset: list, of stimulus onsets as frame numbers
        :param stim_offset: list, of stimulus offsets as frame numbers
        :param default_radius: int, default radius of ROIs
        """
        assert len(raw_data_list) == len(signal_list) == metadata.shape[0]
        assert "Label to use" in metadata.columns
        assert all(type(x) is np.ndarray for x in raw_data_list)
        assert all(len(x.shape) == 3 for x in raw_data_list)
        assert all(type(x) is np.ndarray for x in signal_list)
        assert all(len(x.shape) == 3 for x in signal_list)

        for raw_data, sig_data in zip(raw_data_list[1:], signal_list[1:]):

            if not (raw_data.shape == raw_data_list[0].shape == sig_data.shape == signal_list[0].shape):
                QMessageBox.critical(
                    self.MainWindow, "Error importing data",
                    "Data being imported have different sizes (X, Y and/or Z). Please have a look at the columns"
                    "'No. of pixels along X', 'No. of pixels along Y' and 'No. of frames' of the table shown "
                    "when choosing data for import"
                )
                return

        self.write_status("[working] Importing data from VIEW to ILTIS")

        old_roi_options = self.reset(restore_options=False)

        self.metadata = metadata

        n_trials = len(raw_data_list)

        # set raw data,
        # view.idl_translation_core.ViewLoadData.load_pst
        self.Data.raw = np.concatenate([x[:, :, :, np.newaxis] for x in raw_data_list], axis=3)

        # dFF needs to be a float to avoid problems with pyqtgraph, see Issue 56 of VIEW
        self.Data.dFF = np.zeros_like(self.Data.raw, dtype="float32")

        # set some metadata
        self.Data.Metadata.paths = metadata["Raw File Name"].values
        self.Data.nFrames = raw_data_list

        # set inferred data, in principle replicates iltis.Objects.Data_Object.Data_Object.infer
        self.Data.nTrials = n_trials
        self.Data.nFrames = n_frames

        # instead of file names, set trial labels directly
        self.Data.Metadata.trial_labels = metadata["Label to use"].values.tolist()

        # restore options; placed here because (1) load_default_options() uses Data.nFrames and Metadata.paths
        # (2) since load_default_options() need to be called before initing Option_Control (see below)
        self.Options.load_default_options()
        [setattr(self.Options, k, v) for k, v in old_roi_options.items() if len(v)]
        try:
            getattr(self.Options, "ROI")["diameter"] = 2 * default_radius + 1
            self.MainWindow.roi_type_widget.layout().itemAt(1).widget().set_value(old_roi_options["ROI"]["type"])
        except KeyError as ke:
            pass

        # set cwd to IDLOutput
        random_metadata = metadata.iloc[0]
        op_dir_first_dataset = random_metadata["STG_OdorReportPath"]
        self.cwd = op_dir_first_dataset
        self.Options.general['cwd'] = op_dir_first_dataset

        # set data_path and roi_path
        self.data_path = random_metadata["STG_Datapath"]
        self.roi_path = random_metadata["STG_OdormaskPath"]

        # set stimuli parameters
        self.add_stim_options(stim_onset, stim_offset)

        # initialize and update GUI elements
        self.MainWindow.Options_Control.init_UI()
        self.Signals.initDataSignal.emit()
        self.Signals.updateSignal.emit()

        # replace nans if any in signals with lowest value of signal
        for x in signal_list:
            x[np.isnan(x)] = np.nanmin(x)

        # set dFF
        self.Data.dFF = np.concatenate([x[:, :, :, np.newaxis] for x in signal_list], axis=3)
        self.Options.flags["dFF_was_calc"] = True

        # - for all display triggers, whatever the state, set it to True and toggle it.
        self.MainWindow.ToolBar.setEnabled(True)
        # -- list of tuples to store flag name and trigger
        flag_action_names = [
            ('show_dFF', 'toggledFFAction'),
            ('use_global_levels', 'toggleGlobalLevels'),
            ('show_avg', 'toggleAvgAction'),
            ('show_monochrome', 'toggleMonochromeAction')
        ]

        for flag_name, action_name in flag_action_names:
            self.Options.view[flag_name] = True
            action = getattr(self.MainWindow, action_name)
            action.setChecked(True)
            action.trigger()

        # reset levels of dFF signal once set
        self.Data_Display.LUT_Controlers.reset_levels(which="dFF")

        # enable all mouse based interactions in the Data_Display_Widget
        self.MainWindow.Data_Display.enable_interaction()

        # add a warning about signal calculation in ILTIS/transfer from VIEW
        qfont = QFont()
        qfont.setBold(True)
        qlabel = QLabel("Warning: The following options will only be used when data is loaded using Open->load data.\n"
                        "They are not used when data is imported from VIEW using VIEW-Related->Import data from VIEW.\n"
                        "In this case, deltaF/F is not calculated in ILTIS, but initialized with the signal data "
                        "calculated in VIEW.")
        qlabel.setFont(qfont)
        fake_field = SingleValueWidget(parent=self.MainWindow.Options_Control, dict_name="preprocessing",
                                       param_name="fake", dtype='S')
        fake_field.setText("Please take care!")
        fake_field.setReadOnly(True)
        self.MainWindow.Options_Control.widget(1).layout().insertRow(1, qlabel, fake_field)

        # enable other VIEW-related actions
        self.save_area_action.setEnabled(True)
        self.save_rois_action.setEnabled(True)
        self.save_cirle_rois_action.setEnabled(True)
        self.quick_save_area_action.setEnabled(True)
        self.MainWindow.roi_type_widget.setEnabled(True)

        # done, write status and return
        self.write_status("[success] Importing data from VIEW to ILTIS")

    def write_status(self, msg):

        self.MainWindow.statusBar().showMessage(msg)
        logging.info(msg)

    def add_stim_options(self, stim_onset, stim_offset):

        if len(stim_onset) != len(stim_offset) or len(stim_onset) == 0:
            return
        else:
            stim_onset_offsets = [x for x in zip(stim_onset, stim_offset) if x[0] is not None and x[1] is not None]
            stim_times = np.array(stim_onset_offsets, dtype=float)
            self.Options.preprocessing["nStimuli"] = len(stim_onset_offsets)
            self.Options.preprocessing["stimuli"] = stim_times

    def get_roi_and_selected_by_type(self, roi_types=None):

        if roi_types is None:
            roi_types = []

        roi_labels = []
        roi_labels_selected = []
        for roi in self.ROIs.ROI_list:
            if type(roi) in roi_types or roi_types == []:
                roi_labels.append(roi.label)
                if roi.active:
                    roi_labels_selected.append(roi.label)

        return roi_labels, roi_labels_selected

    def get_selected_data_labels(self):

        data_selector = self.MainWindow.Front_Control_Panel.Data_Selector
        selected_data_labels = [data_selector.item(x.row(), 0).text()
                                for x in data_selector.selectionModel().selectedRows()]
        return selected_data_labels

    @pyqtSlot(name="save circle roi_labels for VIEW")
    def spawn_save_circle_rois_dialog(self):

        circle_roi_labels, circle_roi_labels_selected = self.get_roi_and_selected_by_type([myCircleROI])
        selected_data_labels = self.get_selected_data_labels()
        save_circle_rois_dialog = SaveCircleROIsFileDialog(metadata=self.metadata, data_selected=selected_data_labels,
                                                           circle_roi_labels=circle_roi_labels,
                                                           circle_rois_selected=circle_roi_labels_selected)
        save_circle_rois_dialog.return_choices_signal.connect(self.save_coors_for_VIEW)
        self.dialogs.append(save_circle_rois_dialog)
        save_circle_rois_dialog.show()

    @pyqtSlot(name="save roi_labels for VIEW")
    def spawn_save_all_rois_dialog(self):

        roi_labels, roi_labels_selected = self.get_roi_and_selected_by_type([myCircleROI, myPolyLineROI])
        selected_data_labels = self.get_selected_data_labels()
        save_all_rois_dialog = SaveAllROIsFileDialog(metadata=self.metadata, data_selected=selected_data_labels,
                                                     roi_labels=roi_labels,
                                                     roi_labels_selected=roi_labels_selected)
        save_all_rois_dialog.return_choices_signal.connect(self.save_coors_for_VIEW)
        self.dialogs.append(save_all_rois_dialog)
        save_all_rois_dialog.show()

    @pyqtSlot(name="save area for VIEW")
    def spawn_save_area_dialog(self):

        poly_roi_labels, poly_roi_labels_selected = self.get_roi_and_selected_by_type([myPolyLineROI])

        selected_data_labels = self.get_selected_data_labels()
        save_area_dialog = SaveAreaFileDialog(metadata=self.metadata, data_selected=selected_data_labels,
                                              poly_roi_labels=poly_roi_labels,
                                              poly_rois_selected=poly_roi_labels_selected)
        save_area_dialog.return_choices_signal.connect(self.save_area_for_VIEW)
        self.dialogs.append(save_area_dialog)
        save_area_dialog.show()

    @pyqtSlot(list, str, name="save area for VIEW")
    def save_area_for_VIEW(self, roi_labels, filename):

        self.write_status("[working] Writing AREA file for VIEW")

        extraction_mask = np.zeros((self.Data.raw.shape[0],
                                    self.Data.raw.shape[1],
                                    len(roi_labels)), dtype='bool')

        rois_chosen = [x for x in self.ROIs.ROI_list if x.label in roi_labels and type(x) == myPolyLineROI]
        roi_data = []
        for i, ROI in enumerate(rois_chosen):
            if ROI.label in roi_labels:
                mask, inds = self.ROIs.get_ROI_mask(ROI)
                extraction_mask[mask, i] = 1
                roi_data.append(convert_iltisROI2VIEWROI(ROI))

        pl.Path(filename).parent.mkdir(exist_ok=True)
        ILTISTextROIFileIO.write(f"{filename}.roi", roi_data)
        save_tstack(extraction_mask, filename)

        QMessageBox.information(self.MainWindow, "AREA File saved!", f"to\n{filename}\nusing ROIs {roi_labels}")

        self.write_status("[success] Writing AREA file for VIEW")

    @pyqtSlot(list, str, name="save COORs for VIEW")
    def save_coors_for_VIEW(self, roi_labels, filename):

        self.write_status("[working] Writing COORs file for VIEW")

        rois_chosen = [x for x in self.ROIs.ROI_list if x.label in roi_labels]

        roi_datas = []
        for roi in rois_chosen:
            roi_data = convert_iltisROI2VIEWROI(roi)
            roi_datas.append(roi_data)

        ILTISTextROIFileIO.write(filename, roi_datas)

        QMessageBox.information(self.MainWindow, "Coor File saved!", f"to\n{filename}\nusing ROIs {roi_labels}")

        self.write_status("[success] Writing COORs file for VIEW")

    @pyqtSlot(name="quick save area")
    def quick_save_area(self):

        self.write_status("[working] Writing COORs file for VIEW")

        selected_data_labels = self.get_selected_data_labels()

        mask = self.metadata["Label to use"].apply(lambda x: x in selected_data_labels)
        metadata_selected_data = self.metadata.loc[mask, :]
        animals_deduplicated = metadata_selected_data['STG_ReportTag'].unique()
        if animals_deduplicated.shape[0] == 1:

            current_metadata_row = metadata_selected_data.iloc[0]
            filename = \
                str(pl.Path(current_metadata_row["STG_OdorAreaPath"]) / f"{animals_deduplicated[0]}.area.tif")

            _, selected_roi_labels = self.get_roi_and_selected_by_type()

            if len(selected_roi_labels) == 0:
                QMessageBox.critical(
                    self.MainWindow, "No ROIs selected!",
                    "Please select one or more ROIs on the right column and try again!"
                )

            self.save_area_for_VIEW(roi_labels=selected_roi_labels, filename=filename)

        else:

            QMessageBox.critical(
                self.MainWindow, "No data selected!",
                "Please select one imaging data on the right column and try again!"
            )

