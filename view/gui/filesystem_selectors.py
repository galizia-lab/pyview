from PyQt5.QtWidgets import QGroupBox, QLabel, QSizePolicy, QPushButton, \
    QHBoxLayout, QFileDialog, QMessageBox
import os


def raiseInfo(str, parent):
    QMessageBox.information(parent, 'Warning!', str)


class PathChooser(QGroupBox):

    def choose_path_and_init(self):

        pass

    def __init__(self, title, parent=None, button_name="Select"):

        super().__init__(title, parent=parent)

        self.path_label = QLabel()
        self.path_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.choose_path_button = QPushButton(button_name)
        self.choose_path_button.setMaximumHeight(30)
        self.choose_path_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.choose_path_button.clicked.connect(self.choose_path_and_init)

        hbox = QHBoxLayout()
        hbox.addWidget(self.path_label)
        hbox.addWidget(self.choose_path_button)

        self.path_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.setMaximumHeight(60)

        self.setLayout(hbox)

    def setText(self, text):

        self.path_label.setText(text)

    def getText(self):

        return self.path_label.text()


class DirSelector(PathChooser):

    def __init__(self, title, parent=None, dialogTitle='',
                 dialogDefaultPath=None, **kwargs):
        super().__init__(title, parent, **kwargs)

        self.dialogTitle = dialogTitle
        if dialogDefaultPath is None or not os.path.isdir(dialogDefaultPath):
            dialogDefaultPath = os.path.expanduser('~')
        self.dialogDefaultPath = dialogDefaultPath

    def choose_path_and_init(self):

        dirPath = self.choose_path()
        self.setText(dirPath)

    def choose_path(self):

        return QFileDialog.getExistingDirectory(parent=self,
                                                dir=self.dialogDefaultPath,
                                                caption=self.dialogTitle,
                                                options=QFileDialog.ShowDirsOnly
                                                )

    def setText(self, text):

        if os.path.isdir(text) or os.path.isfile(text) or text is '':
            self.path_label.setText(text)
        else:
            raiseInfo('No such file or directory: ' + text, self)
            # pass


class FileSelector(PathChooser):

    def choose_path_and_init(self):

        file_path = self.choose_path()
        if file_path:
            self.setText(file_path)

    def choose_path(self):

        pass

    def __init__(self, widget_title, parent=None,
                 dialog_title='', default_dir=None, filter='All Files(*.*)',
                 **kwargs):

        super().__init__(widget_title, parent, **kwargs)
        self.dialogTitle = dialog_title
        if default_dir is None or not os.path.isdir(default_dir):
            default_dir = os.path.expanduser('~')
        self.dialogDefaultPath = default_dir
        self.dialogFileTypeFilter = filter


class FileSelectorExisting(FileSelector):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def setText(self, text):

        if os.path.isdir(text) or os.path.isfile(text) or text is '':
            self.path_label.setText(text)
        else:
            raiseInfo('No such file or directory: ' + text, self)
            # pass

    def choose_path(self):
        filePath, filter = QFileDialog.getOpenFileName(parent=self,
                                                       caption=self.dialogTitle,
                                                       directory=self.dialogDefaultPath,
                                                       filter=self.dialogFileTypeFilter)
        return filePath


class FileSaver(FileSelector):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.setText(self.dialogDefaultPath)

    def choose_path(self):

        filename, file_filter = QFileDialog.getSaveFileName(parent=self,
                                                             caption=self.dialogTitle,
                                                             directory=self.dialogDefaultPath,
                                                             filter=self.dialogFileTypeFilter)

        return filename