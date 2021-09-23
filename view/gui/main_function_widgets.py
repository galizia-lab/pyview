from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLineEdit, QLabel, QPushButton, QGroupBox, QSizePolicy, \
    QFormLayout, QWidget, QCheckBox


class MainFunctionAbstract(QGroupBox):

    send_data = pyqtSignal(str, dict)
    flag_update_signal = pyqtSignal(str, str)

    def __init__(
            self, parent, button_names=(), flag_names=(),
            flag_defaults=(), group_name="", comment=None, stack_vertically=True):

        super().__init__(group_name, parent)

        if stack_vertically:
            layout = QVBoxLayout(self)
        else:
            layout = QHBoxLayout(self)

        if comment is not None:
            layout.addWidget(QLabel(comment, parent))

        flags_hbox = QHBoxLayout()

        self.flag_names = flag_names
        self.flag_line_edits = {}

        for flag, flag_default_value in zip(flag_names, flag_defaults):

            flag_group_box = self.create_get_flags_groupbox(flag, flag_default_value)

            flags_hbox.addWidget(flag_group_box)

        layout.addLayout(flags_hbox)

        buttons_hbox = QHBoxLayout()

        self.buttons = {}
        for button_name in button_names:
            button = QPushButton(button_name)
            self.buttons[button_name] = button
            button.clicked.connect(self.collect_send_data)
            buttons_hbox.addWidget(button)

        layout.addLayout(buttons_hbox)

    def create_get_flags_groupbox(self, flag, flag_default_value):

        flag_group_box = QWidget(self)
        flag_form_box = QFormLayout(flag_group_box)
        flag_group_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        line_edit = QLineEdit(str(flag_default_value))
        line_edit.setAccessibleName(flag)
        line_edit.editingFinished.connect(self.flag_update_request)
        flag_form_box.addRow(flag, line_edit)
        self.flag_line_edits[flag] = line_edit

        return flag_group_box

    def collect_send_data(self):

        sender = QObject.sender(self)

        self.send_data.emit(
            sender.text(),
            {flag: flag_line_edit.text() for flag, flag_line_edit in self.flag_line_edits.items()})

    def update_flag_defaults(self, flag_defaults):

        for flag_name, flag_value in flag_defaults.items():
            if flag_name in self.flag_names:
                self.flag_line_edits[flag_name].setText(str(flag_value))

    def flag_update_request(self):

        sender_le = QObject.sender(self)
        self.flag_update_signal.emit(sender_le.accessibleName(), sender_le.text())

    def reset_flag(self, flag_name, flag_value):

        self.flag_line_edits[flag_name].setText(str(flag_value))


class OverviewGenWidget(MainFunctionAbstract):

    send_data = pyqtSignal(str, dict, bool, bool)
    
    def __init__(self, parent, current_flags):
        
        gen_overviews_box_flags = ["CTV_Method", "CTV_firstframe", "CTV_lastframe"]
        super().__init__(
            parent=parent, button_names=["Generate(new)"],
            flag_names=gen_overviews_box_flags,
            flag_defaults=[current_flags[f] for f in gen_overviews_box_flags],
            group_name="Generate overview images",
            stack_vertically=True
        )
        
        self.check_boxes = {}
        self.deactivatable_flag_boxes = {}
        
        extra_hbox = QHBoxLayout()

        temp = {
                "CTV_FeatureNumber": "Use all features?", "CTV_StimulusNumber": "Use all stimuli?"
                }
        
        for flag, check_box_name in temp.items():

            flag_group_box = self.create_get_flags_groupbox(
                flag=flag, flag_default_value=current_flags[flag])

            self.deactivatable_flag_boxes[flag] = flag_group_box
            extra_hbox.addWidget(flag_group_box)

            check_box = QCheckBox(check_box_name, self)
            check_box.setAccessibleName(flag)
            check_box.stateChanged.connect(self.inactivate_flag)
            self.check_boxes[flag] = check_box

            extra_hbox.addWidget(check_box)

        self.layout().insertLayout(1, extra_hbox)

    @pyqtSlot(int, name="inactivate_flag")
    def inactivate_flag(self, state):

        sender = QObject.sender(self)
        self.deactivatable_flag_boxes[sender.accessibleName()].setEnabled(state != 2)

    def collect_send_data(self):
        sender = QObject.sender(self)

        self.send_data.emit(
            sender.text(),
            {flag: flag_line_edit.text() for flag, flag_line_edit in self.flag_line_edits.items()},
            self.check_boxes["CTV_FeatureNumber"].isChecked(),
            self.check_boxes["CTV_StimulusNumber"].isChecked()
        )
