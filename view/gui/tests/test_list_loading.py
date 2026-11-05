#!/usr/bin/env python3
"""
Test file for list loading functionality.
"""

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QPushButton

from view.gui.central_widget import CentralWidget
from view.gui.tests.conftest import ListLoadTestData
from view.gui.tests.test_yml_load_widget import select_yml_file_and_verify


def load_data_yml_list(
    central_widget: CentralWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    list_load_test_data: ListLoadTestData,
):
    """
    Helper function to load data from YML and list files.

    Args:
        central_widget: CentralWidget fixture
        qtbot: pytest-qt bot for simulating user interactions
        monkeypatch: pytest-qt fixture for monkey patching
        list_load_test_data: ListLoadTestData fixture
    """
    # 1. Call select_yml_file_and_verify to load flags from file returned by get_synthetic_data_yml_path()
    list_load_widget = central_widget.main_function_widgets[
        "load_lst"
    ].parent()
    select_yml_file_and_verify(
        list_load_widget, list_load_test_data.test_yml_path, qtbot, monkeypatch
    )

    # 2. Simulate a user click on ListLoadWidget.new_load and check if a new window of type LoadMeasurementFromListWindow gets opened
    new_load_button = list_load_widget.new_load
    qtbot.mouseClick(new_load_button, Qt.LeftButton)

    # Check if the LoadMeasurementFromListWindow is opened
    assert hasattr(
        central_widget, "load_measurement_window"
    ), "LoadMeasurementFromListWindow was not opened"

    # 3. Simulate user selection of the entry that starts with "--Select a new"
    load_measurement_window = central_widget.load_measurement_window
    combobox = load_measurement_window.lst_file_selector.combo_box

    select_new_index = combobox.findText("--Select a new LST/settings file--")
    assert (
        select_new_index >= 0
    ), "Could not find '--Select a new LST/settings file--' option in combobox"

    # Simulate user selecting the list file in the resulting FileOpenDialog
    monkeypatch.setattr(
        "qtpy.compat.getopenfilename",
        lambda *args, **kwargs: (
            str(list_load_test_data.lst_path),
            "List File(*.lst.xls)",
        ),
    )

    qtbot.mouseClick(combobox, Qt.LeftButton)
    qtbot.keyClicks(combobox, "--Select a new LST/settings file--")
    qtbot.keyClick(combobox, Qt.Key_Enter)

    # Assert that this populates the table with 9 entries
    table = load_measurement_window.lst_display_table
    assert (
        table.rowCount() == 9
    ), f"Expected table to have 9 entries, but got {table.rowCount()}"

    # 4. Simulate user selecting rows in the table and pressing the button "Load Measurement"
    for row_ind in list_load_test_data.measurement_rows_to_select:
        table.selectRow(row_ind)

    # Find the "Load Measurement" button in the window
    load_measurement_button = None
    for child in load_measurement_window.findChildren(QPushButton):
        if child.text() == "Load Measurement":
            load_measurement_button = child
            break

    assert (
        load_measurement_button is not None
    ), "Could not find 'Load Measurement' button"
    qtbot.mouseClick(load_measurement_button, Qt.LeftButton)

    # Check that the central_widget has the expected number of entries in its Data Manager
    data_labels = central_widget.data_manager.get_all_internal_labels()

    measurement_rows_to_select = list_load_test_data.measurement_rows_to_select
    assert len(data_labels) == len(
        measurement_rows_to_select
    ), f"Expected Data Manager to have {len(measurement_rows_to_select)} entries, but got {len(data_labels)}"

    # Assert that the widget ListLoadWidget.current_measurement_label shows the absolute path of the .lst.xls file chosen above
    current_measurement_label = list_load_widget.current_measurement_label
    assert current_measurement_label.text() == str(
        list_load_test_data.lst_path.absolute()
    ), f"Expected current_measurement_label to show '{list_load_test_data.lst_path.absolute()}', but got '{current_measurement_label.text()}'"

    # Assert that the button ListLoadWidget.choose_from_current_list is enabled
    choose_from_current_list_button = list_load_widget.choose_from_current_list
    assert (
        choose_from_current_list_button.isEnabled()
    ), "Expected choose_from_current_list button to be enabled"


def test_list_loading(
    central_widget: CentralWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    default_list_load_test_data: ListLoadTestData,
):
    """
    Test function to verify list loading functionality.

    Args:
        central_widget: CentralWidget fixture
        qtbot: pytest-qt bot for simulating user interactions
        monkeypatch: pytest-qt fixture for monkey patching
    """

    load_data_yml_list(
        central_widget, qtbot, monkeypatch, default_list_load_test_data
    )
