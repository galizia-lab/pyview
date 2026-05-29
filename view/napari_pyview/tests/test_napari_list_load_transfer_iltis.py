#!/usr/bin/env python3
"""
Test file for list loading functionality in NapariPyViewWidget and transfer to ILTIS.
"""

import pytest
from pytestqt.qtbot import QtBot

from view.gui.tests.conftest import ListLoadTestData
from view.gui.tests.test_list_loading import load_data_yml_list
from view.napari_pyview.main_pyview_widget_napari import NapariPyViewWidget
from view.napari_pyview.tests.test_napari_direct_load_transfer_iltis import (
    check_transfer_data_napari_plugin_iltis,
)


def test_napari_list_load_transfer_iltis(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    napari_main_widget: NapariPyViewWidget,
    default_list_load_test_data: ListLoadTestData,
):
    """
    Test function to verify list loading functionality in NapariPyViewWidget and transfer to ILTIS.

    Args:
        qtbot: pytest-qt bot for simulating user interactions
        monkeypatch: pytest-qt fixture for monkey patching
    """

    # load list data to pyview
    load_data_yml_list(
        napari_main_widget,
        qtbot,
        monkeypatch,
        default_list_load_test_data,
    )

    # Call the helper function to verify and transfer of data to ILTIS
    check_transfer_data_napari_plugin_iltis(napari_main_widget, qtbot)

    # Check data in ILTIS
    iltis_window = napari_main_widget.iltis_window

    # Get data labels from ILTIS
    data_selector = (
        iltis_window.iltis_main_shell.MainWindow.Front_Control_Panel.Data_Selector
    )
    iltis_data_labels = data_selector.get_current_labels()

    measurement_rows_to_select = (
        default_list_load_test_data.measurement_rows_to_select
    )
    assert len(iltis_data_labels) == len(
        measurement_rows_to_select
    ), f"Expected {len(measurement_rows_to_select)} entries in ILTIS data manager, but got {len(iltis_data_labels)}"

    # Check that the data labels in ILTIS match the expected labels
    data_labels = napari_main_widget.data_manager.get_all_internal_labels()
    for label in data_labels:
        assert (
            label in iltis_data_labels
        ), f"Data label '{label}' not found in ILTIS data manager"


if __name__ == "__main__":
    pytest.main([__file__])
