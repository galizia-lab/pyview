#!/usr/bin/env python3
"""
Test file for list loading functionality in NapariPyViewWidget and transfer to ILTIS.
"""

import pathlib as pl

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtWidgets import QPushButton

from view.gui.tests.test_list_loading import load_data_yml_list
from view.napari_pyview.main_pyview_widget_napari import NapariPyViewWidget
from view.napari_pyview.tests.fixtures import napari_main_widget
from view.napari_pyview.tests.test_napari_direct_load_transfer_iltis import (
    check_transfer_data_napari_plugin_iltis,
)
from view.python_core.tests.common import get_synthetic_data_yml_path


def test_napari_list_load_transfer_iltis(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    napari_main_widget: NapariPyViewWidget,
):
    """
    Test function to verify list loading functionality in NapariPyViewWidget and transfer to ILTIS.

    Args:
        qtbot: pytest-qt bot for simulating user interactions
        monkeypatch: pytest-qt fixture for monkey patching
    """

    test_yml_file = str(get_synthetic_data_yml_path())
    lst_file = str(
        pl.Path(get_synthetic_data_yml_path()).parent
        / "02_LISTS"
        / "Synthetic_data_strip.lst.xls"
    )
    measurement_rows_to_select = (2, 3, 5, 6)

    load_data_yml_list(
        napari_main_widget,
        qtbot,
        monkeypatch,
        test_yml_file,
        lst_file,
        measurement_rows_to_select,
    )

    # Verify buttons in napari_functions_widget
    napari_functions_widget = napari_main_widget.main_function_widgets[
        "Napari functions"
    ]
    napari_buttons = napari_functions_widget.findChildren(QPushButton)
    for button in napari_buttons:
        assert button.isEnabled(), (
            f"Napari button '{button.text()}' not enabled."
        )

    # Call the helper function to verify and transfer of data to ILTIS
    check_transfer_data_napari_plugin_iltis(napari_main_widget, qtbot)

    # Check data in ILTIS
    iltis_window = napari_main_widget.iltis_window

    # Get data labels from ILTIS
    data_selector = iltis_window.iltis_main_shell.MainWindow.Front_Control_Panel.Data_Selector
    iltis_data_labels = data_selector.get_current_labels()

    assert len(iltis_data_labels) == len(measurement_rows_to_select), (
        f"Expected {len(measurement_rows_to_select)} entries in ILTIS data manager, but got {len(iltis_data_labels)}"
    )

    # Check that the data labels in ILTIS match the expected labels
    data_labels = napari_main_widget.data_manager.get_all_internal_labels()
    for label in data_labels:
        assert label in iltis_data_labels, (
            f"Data label '{label}' not found in ILTIS data manager"
        )


if __name__ == "__main__":
    pytest.main([__file__])
