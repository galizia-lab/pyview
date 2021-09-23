from PyQt5.QtWidgets import QGroupBox, QComboBox, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from view.python_core.get_internal_files import get_setup_description_dict


class SetupChoice(QGroupBox):

    update_LE_loadExp_flag_signal = pyqtSignal(str, str)
    return_LE_loadExp = pyqtSignal(int)

    def __init__(self, parent):

        super().__init__("Choose your setup", parent)

        self.setup_description_dict = get_setup_description_dict()

        self.dropdown = QComboBox()
        self.dropdown.addItems(self.setup_description_dict.keys())
        self.dropdown.activated.connect(self.choice_made)

        vbox_layout = QVBoxLayout(self)

        vbox_layout.addWidget(self.dropdown)

    @pyqtSlot(int)
    def choice_made(self, index):
        chosen_LE_loadExp = list(self.setup_description_dict.values())[index]
        self.update_LE_loadExp_flag_signal.emit("LE_loadExp", str(chosen_LE_loadExp))
        self.return_LE_loadExp.emit(chosen_LE_loadExp)

    def get_current_LE_loadExp(self):

        return self.setup_description_dict[self.dropdown.currentText()]

    def update_flag_defaults(self, flags):
        if "LE_loadExp" in flags:
            for k, v in self.setup_description_dict.items():
                if v == int(flags["LE_loadExp"]):
                    self.dropdown.setCurrentText(k)
                    break









