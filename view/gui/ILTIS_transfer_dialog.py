import pandas as pd
from qtpy.QtCore import Signal, Slot
from qtpy.QtWidgets import (
    QAbstractItemView,
    QDesktopWidget,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from view.gui.custom_widgets import QTableWidgetPandasDF


class ILTISTransferDialog(QMainWindow):
    send_data_signal = Signal(list, list, name="send data")

    def __init__(self, parent, data_loaded_df, metadata_to_choose_from):

        super().__init__(parent)

        metadata_to_choose_from = [
            x.replace("\n", "---") for x in metadata_to_choose_from
        ]

        self.data_loaded_df = data_loaded_df

        centralWidget = QWidget(self)
        main_vbox = QVBoxLayout(centralWidget)

        self.table = QTableWidgetPandasDF(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.refresh(data_loaded_df)

        main_vbox.addWidget(self.table)

        metadata_choice_box = QGroupBox(
            "Select one or more metadata that will be used to "
            "construct the dataset name in iltis"
        )
        metadata_choice_vboxlayout = QVBoxLayout(metadata_choice_box)
        self.metadata_choice_list = QTableWidgetPandasDF(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.metadata_choice_list.setSelectionMode(
            QAbstractItemView.MultiSelection
        )
        self.metadata_choice_list.refresh(
            pd.DataFrame.from_dict(
                {"Metadata to choose from": metadata_to_choose_from}
            )
        )
        self.metadata_choice_list.resizeColumnsToContents()

        metadata_choice_vboxlayout.addWidget(self.metadata_choice_list)

        main_vbox.addWidget(metadata_choice_box)

        import_hbox = QWidget(self)
        import_hbox_layout = QHBoxLayout(import_hbox)
        import_button = QPushButton("Import", self)
        import_button.clicked.connect(self.send_data)

        import_hbox_layout.addWidget(import_button)

        import_all_button = QPushButton("Import all", self)
        import_all_button.clicked.connect(self.send_all_data)
        import_hbox_layout.addWidget(import_all_button)

        main_vbox.addWidget(import_hbox)

        self.setCentralWidget(centralWidget)

        self.setWindowTitle("Transfer Data to ILTIS")
        self.setGeometry(300, 300, 500, 700)
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    @Slot(name="Trigger import of data from View to ILTIS")
    def send_data(self):

        indices = [x.row() for x in self.table.selectionModel().selectedRows()]
        metadata_cols = [
            self.metadata_choice_list.item(x.row(), 0).text()
            for x in self.metadata_choice_list.selectionModel().selectedRows()
        ]

        # the inverse replacement was done for visualization purposes in self.__init__()
        metadata_cols = [x.replace("---", "\n") for x in metadata_cols]

        if not indices:
            QMessageBox.critical(
                self,
                "No data Selected!",
                "Please select some data to continue transfer to ILTIS",
            )
        else:
            self.send_data_signal.emit(indices, metadata_cols)
            self.close()

    def send_all_data(self):

        self.table.selectAll()
        self.send_data()
