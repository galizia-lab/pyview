#!/usr/bin/env python3
"""
Test file for direct data load flow in pyView and transfer to ILTIS

This test verifies that:\
 1. when a specific value is chosen in the setup_choice_box.dropdown, the corresponding loader object is correctly set\
 and the load button can be clicked.\
 2. When load button is clicked, data shows up correctly in pyView's data manager; widgets are enabled
 3. When data is transferred to ILTIS, data shows up correctly in ILTIS's data selector

"""

import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QPushButton

from view.gui.direct_load import DirectDataLoader, SampleData666LoaderWidget
from view.gui.tests.test_setup_choice import (
    select_item_and_check_in_setup_choice_box,
)


def test_direct_load_interaction(main_container_widget, qtbot):
    """
    Test that when the value "Synthetic data, type 665 (LE_loadExp=665)" is chosen in
    setup_choice_box.dropdown, then:
    1. direct_loader.loader_object is an object of class SampleData666LoaderWidget
    2. Simulate user click on the button direct_loader.load_button with text "Load sample Data"
    """

    # direct data load in VIEW

    central_widget = main_container_widget.view_main_window.centralWidget()

    # Get the setup_choice_box and direct_loader from the central_widget
    setup_choice_box = central_widget.setup_choice_box
    direct_loader = central_widget.findChild(DirectDataLoader)
    data_manager = central_widget.data_manager

    # select setup (LE_loadExp)
    target_text = "Synthetic data, type 665 (LE_loadExp=665)"
    select_item_and_check_in_setup_choice_box(
        setup_choice_box, qtbot, target_text
    )

    # Assert that the loader_object is an instance of SampleData666LoaderWidget
    assert isinstance(
        direct_loader.loader_object, SampleData666LoaderWidget
    ), f"Expected loader_object to be an instance of SampleData666LoaderWidget, but got {type(direct_loader.loader_object)}."

    # Simulate user click on the load button
    load_button = direct_loader.findChild(
        QPushButton, options=Qt.FindChildrenRecursively
    )
    load_button.click()

    data_labels = data_manager.get_all_internal_labels()

    assert (
        len(data_labels) == 1
    ), "No entry found in data manager after direct load with 665"
    assert (
        data_labels[0] == "Fake"
    ), "Data label wrong after direct data load with 665"

    for function_name in ["generate_overview"]:
        assert central_widget.main_function_widgets[
            function_name
        ].isEnabled(), f"Main function widget '{function_name}' not enabled."

    for (
        button_name,
        button_widget,
    ) in central_widget.misc_function_buttons.items():
        assert (
            button_widget.isEnabled()
        ), f"Misc. function button '{button_name}' not enabled."

    # ------------------------------------------------------------------------------------------------------------------

    # Transfer to ILTIS

    iltis_main_object = main_container_widget.iltis_main_object
    iltis_main_object.import_action_quick.trigger()

    data_selector = (
        iltis_main_object.MainWindow.Front_Control_Panel.Data_Selector
    )

    iltis_data_labels = data_selector.get_current_labels()

    assert (
        len(iltis_data_labels) == 1
    ), "No entry found in data manager of ILTIS after direct load with 665 and transfer to ILTIS"
    assert (
        data_labels[0] == "Fake"
    ), "Data label wrong in ILTIS after direct data load with 665 and transfer to ILTIS"


if __name__ == "__main__":
    pytest.main([__file__])
