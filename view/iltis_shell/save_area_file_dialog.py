from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QComboBox, QGroupBox, QListWidget, QAbstractItemView,\
QListWidgetItem, QPushButton, QDesktopWidget, QMessageBox
from PyQt5.QtCore import pyqtSlot, pyqtSignal
from view.gui.filesystem_selectors import FileSaver
import pathlib as pl


class AbstractSaveROIsDialog(QMainWindow):

    return_choices_signal = pyqtSignal(list, str, name="choices")

    def __init__(self, metadata, roi_labels, extension, file_filter):

        super().__init__()

        self.metadata = metadata
        self.roi_labels = roi_labels
        self.extension = extension
        self.file_filter = file_filter

    def initui(self, data_selected, rois_selected, data_chooser_title, roi_chooser_title,
               file_selector_dialog_title, file_selector_widget_title, save_button_title, window_title):

        central_widget = QWidget(self)
        main_vbox = QVBoxLayout(central_widget)

        data_chooser_group = QGroupBox(data_chooser_title)
        data_chooser_vbox = QVBoxLayout(data_chooser_group)
        self.data_chooser = QComboBox(data_chooser_group)
        self.data_chooser.addItems(self.metadata["Label to use"].values)
        self.data_chooser.setCurrentText(str(data_selected[0]))
        self.data_chooser.setDuplicatesEnabled(False)
        self.data_chooser.activated.connect(self.refresh_filename)
        data_chooser_vbox.addWidget(self.data_chooser)
        main_vbox.addWidget(data_chooser_group)

        roi_chooser_group = QGroupBox(roi_chooser_title)
        roi_chooser_vbox = QVBoxLayout(roi_chooser_group)
        self.roi_chooser = QListWidget(self)
        self.roi_chooser.setSelectionMode(QAbstractItemView.MultiSelection)
        for poly_roi in self.roi_labels:
            list_item = QListWidgetItem(poly_roi, parent=self.roi_chooser, type=0)
            if poly_roi in rois_selected:
                list_item.setSelected(True)
            self.roi_chooser.addItem(list_item)

        roi_chooser_vbox.addWidget(self.roi_chooser)
        main_vbox.addWidget(roi_chooser_group)

        save_mode_group = QGroupBox("Choose whether to save for only this "
                                    "measurement or all measurements of this animal")
        save_mode_vbox = QVBoxLayout(save_mode_group)

        self.save_mode_chooser = QComboBox(save_mode_group)
        self.save_mode_chooser.addItems(["Save FOR ALL measurements of this animal",
                                         "Save ONLY FOR THIS measurement of this animal"])
        self.save_mode_chooser.setCurrentIndex(0)
        self.save_mode_chooser.activated.connect(self.refresh_filename)
        save_mode_vbox.addWidget(self.save_mode_chooser)
        main_vbox.addWidget(save_mode_group)

        self.file_selector = FileSaver(widget_title=file_selector_widget_title, parent=self,
                                       dialog_title=file_selector_dialog_title, filter=self.file_filter
                                       )
        self.refresh_filename(0)
        main_vbox.addWidget(self.file_selector)

        save_button = QPushButton(save_button_title)
        save_button.clicked.connect(self.return_choices)
        main_vbox.addWidget(save_button)

        self.setCentralWidget(central_widget)

        self.setWindowTitle(window_title)
        self.setGeometry(300, 300, 500, 700)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @classmethod
    def get_destination_directory_flag_name(cls):
        return None

    @pyqtSlot(int, name="refresh filename when data or mode changes")
    def refresh_filename(self, index):

        current_label = self.data_chooser.currentText()
        current_metadata_row = self.metadata.loc[self.metadata["Label to use"] == current_label, :].iloc[0]
        choice_mode = self.save_mode_chooser.currentIndex()
        animal = current_metadata_row['STG_ReportTag']
        measurement_label = current_metadata_row['Measurement\nLabel']
        if choice_mode == 0:
            filename = f"{animal}{self.extension}"
        else:
            filename = f"{animal}_{measurement_label}{self.extension}"
        destination_dir = pl.Path(current_metadata_row[self.get_destination_directory_flag_name()])
        default_filename = str(destination_dir / filename)
        self.file_selector.dialogDefaultPath = default_filename
        self.file_selector.setText(default_filename)

    def return_choices(self):

        chosen_rois = [x.text() for x in self.roi_chooser.selectedItems()]
        target_filename = self.file_selector.getText()

        if len(chosen_rois) > 0:
            self.return_choices_signal.emit(chosen_rois, target_filename)
            self.close()
        else:
            QMessageBox.critical(self, "IO Error", "No ROIs selected.  Please select at least one!")


class SaveAreaFileDialog(AbstractSaveROIsDialog):

    def __init__(self, metadata, poly_roi_labels, data_selected, poly_rois_selected):

        super().__init__(metadata, poly_roi_labels, extension=".area.tif", file_filter="AREA files (*tif)")
        self.initui(data_selected=data_selected, rois_selected=poly_rois_selected,
                    data_chooser_title="Choose the measurement for which area file is to be saved",
                    roi_chooser_title="Choose the polygon ROIS, the union of which will form the area",
                    file_selector_widget_title="Select the folder and filename into which the area file is to be saved",
                    file_selector_dialog_title="Select where the area file is to be saved",
                    save_button_title="Save area file for VIEW",
                    window_title='Save area file for VIEW')

    @classmethod
    def get_destination_directory_flag_name(cls):

        return "STG_OdorAreaPath"


class SaveCircleROIsFileDialog(AbstractSaveROIsDialog):

    def __init__(self, metadata, circle_roi_labels, data_selected, circle_rois_selected):

        super().__init__(metadata, circle_roi_labels, extension=".roi", file_filter="Roi files (*roi)")
        self.initui(data_selected=data_selected, rois_selected=circle_rois_selected,
                    data_chooser_title="Choose the measurement for which ROIs are to be saved",
                    roi_chooser_title="Choose the circle ROIs to be saved",
                    file_selector_widget_title="Select the folder and filename into which the ROIs are to be saved",
                    file_selector_dialog_title="Select where the ROIs are to be saved",
                    save_button_title="Save ROIs for VIEW",
                    window_title="Save ROIs for VIEW")

    @classmethod
    def get_destination_directory_flag_name(cls):
        return "STG_OdormaskPath"


class SaveAllROIsFileDialog(AbstractSaveROIsDialog):

    def __init__(self, metadata, roi_labels, data_selected, roi_labels_selected):

        super().__init__(metadata, roi_labels, extension=".roi", file_filter="ROI files (*roi)")
        self.initui(data_selected=data_selected, rois_selected=roi_labels_selected,
                    data_chooser_title="Choose the measurement for which ROIs are to be saved",
                    roi_chooser_title="Choose the ROIs to be saved",
                    file_selector_widget_title="Select the folder and filename into which the ROIs are to be saved",
                    file_selector_dialog_title="Select where the ROIs are to be saved",
                    save_button_title="Save ROI for VIEW",
                    window_title="Save ROI for VIEW")

    @classmethod
    def get_destination_directory_flag_name(cls):
        return "STG_OdormaskPath"









