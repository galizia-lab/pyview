from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QWidget, QAbstractItemView
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt
from view.python_core.get_internal_files import get_internal_icons
import pandas as pd
import logging


class QTableWidgetPandasDF(QTableWidget):

    def __init__(self, parent):

        super().__init__(parent)

    def remove_all_rows(self):
        self.clear()
        self.setRowCount(0)

    def refresh(self, df: pd.DataFrame):
        self.remove_all_rows()
        self.setSortingEnabled(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.setColumnCount(df.shape[1])
        self.setHorizontalHeaderLabels(df.columns)

        df_no_index = df.reset_index(drop=True)
        for row_ind, row in df_no_index.iterrows():
            table_widget_items = []
            for x in row.values:
                table_widget_item = QTableWidgetItem()
                table_widget_item.setData(Qt.DisplayRole, str(x))
                table_widget_items.append(table_widget_item)

            self._add_row_items(row_index=str(row_ind), items=table_widget_items)

        self.setVerticalHeaderLabels([str(x) for x in df.index.values])
        self.setSortingEnabled(True)

    def get_headers(self):
        return [self.horizontalHeaderItem(col_ind).text() for col_ind in range(self.columnCount())]

    def add_row(self, s: pd.Series):

        cols_input = s.index.values.tolist()
        headers = self.get_headers()

        # if header is empty initialize
        if len(headers) == 0:
            assert self.rowCount() == 0 and self.columnCount() == 0, "Table has entries without headers, cannot " \
                                                                     "figure out how to insert entries from series"
            self.setHorizontalHeader(cols_input)
            vals2add = s.values
        else:

            vals2add = {k: v for k, v in enumerate(headers) if v in cols_input}

            cols_missing = set(vals2add.values()) - set(cols_input)

            if len(cols_missing) > 0:

                logging.warning(f"Adding a row: Ignoring the following columns, for which values were not specified: "
                                f"{cols_missing}")

        ind_item_mapping = {col_ind: QTableWidgetItem(str(s[col_name]), 0)
                            for col_ind, col_name in vals2add.items()}
        self._add_row_items(row_index=s.name, items=ind_item_mapping)

    def _add_row_items(self, row_index: str, items):
        """
        add a row of items
        :param row_index: str, vertical header label for the newly added row
        :param items: list or dict, if dict, keys must be column numbers and values column entries. if list, then
        indices of values will be interpreted as column numbers
        :return:
        """

        assert type(items) in (list, dict)

        if type(items) == list:
            items2use = {k: v for k, v in enumerate(items)}
        else:
            items2use = items

        new_row_ind = self.rowCount()
        self.insertRow(new_row_ind)

        for col_ind, item in items2use.items():
            self.setItem(new_row_ind, col_ind, item)

        self.setVerticalHeaderItem(new_row_ind, QTableWidgetItem(row_index, 0))


class QTableWidgetPandasDFDeletable(QTableWidgetPandasDF):

    remove_data_signal = pyqtSignal(int, name="delete data")

    def __init__(self, parent):

        super().__init__(parent)
        self.cellClicked.connect(self.send_delete_signal)
        self.horizontalHeader().sectionClicked.connect(self.delete_all)

    def setColumnCount(self, p_int):

        super().setColumnCount(p_int + 1)

    def setItem(self, row_ind: int, col_ind: int, item: QTableWidgetItem):

        super().setItem(row_ind, col_ind + 1, item)

    def setCellWidget(self, row_ind, col_ind, item: QWidget):

        super().setCellWidget(row_ind, col_ind + 1, item)

    def _add_row_items(self, row_index, items):

        super()._add_row_items(row_index, items)
        close_icon = QIcon(get_internal_icons("twotone-delete_forever-24px.svg"))
        super().setItem(self.rowCount() - 1, 0, QTableWidgetItem(close_icon, "", 0))

    def setHorizontalHeaderLabels(self, Iterable, p_str=None):

        super().setHorizontalHeaderLabels([""] + list(Iterable))
        close_icon = QIcon(get_internal_icons("twotone-delete_forever-24px.svg"))
        super().setHorizontalHeaderItem(0, QTableWidgetItem(close_icon, "", 0))

    def get_headers(self):

        to_return = super().get_headers()
        del to_return[0]
        return to_return

    @pyqtSlot(int, int, name="cell clicked")
    def send_delete_signal(self, row_ind, col_ind):
        if col_ind == 0:
            self.removeRow(row_ind)
            self.remove_data_signal.emit(row_ind)

    @pyqtSlot(int, name="header clicked")
    def delete_all(self, col_ind):
        if col_ind == 0:
            row_count = self.rowCount()
            for row_ind in list(range(row_count))[::-1]:
                self.send_delete_signal(row_ind=row_ind, col_ind=0)














