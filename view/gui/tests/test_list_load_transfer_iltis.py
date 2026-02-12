#!/usr/bin/env python3
"""
Test file for list loading functionality and transfer to ILTIS.
"""

import pathlib as pl

import pytest
from pytestqt.qtbot import QtBot

from view.gui.start_view_gui import ContainerWidget
from view.gui.tests.fixtures import main_container_widget
from view.gui.tests.test_list_loading import load_data_yml_list
from view.python_core.tests.common import get_synthetic_data_yml_path


def test_list_load_transfer_iltis(
    main_container_widget: ContainerWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
):
    """
    Test function to verify list loading functionality and transfer to ILTIS.

    Args:
        main_container_widget: Main container widget fixture
        qtbot: pytest-qt bot for simulating user interactions
        monkeypatch: pytest-qt fixture for monkey patching
    """
    central_widget = main_container_widget.view_main_window.centralWidget()

    test_yml_file = str(get_synthetic_data_yml_path())
    lst_file = str(
        pl.Path(get_synthetic_data_yml_path()).parent
        / "02_LISTS"
        / "Synthetic_data_strip.lst.xls"
    )
    measurement_rows_to_select = (2, 3, 5, 6)

    load_data_yml_list(
        central_widget,
        qtbot,
        monkeypatch,
        test_yml_file,
        lst_file,
        measurement_rows_to_select,
    )

    # Transfer to ILTIS
    iltis_main_object = main_container_widget.iltis_main_object
    iltis_main_object.import_action_quick.trigger()

    data_selector = (
        iltis_main_object.MainWindow.Front_Control_Panel.Data_Selector
    )

    iltis_data_labels = data_selector.get_current_labels()

    assert len(iltis_data_labels) == len(
        measurement_rows_to_select
    ), f"Expected {len(measurement_rows_to_select)} entries in ILTIS data manager, but got {len(iltis_data_labels)}"

    # Check that the data labels in ILTIS match the expected labels
    data_labels = central_widget.data_manager.get_all_internal_labels()
    for label in data_labels:
        assert (
            label in iltis_data_labels
        ), f"Data label '{label}' not found in ILTIS data manager"


if __name__ == "__main__":
    pytest.main([__file__])
