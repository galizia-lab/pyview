from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QLabel
from .file_selector_combobox import get_file_selector_combobox_using_settings
from .main_function_widgets import MainFunctionAbstract


class LogLoadWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        new_vws_log_load = QPushButton("Load from new vws log file")
        new_vws_log_load.clicked.connect(self.parent.load_from_new_vws_log)
        layout.addWidget(new_vws_log_load)

        choose_from_current_vws_log = QPushButton("Select from current vws.log")
        choose_from_current_vws_log.clicked.connect(self.parent.choose_row_from_current_vws_log)
        layout.addWidget(choose_from_current_vws_log)


class ListLoadWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        yaml_loader = get_file_selector_combobox_using_settings()(
            groupbox_title="The YML file",
            file_filter="YML File(*.yml)",
            file_type="YML",
            parent=self.parent,
            use_list_in_settings="yml_file_list",
        )
        yaml_loader.return_filename_signal.connect(self.parent.load_yml_flags)
        layout.addWidget(yaml_loader)

        loading_hbox = QHBoxLayout()
        list_vbox = QVBoxLayout()

        new_load = QPushButton("Load from new list file")
        new_load.clicked.connect(self.parent.load_from_new_list)
        list_vbox.addWidget(new_load)
        self.parent.main_function_widgets["load_lst"] = new_load

        choose_from_current_list = QPushButton("Select row from current list")
        choose_from_current_list.clicked.connect(self.parent.choose_row_from_current_list)
        self.parent.main_function_widgets["select row from current list"] = choose_from_current_list
        list_vbox.addWidget(choose_from_current_list)

        new_vws_log_load = QPushButton("Load from new vws log file")
        new_vws_log_load.clicked.connect(self.parent.load_from_new_vws_log)
        list_vbox.addWidget(new_vws_log_load)
        self.parent.main_function_widgets["select row from new vws log file"] = new_vws_log_load

        choose_from_current_vws_log = QPushButton("Select from current vws.log")
        choose_from_current_vws_log.clicked.connect(self.parent.choose_row_from_current_vws_log)
        self.parent.main_function_widgets["select row from current vws log file"] = choose_from_current_vws_log
        list_vbox.addWidget(choose_from_current_vws_log)

        quick_load_from_current_lst_box_flags = ["STG_Measu"]
        quick_load_from_current_lst_box = MainFunctionAbstract(parent=self.parent,
                                                               group_name="Quick Load",
                                                               button_names=["Quick Load from current list"],
                                                               flag_names=quick_load_from_current_lst_box_flags,
                                                               flag_defaults=[self.parent.flags[f] for f in
                                                                              quick_load_from_current_lst_box_flags],
                                                               stack_vertically=False)
        loading_hbox.addLayout(list_vbox)
        quick_load_from_current_lst_box.send_data.connect(self.parent.quick_load_from_current_lst)
        quick_load_from_current_lst_box.flag_update_signal.connect(self.parent.flag_update_request_gui)
        self.parent.main_function_widgets["quick load from current list"] = quick_load_from_current_lst_box
        loading_hbox.addWidget(quick_load_from_current_lst_box)

        layout.addLayout(loading_hbox)
        selected_list_file_box = QGroupBox("List/VWS.LOG file selected", self)
        self.parent.current_measurement_label = QLabel("None selected yet")
        label_layout = QHBoxLayout(selected_list_file_box)
        label_layout.addWidget(self.parent.current_measurement_label)
        self.parent.main_function_widgets["selected list file"] = selected_list_file_box
        layout.addWidget(selected_list_file_box)