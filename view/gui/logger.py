import logging
from PyQt5.QtWidgets import QPlainTextEdit, QGroupBox, QVBoxLayout
from ..python_core.appdirs import get_app_log_dir
import pathlib as pl
import time
import sys


# solution copied from https://stackoverflow.com/questions/28655198/best-way-to-display-logs-in-pyqt
class QPlainTextEditLogger(QPlainTextEdit, logging.Handler):

    def __init__(self, parent):
        super(QPlainTextEdit, self).__init__(parent)
        super(logging.Handler, self).__init__()

        self.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        text_cursor = self.textCursor()
        text_cursor.insertText(f"{msg}\n")
        self.setTextCursor(text_cursor)


class LoggerGroupBox(QGroupBox):

    def __init__(self, parent, location_dir=None):

        super().__init__("Event Log", parent)

        if location_dir is None:
            location_dir = get_app_log_dir()
        log_dir = pl.Path(location_dir)

        log_dir.mkdir(exist_ok=True, parents=True)

        log_file = str(log_dir / f"started_at_{time.strftime('%Y-%m-%d-%H-%M-%S')}.log")

        vbox = QVBoxLayout(self)

        self.log_pte = QPlainTextEditLogger(parent)
        self.log_pte.setLevel(level=logging.INFO)

        vbox.addWidget(self.log_pte)

        view_logger = logging.getLogger("VIEW")
        view_logger.setLevel(level=logging.INFO)

        formatter = logging.Formatter("%(asctime)s [VIEW] [%(levelname)-5.5s] %(message)s")

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

    def __del__(self):

        root_logger = logging.getLogger("VIEW")
        root_logger.removeHandler(self.log_pte)
        root_logger.removeHandler(self.log_file_handler)
