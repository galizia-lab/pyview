from PyQt5.QtWidgets import QGroupBox, QComboBox, QVBoxLayout, QFileDialog, QSizePolicy, QLabel
from PyQt5.QtCore import QSettings, pyqtSlot, pyqtSignal, QCoreApplication
import os
import pathlib as pl
from collections import OrderedDict

from view.gui.application_settings import get_view_qsettings_manager


class SingleFileSelectorHComboBox(QGroupBox):

    return_filename_signal = pyqtSignal(str, name="return filename")

    def new_selection_handler(self, label):
        filename, used_filter = QFileDialog.getOpenFileName(parent=self,
                                                            caption=f"Select a {self.file_type} file",
                                                            directory=self.get_default_directory(),
                                                            filter=self.file_filter)

        possibly_index = self.combo_box.findText(filename)

        if filename:
            if possibly_index == -1:
                self.combo_box.addItem(filename)
                self.combo_box.setCurrentIndex(self.combo_box.count() - 1)
            else:
                self.combo_box.setCurrentIndex(possibly_index)
            self.return_filename(filename)

    def list_clearance_handler(self, label):

        entries_to_remove = []
        for index in range(self.combo_box.count()):
            entry = self.combo_box.itemText(index)
            if entry not in self.entry_handler_orderedDict.keys():
                entries_to_remove.append(entry)

        self.remove_entries(entries_to_remove)

    def __init__(self, parent, groupbox_title="File Selector",
                 file_type="", file_filter="All Files(*.*)", comment=None):

        super().__init__(title=groupbox_title, parent=parent)

        self.file_type = file_type
        self.file_filter = file_filter

        vbox = QVBoxLayout(self)

        if comment is not None:
            vbox.addWidget(QLabel(comment, parent))

        self.combo_box = QComboBox(self)

        self.entry_handler_orderedDict = OrderedDict()
        self.entry_handler_orderedDict[f"--Please choose a {file_type} file--"] = None
        self.entry_handler_orderedDict[f"--Select a new {file_type} file--"] = self.new_selection_handler
        self.entry_handler_orderedDict[f"--Clear this list--"] = self.list_clearance_handler

        self.inaction_entries = [f"--Please choose a {file_type} file--"]

        self.combo_box.addItems(self.entry_handler_orderedDict.keys())
        self.combo_box.setCurrentIndex(0)
        self.combo_box.setDuplicatesEnabled(False)
        self.combo_box.activated.connect(self.combo_box_activated)
        vbox.addWidget(self.combo_box)

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_file_type(self, file_type):

        self.file_type = file_type

    def set_file_filter(self, file_filter):

        self.file_filter = file_filter

    def get_current_file_list(self):

        return [self.combo_box.itemText(ind) for ind in range(self.combo_box.count())
                if self.combo_box.itemText(ind) not in self.entry_handler_orderedDict.keys()]

    def get_default_directory(self):

        return os.path.expanduser("~")

    def set_entry(self, entry):

        possible_index = self.combo_box.findText(entry)

        if possible_index < 0:
            raise ValueError(f"Entry {entry} not found in combobox")
        else:
            self.combo_box.setCurrentIndex(possible_index)

    def get_current_entry(self):

        current_text = self.combo_box.currentText()

        if current_text in self.entry_handler_orderedDict.keys():
            return None
        else:
            return current_text

    @pyqtSlot(int, name="combo box activation handler")
    def combo_box_activated(self, index):

        label = self.combo_box.itemText(index)
        for entry, handler in self.entry_handler_orderedDict.items():
            if label == entry and handler is not None:
                handler(label)
                return

        if label not in self.inaction_entries:
            self.return_filename(self.combo_box.currentText())

    def remove_entries(self, entries):

        [self.combo_box.removeItem(self.combo_box.findText(x)) for x in entries]

    def return_filename(self, filename):

        self.return_filename_signal.emit(filename)


class MultiFileSelectorHComboBox(SingleFileSelectorHComboBox):

    return_filenames_signal = pyqtSignal(list, name="return filename")

    def multi_selection_handler(self, label):
        filenames, used_filter = QFileDialog.getOpenFileNames(parent=self,
                                                              caption=f"Select a {self.file_type} file",
                                                              directory=self.get_default_directory(),
                                                              filter=self.file_filter)

        if len(filenames):
            entry = ",".join([pl.Path(x).name for x in filenames])
            self.combo_box.addItem(entry)
            self.combo_box.setCurrentIndex(self.combo_box.count() - 1)
            self.inaction_entries.append(entry)
            self.return_filename(filenames)

    def __init__(self, parent, groupbox_title="File Selector",
                 file_type="", file_filter="All Files(*.*)", comment=None):

        super().__init__(parent, groupbox_title, file_type, file_filter, comment)

        additional_entry = f"--Select multiple {self.file_type} files--"

        self.entry_handler_orderedDict[additional_entry] = self.multi_selection_handler

        self.combo_box.insertItem(2, additional_entry)

    def return_filename(self, filename):

        if type(filename) is str:
            return self.return_filenames_signal.emit([filename])
        elif type(filename) is list:
            return self.return_filenames_signal.emit(filename)
        else:
            raise(TypeError(f"Can only return str or list, got {type(filename)}"))


def get_file_selector_combobox_using_settings(multiple_selection_allowed=False):

    if multiple_selection_allowed:
        super_class = MultiFileSelectorHComboBox
    else:
        super_class = SingleFileSelectorHComboBox

    class FileSelectorHComboBoxUsingSettingsList(super_class):

        def __init__(self, parent, groupbox_title, use_list_in_settings, settings_list_value_filter=lambda x: True,
                     default_directory=None, file_type="", file_filter="All Files(*.*)",
                     comment=None):

            super().__init__(parent, groupbox_title, file_type, file_filter, comment)

            self.settings_list = use_list_in_settings

            self.default_directory = default_directory
            if self.default_directory is not None:
                if pl.Path(default_directory).is_dir():
                    self.default_directory = default_directory
                else:
                    self.default_directory = None

            settings = get_view_qsettings_manager()
            # add files from internal settings, checking if they exist and satisfy <settings_list_value_filter>
            if settings.contains(self.settings_list):
                file_list = settings.value(self.settings_list, type=list)
                file_list_existing = [x for x in file_list if os.path.isfile(x)]
                settings.setValue(self.settings_list, file_list_existing)
                self.combo_box.addItems([x for x in file_list_existing if settings_list_value_filter(x)])
            # if the <self.settings_list> does not exist, initialize it to empty list
            else:
                settings.setValue(self.settings_list, [])

        def get_default_directory(self):

            current_file_list = self.get_current_file_list()
            if self.default_directory is not None:
                return self.default_directory
            elif len(current_file_list):
                return str(pl.Path(current_file_list[-1]).parent)
            else:
                return os.path.expanduser("~")

        def return_filename(self, filename):

            settings = get_view_qsettings_manager()
            current_file_list = settings.value(self.settings_list, type=list)
            if filename not in current_file_list:
                if type(filename) is str:
                    filenames = [filename]
                elif type(filename) is list:
                    filenames = filename
                else:
                    raise NotImplementedError
                # update internal settings after deduplication
                settings.setValue(self.settings_list, list(set(current_file_list + filenames)))
            super().return_filename(filename)

        def remove_entries(self, entries):

            settings = get_view_qsettings_manager()
            current_file_list = settings.value(self.settings_list, type=list)
            for entry in entries:
                current_file_list.remove(entry)
                self.combo_box.removeItem(self.combo_box.findText(entry))
            settings.setValue(self.settings_list, current_file_list)

    return FileSelectorHComboBoxUsingSettingsList

