from PyQt5.QtWidgets import QMainWindow, QMessageBox, QAction
from PyQt5.QtGui import QIcon
from .central_widget import CentralWidget
from view.python_core.get_internal_files import get_internal_icons
import pkg_resources


class VIEWMainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.initUI()

    def initUI(self):

        exit_icon = get_internal_icons("twotone-exit_to_app-24px.svg")
        exitAction = QAction(QIcon(exit_icon), 'Exit', self)
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(self.close)

        version_icon = get_internal_icons("twotone-loyalty-24px.svg")
        show_version_action = QAction(QIcon(version_icon), "Show Version", self)
        show_version_action.setStatusTip("Show Version")
        show_version_action.triggered.connect(self.show_version)


        self.statusBar().showMessage("Welcome! Load a YML file to begin.")

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(show_version_action)

        centralWidget = CentralWidget(self)
        self.setCentralWidget(centralWidget)

        self.setWindowTitle('VIEW')
        # self.setGeometry(QDesktopWidget().availableGeometry())
        # self.setWindowIcon(QIcon('web.png'))

    def show_version(self):

        view_version = pkg_resources.get_distribution("view").version
        QMessageBox.information(self, "Version", view_version)

    def closeEvent(self, event):

        msg = "Are you sure to quit?"
        reply = QMessageBox.question(self, 'Message',
                                     msg, QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()