from PyQt5.QtWidgets import QVBoxLayout, QMessageBox, QWidget, QPushButton
from .file_selector_combobox import get_file_selector_combobox_using_settings
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject, QMetaObject
from ..python_core.p1_class import Default_P1_Getter, P1SingleWavelengthTIF, \
    P1SingleWavelengthLSM, P1DualWavelengthTill, P1SingleWavelengthTill, P1DualWavelengthTIFSingleFile, \
    P1SingleWavelengthLIF, P1SingleWavelength666, get_empty_p1
from view.python_core.flags import FlagsManager
import pathlib as pl
import traceback
import sys
from abc import abstractmethod
import tempfile


# modified version of solution from https://stackoverflow.com/questions/9374063/remove-all-items-from-a-layout
def clear_layout(layout):
    if layout is not None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
            else:
                clear_layout(item.layout())


class DirectDataLoader(QWidget):

    data_loaded_signal = pyqtSignal(dict, FlagsManager)

    def __init__(self, parent, default_LE_loadExp=3):

        super().__init__(parent=parent)
        vbox = QVBoxLayout(self)
        self.refresh_layout(default_LE_loadExp)

    @pyqtSlot(int)
    def refresh_layout(self, LE_loadExp):

        loader_interface_class = get_loader_interface_class(LE_loadExp)
        self.loader_interface = loader_interface_class(self)
        self.loader_interface.refresh_layout(self)
        self.loader_interface.data_loaded_signal.connect(self.data_loaded_signal)


def get_a_pst_combobox(parent, multiple_selection_allowed=True):
    combobox_class = get_file_selector_combobox_using_settings(multiple_selection_allowed=multiple_selection_allowed)

    return combobox_class(parent=parent,
                          groupbox_title="Till Vision Raw Data File(s)",
                          use_list_in_settings="raw data files",
                          settings_list_value_filter=lambda x: x.endswith(".pst"),
                          default_directory=None,
                          file_type="PST",
                          file_filter="PST files(*.pst)",
                          comment=None)


def get_an_lsm_combobox(parent):
    combobox_class = get_file_selector_combobox_using_settings(multiple_selection_allowed=True)

    return combobox_class(parent=parent,
                          groupbox_title="Zeiss Raw Data File(s)",
                          use_list_in_settings="raw data files",
                          settings_list_value_filter=lambda x: x.endswith(".lsm"),
                          default_directory=None,
                          file_type="LSM",
                          file_filter="LSM files(*.lsm)",
                          comment=None)


def get_a_lif_combobox(parent):
    combobox_class = get_file_selector_combobox_using_settings(multiple_selection_allowed=True)

    return combobox_class(parent=parent,
                          groupbox_title="Leica .lif Data File(s)",
                          use_list_in_settings="raw data files",
                          settings_list_value_filter=lambda x: x.endswith(".lif"),
                          default_directory=None,
                          file_type="Lif",
                          file_filter="Llif files(*.lif)",
                          comment=None)


def get_a_tiff_combobox(parent):
    combobox_class = get_file_selector_combobox_using_settings(multiple_selection_allowed=True)

    return combobox_class(parent=parent,
                          groupbox_title="VIEW-tif File(s)",
                          use_list_in_settings="raw data files",
                          settings_list_value_filter=lambda x: x.endswith(".tif") or x.endswith(".tiff"),
                          default_directory=None,
                          file_type="TIF",
                          file_filter="TIF files(*.tif *.tiff)",
                          comment=None)


class BaseLoaderInterface(QObject):

    data_loaded_signal = pyqtSignal(dict, FlagsManager)

    def __init__(self, parent):

        super().__init__(parent)
        self.default_p1_getter = Default_P1_Getter()

    def write_status(self, msg):

        self.parent().parent().parent().parent().write_status(msg)

    @pyqtSlot(list)
    @pyqtSlot(str)
    def load_list(self, filenames):

        filenames = self.check_revise_filenames(filenames)
        temp_dir = pl.Path(filenames[0][0]).parent / "temp_dir_for_view_analyses"
        temp_dir.mkdir(exist_ok=True)

        if filenames is not None:
            current_flags = self.parent().parent().parent().parent().flags.copy()
            # by default, compound path flags are not set, so set to parent of the raw files
            for flag_name in current_flags.compound_path_flags:
                current_flags.update_flags({flag_name: str(temp_dir)})
            current_flags.update_flags({"STG_Datapath": str(temp_dir.parent)})

            label_p1_mapping = {}
            for filename in filenames:
                p1 = self.check_read_data(current_flags, filename)
                if p1 is not None:
                    p1.calculate_signals(current_flags)
                    label_p1_mapping[p1.metadata.ex_name] = p1

            if label_p1_mapping:
                self.data_loaded_signal.emit(label_p1_mapping, current_flags)

    def check_read_data(self, flags, filenames):

        p1 = get_empty_p1(LE_loadExp=flags["LE_loadExp"], odor_conc=10)  # here p1 has not data, i.e. empty
        self.write_status(f"[working] Loading raw data directly from {filenames} using {p1.__class__.__name__}")
        try:
            p1.load_without_metadata(filenames=filenames, flags=flags)
        except Exception as e:
            exception_formatted = traceback.format_exception(*sys.exc_info())
            QMessageBox.critical(self.parent(), "Error reading file",
                                 f"Please check {filenames}.\n\n"
                                 f"Complete error message:\n"
                                 f"\n{''.join(exception_formatted)}")
            self.write_status(f"[failure] Loading raw data directly from {filenames}")
            return None

        self.write_status(f"[success] Loading raw data directly from {filenames}")
        return p1

    def check_revise_filenames(self, filenames):

        return [[x] for x in filenames]

    @abstractmethod
    def refresh_layout(self, widget):
        pass


