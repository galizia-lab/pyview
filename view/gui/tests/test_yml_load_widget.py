#!/usr/bin/env python3
"""
Test file for ListLoadWidget functionality.
"""

import pathlib as pl

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtTest import QSignalSpy

from view.gui.loader_widgets import ListLoadWidget
from view.python_core.tests.common import get_synthetic_data_yml_path


def select_yml_file_and_verify(
    list_load_widget: ListLoadWidget,
    yml_path: pl.Path,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Helper function to simulate user selection of a YML file in ListLoadWidget.

    Args:
        list_load_widget: ListLoadWidget instance
        yml_path: pathlib Path to the YML file to select
        qtbot: pytest-qt bot for simulating user interactions
        monkeypatch: pytest-qt fixture for monkey patching
    """
    # 1. Assert the YML file exists on disk
    assert yml_path.exists(), f"YML file '{yml_path}' does not exist on disk"
    assert yml_path.is_file(), f"'{yml_path}' is not a file"

    yml_path_str = str(yml_path)
    # Use monkeypatch to replace qtpy.compat.getopenfilename with our test file
    monkeypatch.setattr(
        "qtpy.compat.getopenfilename",
        lambda *args, **kwargs: (yml_path_str, "YML File(*.yml)"),
    )

    # Create a signal spy to monitor the return_filename_signal
    signal_spy = QSignalSpy(
        list_load_widget.yaml_loader.return_filename_signal
    )

    # 2. Simulate user selecting "--Select a new YML file--" option
    combobox = list_load_widget.yaml_loader.combo_box
    select_new_index = combobox.findText("--Select a new YML file--")
    assert (
        select_new_index >= 0
    ), "Could not find '--Select a new YML file--' option in combobox"

    qtbot.mouseClick(combobox, Qt.LeftButton)
    qtbot.keyClicks(combobox, "--Select a new YML file--")
    qtbot.keyClick(combobox, Qt.Key_Enter)

    # 3. Assert that the file name is shown in the combobox
    current_text = combobox.currentText()
    assert (
        current_text == yml_path_str
    ), f"Expected combobox to show '{yml_path_str}', but got '{current_text}'"

    # 4. Assert that the signal was fired with the correct file name
    # We need to capture the signal emission using QSignalSpy

    # The signal should have been emitted when the file was selected
    assert len(signal_spy) > 0, "return_filename_signal was not emitted"

    # Get the arguments the signal was called with
    signal_args = signal_spy[0]  # Get the first emission
    assert len(signal_args) > 0, "Signal was not called with any arguments"

    emitted_filename = signal_args[0]  # First argument is the filename
    assert (
        emitted_filename == yml_path_str
    ), f"Expected signal to emit '{yml_path_str}', but got '{emitted_filename}'"


def test_yml_file_selection(
    list_load_widget: ListLoadWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):

    test_yml_path = get_synthetic_data_yml_path()

    select_yml_file_and_verify(
        list_load_widget, test_yml_path, qtbot, monkeypatch
    )
