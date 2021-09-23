from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QAbstractItemView, QGroupBox, \
    QMessageBox, QDesktopWidget, QListWidget, QListWidgetItem, QPushButton, QHeaderView
from PyQt5.QtCore import pyqtSignal
from .custom_widgets import QTableWidgetPandasDF
import pandas as pd


class ILTISTransferDialog(QMainWindow):

    send_data_signal = pyqtSignal(list, list, pd.DataFrame, name="send data")

    def __init__(self, data_loaded_df, metadata_to_choose_from):

        super().__init__()

        self.data_loaded_df = data_loaded_df

        centralWidget = QWidget(self)
        main_vbox = QVBoxLayout(centralWidget)

        self.table = QTableWidgetPandasDF(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.refresh(data_loaded_df)

        main_vbox.addWidget(self.table)

        metadata_choice_box = QGroupBox("Select one or more metadata that will be used to "
                                        "construct the dataset name in iltis")
        metadata_choice_vboxlayout = QVBoxLayout(metadata_choice_box)
        self.metadata_choice_list = QTableWidgetPandasDF(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.metadata_choice_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.metadata_choice_list.refresh(pd.DataFrame.from_dict({"Metadata to choose from": metadata_to_choose_from}))
        self.metadata_choice_list.resizeColumnsToContents()

        metadata_choice_vboxlayout.addWidget(self.metadata_choice_list)

        main_vbox.addWidget(metadata_choice_box)

        import_button = QPushButton("Import")
        import_button.clicked.connect(self.send_data)

        main_vbox.addWidget(import_button)

        self.setCentralWidget(centralWidget)

        self.setWindowTitle('Transfer Data to ILTIS')
        self.setGeometry(300, 300, 500, 700)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def send_data(self):

        indices = [x.row() for x in self.table.selectionModel().selectedRows()]
        metadata_cols = [self.metadata_choice_list.item(x.row(), 0).text()
                         for x in self.metadata_choice_list.selectionModel().selectedRows()]

        if not indices:
            QMessageBox.critical(self, "No data Selected!", "Please select some data to continue transfer to ILTIS")
        else:
            self.send_data_signal.emit(indices, metadata_cols, self.data_loaded_df)
            self.close()