class SampleData666LoaderInterface(BaseLoaderInterface):

    def __init__(self, parent):
        super().__init__(parent)
        self.temp_sample_dir = pl.Path(tempfile.gettempdir()) / "SampleDataPyView"
        self.temp_sample_dir.mkdir(exist_ok=True)

    def load_list_fake(self):
        self.load_list([str(self.temp_sample_dir / "Fake")])

    def refresh_layout(self, widget):

        clear_layout(widget.layout())
        button = QPushButton("&Load sample Data", widget)
        button.clicked.connect(self.load_list_fake)
        widget.layout().addWidget(button)


class VIEWTIFFLoaderInterface(BaseLoaderInterface):

    def __init__(self, parent):

        super().__init__(parent)

    def refresh_layout(self, widget):
        clear_layout(widget.layout())

        view_tif_combobox = get_a_tiff_combobox(widget)
        view_tif_combobox.return_filenames_signal.connect(self.load_list)

        widget.layout().addWidget(view_tif_combobox)


class TillSingleLoaderInterface(BaseLoaderInterface):

    def __init__(self, parent):

        super().__init__(parent)

    def refresh_layout(self, widget):
        clear_layout(widget.layout())

        pst_combobox = get_a_pst_combobox(widget, multiple_selection_allowed=True)
        pst_combobox.return_filenames_signal.connect(self.load_list)

        widget.layout().addWidget(pst_combobox)


class TillDualLoaderInterface(BaseLoaderInterface):

    def __init__(self, parent):

        super().__init__(parent)

    def refresh_layout(self, widget):

        clear_layout(widget.layout())

        self.pst_1_combobox = get_a_pst_combobox(widget, multiple_selection_allowed=False)
        # for the case when pst2 combobox is selected before pst1 combobox
        self.pst_1_combobox.return_filename_signal.connect(self.load_list)

        widget.layout().addWidget(self.pst_1_combobox)

        self.pst_2_combobox = get_a_pst_combobox(widget, multiple_selection_allowed=False)
        # for the case when pst1 combobox is selected before pst2 combobox
        self.pst_2_combobox.return_filename_signal.connect(self.load_list)

        widget.layout().addWidget(self.pst_2_combobox)

    @pyqtSlot(str)
    def check_revise_filenames(self, filenames):

        dbb1_filename = self.pst_1_combobox.get_current_entry()
        dbb2_filename = self.pst_2_combobox.get_current_entry()

        # load data and return only if both dbb1 and dbb2 files have been selected
        if dbb1_filename is not None and dbb2_filename is not None:

            return [[dbb1_filename, dbb2_filename]]
        else:
            return None


class LifSingleLoaderInterface(BaseLoaderInterface):

    def __init__(self, parent):

        super().__init__(parent)

    def refresh_layout(self, widget):

        clear_layout(widget.layout())

        lif_combobox = get_a_lif_combobox(widget)
        lif_combobox.return_filenames_signal.connect(self.load_list)

        widget.layout().addWidget(lif_combobox)


class ZeissSingleLoaderInterface(BaseLoaderInterface):

    def __init__(self, parent):

        super().__init__(parent)

    def refresh_layout(self, widget):

        clear_layout(widget.layout())

        lsm_combobox = get_an_lsm_combobox(widget)
        lsm_combobox.return_filenames_signal.connect(self.load_list)

        widget.layout().addWidget(lsm_combobox)


def get_loader_interface_class(LE_loadExp):

    if LE_loadExp == 3:
        return TillSingleLoaderInterface
    elif LE_loadExp == 4:
        return TillDualLoaderInterface
    elif LE_loadExp == 20:
        return ZeissSingleLoaderInterface
    elif LE_loadExp == 33:
        return VIEWTIFFLoaderInterface
    elif LE_loadExp == 34:
        return VIEWTIFFLoaderInterface
    elif LE_loadExp in (665, 667, 676):
        return SampleData666LoaderInterface
    else:
        raise NotImplementedError

