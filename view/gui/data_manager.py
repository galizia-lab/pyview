from view.gui.custom_widgets import QTableWidgetPandasDFDeletable
from PyQt5.QtWidgets import QAbstractItemView, QHeaderView, QLineEdit, QWidget
from PyQt5.QtCore import pyqtSlot, QObject, pyqtSignal
import pandas as pd
from view.python_core.utils.deduplicator import dedupilicate
from collections import OrderedDict
import copy


class DataManager(QObject):

    remove_data_signal = pyqtSignal(str, name="remove data signal")

    def __init__(self, parent: QWidget, flag_values_to_use: dict,
                 p1_values_to_use: dict, label_joiner: str,
                 default_label_cols: list, precedence_order: list):
        """
        The columns for gui-table are composed as follows: The column for the user-editable data label, followed by
        those defined in <p1_values_to_use>, followed by those defined in <flag_values_to_use>.
        The internal Dataframe variable <df> consists of the same columns, except the column for data labels. The row
        indices of <df> are internally generated labels.
        :param flag_values_to_use: dict, containing info about the flags values to store with data.
        Values are flag names and keys are the column names under which they will be shown
        :param p1_values_to_use: dict, containing info about the p1 values to store with data.
        Values are functions that take one argument, p1, as input and returns the string to show. Keys are the column
        names under which they will be shown
        :param label_joiner: str, which is used to join metadata values to form labels. E.g.: _ and -
        :param default_label_cols: list, list of column names whose values are to be joined to form the default label
        :param list precedence_order:  these column names will be placed before others, if they are used
        """

        super().__init__()
        self.label_line_edits = {}
        self.label_col_name = "gui_label"
        self.label_joiner = label_joiner
        self.defaultLabelCols = default_label_cols
        self.ui_table = None
        self.flag_values_to_use = flag_values_to_use
        self.p1_values_to_use = p1_values_to_use
        column_headers = \
            [self.label_col_name] + \
            self.reorder_column_names(
                list(self.flag_values_to_use.keys()) + list(self.p1_values_to_use.keys()), precedence_order)
        self.init_ui(parent, column_headers)
        self.df = pd.DataFrame(columns=column_headers[1:])

    def reorder_column_names(self, column_names: list, precedence_order: list):

        precedence_order2retain = [x for x in precedence_order if x in column_names]
        other_col_names = [x for x in column_names if x not in precedence_order]

        return precedence_order2retain + other_col_names

    def init_ui(self, parent, horizontal_headers=()):

        self.ui_table = QTableWidgetPandasDFDeletable(parent=parent)
        self.ui_table.setColumnCount(len(horizontal_headers))
        self.ui_table.setHorizontalHeaderLabels(horizontal_headers)
        self.ui_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.ui_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.ui_table.remove_data_signal.connect(self.row_deleted)

    def get_item_at(self, row_ind, col_ind):

        if col_ind == 1:
            return self.ui_table.cellWidget(row_ind, col_ind).text()
        else:
            return self.ui_table.item(row_ind, col_ind).text()

    def add_data(self, flags, p1, label_suggestion):

        row = pd.Series(dtype='float64')

        for k, v in self.p1_values_to_use.items():
            row[k] = str(v(p1))

        for k, v in self.flag_values_to_use.items():
            row[k] = str(flags[v])

        label = dedupilicate(value=label_suggestion, existing_values=self.get_all_internal_labels())
        self.ui_table.add_row(row)

        row.name = label
        #self.df = self.df.append(row) - since this is append of a series, the concat translation is with to_frame.T
        self.df = pd.concat([self.df, row.to_frame().T])

        le = QLineEdit(label)
        self.ui_table.setCellWidget(self.ui_table.rowCount() - 1, 0, le)
        self.label_line_edits[label] = le

        self.ui_table.selectRow(self.ui_table.rowCount() - 1)

        return label

    def get_selected_data_label(self):

        return self.df.index.values[self.ui_table.selectionModel().selectedRows()[0].row()]

    def get_all_internal_labels(self):

        return self.df.index.values.tolist()

    @pyqtSlot(int, name="row deleted")
    def row_deleted(self, row_ind):

        label_of_data_to_delete = self.df.index.values[row_ind]
        del self.label_line_edits[label_of_data_to_delete]
        self.df.drop(index=label_of_data_to_delete, inplace=True)
        self.remove_data_signal.emit(label_of_data_to_delete)















