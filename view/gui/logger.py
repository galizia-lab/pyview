import logging
import pathlib as pl
import sys
import time

from qtpy import QtCore
from qtpy.QtWidgets import QGroupBox, QPlainTextEdit, QVBoxLayout

from view.python_core.appdirs import get_app_log_dir

# Source - https://stackoverflow.com/a/60528393
# Posted by tobilocker, modified by community. See post 'Timeline' for change history
# Retrieved 2026-02-05, License - CC BY-SA 4.0


class QTextEditLogger(logging.Handler, QtCore.QObject):
    appendPlainText = QtCore.Signal(str)

    def __init__(self, parent):
        super().__init__()
        QtCore.QObject.__init__(self)
        self.widget = QPlainTextEdit(parent)
        self.widget.setReadOnly(True)
        self.appendPlainText.connect(self.widget.appendPlainText)

    def emit(self, record):
        msg = self.format(record)
        self.appendPlainText.emit(msg)


class LoggerGroupBox(QGroupBox):
    def __init__(self, parent=None, location_dir=None):

        super().__init__("Event Log", parent)

        if location_dir is None:
            location_dir = get_app_log_dir()
        log_dir = pl.Path(location_dir)

        log_dir.mkdir(exist_ok=True, parents=True)

        log_file = str(
            log_dir / f"started_at_{time.strftime('%Y-%m-%d-%H-%M-%S')}.log"
        )

        vbox = QVBoxLayout(self)

        self.log_pte = QTextEditLogger(self)
        self.log_pte.setLevel(level=logging.INFO)

        vbox.addWidget(self.log_pte.widget)

        view_logger = logging.getLogger("VIEW")
        view_logger.setLevel(level=logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s [VIEW] [%(levelname)-5.5s] %(message)s"
        )

        self.log_file_handler = logging.FileHandler(log_file)
        self.log_file_handler.setFormatter(formatter)
        self.log_file_handler.setLevel(level=logging.DEBUG)

        view_logger.addHandler(self.log_file_handler)

        self.log_pte.setFormatter(formatter)
        view_logger.addHandler(self.log_pte)

        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level=logging.INFO)
        stream_handler.setFormatter(formatter)
        view_logger.addHandler(stream_handler)
