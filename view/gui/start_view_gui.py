from PyQt5.QtWidgets import QMainWindow, QAction, QApplication, QMessageBox, QDesktopWidget, QTabWidget
import sys
from view.gui.application_settings import initialize_app_settings
from view.gui.main_window import VIEWMainWindow
from view.iltis_shell.main_shell import ILTISMainShell
from matplotlib import pyplot as plt


class ContainerWidget(QTabWidget):

    def __init__(self):

        super().__init__()

        self.view_main_window = VIEWMainWindow()
        self.iltis_main_object = ILTISMainShell()

        view_central_widget = self.view_main_window.centralWidget()
        self.iltis_main_object.import_action.triggered.connect(view_central_widget.spawn_export_dialog)
        view_central_widget.export_data_signal.connect(self.iltis_main_object.import_data)
        view_central_widget.reset_iltis_signal.connect(self.iltis_main_object.reset)

        self.iltis_main_object.import_action_quick.triggered.connect(view_central_widget.export_data_all)

        self.addTab(self.view_main_window, "VIEW")
        self.addTab(self.iltis_main_object.MainWindow, "ILTIS")

    def closeEvent(self, event):

        msg = "Are you sure to quit?"
        reply = QMessageBox.question(self, 'Message',
                                     msg, QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            plt.close("all")
            event.accept()
        else:
            event.ignore()


def main():

    # Initialize application Name, Organization Name and Domain
    initialize_app_settings()

    app = QApplication(sys.argv)
    ex = ContainerWidget()
    ex.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
