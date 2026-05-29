from qtpy.QtCore import Qt
from qtpy.QtGui import QGuiApplication
from qtpy.QtWidgets import QMainWindow, QMessageBox

from view.iltis_shell.main_shell import ILTISMainShell


class ILTISWindowNapari(QMainWindow):

    def __init__(self, parent):

        super().__init__(parent)

        self.iltis_main_shell = ILTISMainShell(self)
        self.setCentralWidget(self.iltis_main_shell.MainWindow)

        self.setWindowTitle("ILTIS in Napari")
        self.setGeometry(200, 400, 600, 800)

        self.setAttribute(Qt.WA_DeleteOnClose)

        # self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QGuiApplication.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def closeEvent(self, event):

        reply = QMessageBox.critical(
            self,
            "Are you sure to quit?",
            "NOTE: this will also clear all data in ILTIS",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:

            self.iltis_main_shell.reset()
            event.accept()
        else:
            event.ignore()
