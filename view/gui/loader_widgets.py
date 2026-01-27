from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QLabel
from .file_selector_combobox import get_file_selector_combobox_using_settings
from .main_function_widgets import MainFunctionAbstract


class LogLoadWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.new_vws_log_load = None
        self.choose_from_current_vws_log = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.new_vws_log_load = QPushButton("Load from new vws log file")
        layout.addWidget(self.new_vws_log_load)

        self.choose_from_current_vws_log = QPushButton("Select from current vws.log")
        layout.addWidget(self.choose_from_current_vws_log)


class ListLoadWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.new_load = None
        self.choose_from_current_list = None
        self.new_vws_log_load = None
        self.choose_from_current_vws_log = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.yaml_loader = get_file_selector_combobox_using_settings()(
            groupbox_title="The YML file",
            file_filter="YML File(*.yml)",
            file_type="YML",
            parent=self.parent(),
            use_list_in_settings="yml_file_list",
        )
        layout.addWidget(self.yaml_loader)

        loading_hbox = QHBoxLayout()
        list_vbox = QVBoxLayout()

        self.new_load = QPushButton("Load from new list file")
        list_vbox.addWidget(self.new_load)

        self.choose_from_current_list = QPushButton("Select row from current list")
        list_vbox.addWidget(self.choose_from_current_list)

        self.new_vws_log_load = QPushButton("Load from new vws log file")
        list_vbox.addWidget(self.new_vws_log_load)

        self.choose_from_current_vws_log = QPushButton("Select from current vws.log")
        list_vbox.addWidget(self.choose_from_current_vws_log)

        quick_load_from_current_lst_box_flags = ["STG_Measu"]
        self.quick_load_from_current_lst_box = MainFunctionAbstract(parent=self.parent(),
                                                                group_name="Quick Load",
                                                                button_names=["Quick Load from current list"],
                                                                flag_names=quick_load_from_current_lst_box_flags,
                                                                flag_defaults=[self.parent().flags[f] for f in
                                                                               quick_load_from_current_lst_box_flags],
                                                                stack_vertically=False)
        loading_hbox.addLayout(list_vbox)
        loading_hbox.addWidget(self.quick_load_from_current_lst_box)

        layout.addLayout(loading_hbox)
        self.selected_list_file_box = QGroupBox("List/VWS.LOG file selected", self)
        self.current_measurement_label = QLabel("None selected yet")
        label_layout = QHBoxLayout(self.selected_list_file_box)
        label_layout.addWidget(self.current_measurement_label)
        layout.addWidget(self.selected_list_file_box)