from abc import abstractmethod

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QPushButton, QHBoxLayout, QAbstractItemView, QMessageBox, \
    QDesktopWidget, QWidget

from view.python_core.measurement_list import MeasurementList, get_importer_class
from .custom_widgets import QTableWidgetPandasDF
from .file_selector_combobox import get_file_selector_combobox_using_settings


class LoadMeasurementsFromFileWindow(QMainWindow):

    send_data_signal = pyqtSignal(MeasurementList, list,
                                  name="Measurement Selected")

    def __init__(self, LE_loadExp, default_directory_path, measurement_list=None):

        super().__init__()

        self.lst_file = None
        self.lst_df = None
        self.lst_df_filter = None
        self.lst_file_selector = None
        self.lst_display_table = None
        self.LE_loadExp = LE_loadExp
        self.measurement_list = measurement_list
        self.default_directory_path = default_directory_path

        self.init_UI()

        if measurement_list is not None:
            self.refresh_display()

    @abstractmethod
    def get_file_selector_combobox(self):

        pass

    def init_UI(self):

        main_vbox = QVBoxLayout()

        self.lst_file_selector = self.get_file_selector_combobox()

        self.lst_file_selector.return_filename_signal.connect(self.load_lst_from_file)
        main_vbox.addWidget(self.lst_file_selector)

        self.lst_display_table = QTableWidgetPandasDF(self)
        self.lst_display_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lst_display_table.setSelectionMode(QAbstractItemView.MultiSelection)

        main_vbox.addWidget(self.lst_display_table)

        finish_buttons = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.cancel)
        finish_buttons.addWidget(cancel_button)
        load_measurement_button = QPushButton("Load Measurement")
        load_measurement_button.clicked.connect(self.row_selected)
        finish_buttons.addWidget(load_measurement_button)

        main_vbox.addLayout(finish_buttons)

        centralWidget = QWidget(self)
        centralWidget.setLayout(main_vbox)

        self.setCentralWidget(centralWidget)

        self.setWindowTitle('Load Measurement')
        self.setGeometry(300, 300, 500, 700)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @abstractmethod
    def load_lst_from_file(self, lst_file):

        pass

    def refresh_display(self):
        self.lst_display_table.refresh(self.measurement_list.measurement_list_df)

    def cancel(self):
        self.close()

    def row_selected(self):

        row_selection_model = self.lst_display_table.selectionModel()

        try:
            measu_header_ind = self.lst_display_table.get_headers().index("Measu")
        except ValueError as ve:
            raise ValueError("Something went wrong in loading data. Could not find the column 'Measu' in "
                  "measurement selection table")
        
        if row_selection_model.hasSelection():
            selected_measus_widget_items = [
                self.lst_display_table.item(x.row(), measu_header_ind) for x in row_selection_model.selectedRows()]

            selected_measus = [int(float(x.text())) for x in selected_measus_widget_items]

            self.send_data_signal.emit(self.measurement_list, selected_measus)
            self.close()

        else:
            QMessageBox.critical(self, "IO Error", "No rows selected.  Please select one!")


class LoadMeasurementsFromListWindow(LoadMeasurementsFromFileWindow):
    
    def __init__(self, LE_loadExp, default_directory_path, measurement_list=None):
        
        super().__init__(LE_loadExp, default_directory_path, measurement_list)

    def get_file_selector_combobox(self):
        lst_file_selector = \
            get_file_selector_combobox_using_settings()(
                parent=self,
                groupbox_title="Choose a measurement List File "
                               "(.lst, .settings.xls/x, .lst.xls/x)",
                file_type="LST/settings",
                file_filter="Measurement List files"
                            " (*.lst *.xls *.xlsx)",
                use_list_in_settings="lst_file_list",
                default_directory=str(self.default_directory_path),
                settings_list_value_filter=
                lambda x: x.find(str(self.default_directory_path)) >= 0
            )

        return lst_file_selector

    @pyqtSlot(str, name="load lst file")
    def load_lst_from_file(self, lst_file):
        self.measurement_list = MeasurementList.create_from_lst_file(lst_file, self.LE_loadExp)
        self.refresh_display()


def measurement_filter(s):

    # exclude blocks with less than two frames or no calibration
    atleast_two_frames = False
    if type(s["Timing_ms"]) is str:
        if len(s["Timing_ms"].split(' ')) >= 2 and s["Timing_ms"].find("(No calibration available)") < 0:
            atleast_two_frames = True

    return atleast_two_frames


class LoadMeasurementsFromVWSLogWindow(LoadMeasurementsFromFileWindow):

    def __init__(self, LE_loadExp, default_directory_path, measurement_list=None):
        super().__init__(LE_loadExp, default_directory_path, measurement_list)

    def get_file_selector_combobox(self):
        lst_file_selector = \
            get_file_selector_combobox_using_settings()(
                parent=self,
                groupbox_title="Choose a VWS.LOG File "
                               "(.vws.log)",
                file_type="VWS.LOG",
                file_filter="Till VISION VWS.LOG files"
                            " (*.log)",
                use_list_in_settings="vws_log_files",
                default_directory=str(self.default_directory_path),
                settings_list_value_filter=
                lambda x: x.find(str(self.default_directory_path)) >= 0
            )

        return lst_file_selector

    @pyqtSlot(str, name="load lst file")
    def load_lst_from_file(self, lst_file):
        # initialize importer
        importer_class = get_importer_class(self.LE_loadExp)
        importer = importer_class(default_values={})  # no default values specified

        # automatically parse metadata
        metadata_df = importer.import_metadata(raw_data_files=[lst_file],
                                               measurement_filter=measurement_filter)

        self.measurement_list = MeasurementList.create_from_df(LE_loadExp=self.LE_loadExp, df=metadata_df)
        self.measurement_list.last_measurement_list_fle = lst_file
        self.refresh_display()