from PyQt5.QtWidgets import QTableWidget, QTabWidget, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget, \
    QSizePolicy, QHeaderView, QMenu, QComboBox, QHBoxLayout, QLabel, QWidget
from PyQt5.QtGui import QGuiApplication, QCursor
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject
from .flags_search import get_flags_index, query
from collections import OrderedDict
from html.parser import HTMLParser
import pandas as pd


class ButtonCopyableLabel(QPushButton):

    def __init__(self, label):

        super().__init__(label)

    def contextMenuEvent(self, QContextMenuEvent):

        qmenu = QMenu(self)
        copy_action = qmenu.addAction("Copy name")
        copy_action.triggered.connect(self.copy_name_to_clipboard)
        qmenu.exec(QCursor().pos())

    def copy_name_to_clipboard(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.text())


class FlagSubgroupPage(QTableWidget):

    return_flag_signal = pyqtSignal(str, str, name="return_flag_signal")

    def __init__(self, parent, flags_default_values_descriptions_df):

        super().__init__(parent=parent)

        self.setRowCount(flags_default_values_descriptions_df.shape[0])
        self.setColumnCount(2)
        self.setHorizontalHeaderLabels(["Flag Name", "Flag Value"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.flag_values_descriptions_df = flags_default_values_descriptions_df.set_index("Flag Name")
        self.flag_values_descriptions_df.rename(columns={"Flag Default Value": "Flag Value"}, inplace=True)

        for index, (flag_name, flag_value, flags_description, selectable_options_str, flag_value_type) in \
                flags_default_values_descriptions_df.iterrows():

            if flag_value_type.find("bool") >= 0:
                to_update = "True:\nFalse:\n1: same as True\n0: same as False"
                if not pd.isnull(selectable_options_str):
                    to_update = f"{to_update}\n{selectable_options_str}"

                selectable_options_str = to_update
                self.flag_values_descriptions_df.loc[flag_name, "Selectable Options"] = selectable_options_str

            name_button = ButtonCopyableLabel(flag_name)
            name_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            name_button.setToolTip("Click here for a description of flag function and possible choices")
            name_button.clicked.connect(self.display_description)
            self.setCellWidget(index, 0, name_button)
            combobox = QComboBox(self)
            combobox.setToolTip(
                "Click on flag name (button just to the left) "
                "for a description of flag function and possible choices")
            combobox.setInsertPolicy(QComboBox.InsertAtBottom)
            combobox.setAccessibleName(flag_name)
            combobox.setEditable(True)
            if not pd.isnull(selectable_options_str):
                selectable_options_dict = self.parse_selectable_options_str(selectable_options_str)
                combobox.addItems(selectable_options_dict.keys())
            combobox.lineEdit().editingFinished.connect(self.return_flag)
            combobox.currentIndexChanged.connect(self.return_flag)

            self.flag_values_descriptions_df.loc[flag_name, "combobox"] = combobox
            # set_flag accesses the column "combobox", so it needs to be set beforehand
            self.set_flag(flag_name, flag_value)
            self.setCellWidget(index, 1, combobox)
            self.flag_values_descriptions_df.loc[flag_name, "button"] = name_button

    def parse_selectable_options_str(self, selectable_options_str):
        selectable_options_dict = {}
        for line in selectable_options_str.splitlines():
            if ":" in line:
                splits = line.split(":")
                k, d = splits[0], ":".join(splits[1:])
                selectable_options_dict[k.rstrip().lstrip()] = d

        return selectable_options_dict

    def set_flag(self, flag_name, flag_value):

        self.flag_values_descriptions_df.loc[flag_name, "combobox"].setCurrentText(str(flag_value))
        self.flag_values_descriptions_df.loc[flag_name, "Flag Value"] = str(flag_value)

    def reset_flag(self, flag_name, flag_value):
        self.flag_values_descriptions_df.loc[flag_name, "combobox"].setCurrentText(str(flag_value))

    def display_description(self):
        sender = QObject.sender(self)
        flag_name = sender.text()
        flag_descr = self.flag_values_descriptions_df.loc[flag_name, "Flag Description"]
        flag_selectable_values = self.flag_values_descriptions_df.loc[flag_name, "Selectable Options"]
        descr = flag_descr[:]  # make a copy
        if not pd.isnull(flag_selectable_values):
            descr = f"{descr}\n\nValid values:\n\n{flag_selectable_values}"
        QMessageBox.information(self, f"Description of flag '{flag_name}'", descr)

    def return_flag(self):
        sender_le = QObject.sender(self)
        if sender_le is not None:
            flag_name = sender_le.accessibleName()
            if flag_name in self.flag_values_descriptions_df.index.values:  # not sure why this check is needed
                self.return_flag_signal.emit(flag_name, sender_le.currentText())

    def jump_to_flag(self, flag_name):

        flag_index = self.flag_values_descriptions_df.index.values.tolist().index(flag_name)

        # this programmatic change will otherwise send currentChanged signal
        self.blockSignals(True)
        self.setCurrentCell(flag_index, 1)
        self.blockSignals(False)


class FlagsDisplayChoiceTabs(QTabWidget):

    def __init__(self, parent, flags):

        super().__init__(parent=parent)

        self.subgroup_pages = OrderedDict()

        self.setMovable(True)

        self.search_widget = FlagsSearchWidget(self, flags)
        self.search_widget.raise_jump_to_flag_signal.connect(self.jump_to_flag)
        self.addTab(self.search_widget, "Search")

        self.flag_name_subgroup_mapping = {}

        for subgroup in flags.get_subgroups():

            subgroup_flag_def_subset_df = flags.get_subgroup_definition(subgroup)

            subgroup_page = FlagSubgroupPage(parent=None,
                                             flags_default_values_descriptions_df=subgroup_flag_def_subset_df
                                             )
            self.flag_name_subgroup_mapping.update({flag_name: subgroup
                                              for flag_name in subgroup_flag_def_subset_df["Flag Name"]})

            self.subgroup_pages[subgroup] = subgroup_page
            widget = QWidget(self)
            vbox = QVBoxLayout()
            vbox.addWidget(subgroup_page)
            widget.setLayout(vbox)
            self.addTab(widget, subgroup)

    def block_flags_update_signals(self, b):

        for subgroup_page in self.subgroup_pages.values():
            subgroup_page.blockSignals(b)

    def set_flags(self, flags):
        for flag_name, flag_value in flags.items():
            # this can happen when a request is raised for updating a deprecated or an unknown flag
            if flag_name in self.flag_name_subgroup_mapping:
                subgroup = self.flag_name_subgroup_mapping[flag_name]
                self.subgroup_pages[subgroup].set_flag(flag_name, flag_value)

    def reset_flag(self, flag_name, flag_value):

        subgroup = self.flag_name_subgroup_mapping[flag_name]
        self.subgroup_pages[subgroup].reset_flag(flag_name, flag_value)

    @pyqtSlot(str, name="jump to flag")
    def jump_to_flag(self, flag_name):

        target_subgroup_name = self.flag_name_subgroup_mapping[flag_name]
        target_subgroup_page = self.subgroup_pages[target_subgroup_name]
        subgroup_index = list(self.subgroup_pages.keys()).index(target_subgroup_name)

        # this programmatic change will otherwise send currentChanged signal
        self.blockSignals(True)
        self.setCurrentIndex(subgroup_index + 1)  # index 0 is search page
        self.blockSignals(False)
        
        target_subgroup_page.jump_to_flag(flag_name)


class FlagNameParser(HTMLParser):

    def __init__(self, line):
        super().__init__()
        self.flag_name = None
        self.feed(line)

    def handle_data(self, data):
        self.flag_name = data


class FlagsSearchWidget(QWidget):

    raise_jump_to_flag_signal = pyqtSignal(str)

    def __init__(self, parent, flags):

        super().__init__(parent)

        self.search_index = get_flags_index(flags)

        vbox = QVBoxLayout(self)

        self.query_le = QLineEdit()
        self.query_le.setPlaceholderText("--- Search for flags here ---")
        self.query_le.textEdited.connect(self.query)
        vbox.addWidget(self.query_le)

        self.search_results_table = QTableWidget(self)
        self.search_results_table.setColumnCount(3)
        self.search_results_table.setHorizontalHeaderLabels(["Flag Name", "Flag Subgroup", "Flag Description"])
        self.search_results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        vbox.addWidget(self.search_results_table)

        self.flag_name_push_button_mapping_2way = {}

    @pyqtSlot(str, name="query and refresh")
    def query(self, text):

        self.flag_name_push_button_mapping_2way = {}

        highlights = query(index=self.search_index, query_str=text, max_results=20)

        self.search_results_table.clearContents()
        self.search_results_table.setRowCount(len(highlights))
        for ind, highlight in enumerate(highlights):
            self.search_results_table.setCellWidget(ind, 0, QLabel(highlight["flag_name"]))
            flag_name_parser = FlagNameParser(highlight["flag_name"])

            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.addWidget(QLabel(highlight["flag_subgroup"]))
            push_button = QPushButton("Go to flag")
            self.flag_name_push_button_mapping_2way[flag_name_parser.flag_name] = push_button
            self.flag_name_push_button_mapping_2way[push_button] = flag_name_parser.flag_name
            push_button.clicked.connect(self.raise_jump_to_flag)
            layout.addWidget(push_button)
            self.search_results_table.setCellWidget(ind, 1, widget)

            self.search_results_table.setCellWidget(ind, 2, QLabel(highlight["flag_description"]))
        self.search_results_table.resizeColumnsToContents()
        self.search_results_table.resizeRowsToContents()

    @pyqtSlot(name="raise jump to flag")
    def raise_jump_to_flag(self):

        sender = QObject.sender(self)
        self.raise_jump_to_flag_signal.emit(self.flag_name_push_button_mapping_2way[sender])











