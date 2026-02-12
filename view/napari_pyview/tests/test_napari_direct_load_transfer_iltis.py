#!/usr/bin/env python3
"""
Test file for direct data load flow in NapariPyViewWidget and transfer to ILTIS.

This test verifies that:
1. when a specific value is chosen in the setup_choice_box.dropdown, the corresponding loader object is correctly set
   and the load button can be clicked.
2. When load button is clicked, data shows up correctly in NapariPyViewWidget's data manager; widgets are enabled
3. When data is transferred to ILTIS, data shows up correctly in ILTIS's data selector
"""

import pytest
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QPushButton

from view.gui.direct_load import DirectDataLoader, SampleData666LoaderWidget
from view.gui.ILTIS_transfer_dialog import ILTISTransferDialog
from view.gui.tests.test_setup_choice import (
    select_item_and_check_in_setup_choice_box,
)
from view.napari_pyview.iltis_window_napari import ILTISWindowNapari
from view.napari_pyview.main_pyview_widget_napari import NapariPyViewWidget


def test_napari_direct_load_transfer_iltis(
    napari_main_widget: NapariPyViewWidget, qtbot
):
    """
    Test that when the value "Synthetic data, type 665 (LE_loadExp=665)" is chosen in
    setup_choice_box.dropdown, then:
    1. direct_loader.loader_object is an object of class SampleData666LoaderWidget
    2. Simulate user click on the button direct_loader.load_button with text "Load sample Data"
    3. Data is transferred to ILTIS and verified
    """

    # Get the setup_choice_box and direct_loader from the napari_main_widget
    setup_choice_box = napari_main_widget.setup_choice_box
    direct_loader = napari_main_widget.findChild(DirectDataLoader)
    data_manager = napari_main_widget.data_manager

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
        assert napari_main_widget.main_function_widgets[
            function_name
        ].isEnabled(), f"Main function widget '{function_name}' not enabled."

    for (
        button_name,
        button_widget,
    ) in napari_main_widget.misc_function_buttons.items():
        assert (
            button_widget.isEnabled()
        ), f"Misc. function button '{button_name}' not enabled."

    # ------------------------------------------------------------------------------------------------------------------

    # Verify buttons in napari_functions_widget
    napari_functions_widget = napari_main_widget.main_function_widgets[
        "Napari functions"
    ]
    napari_buttons = napari_functions_widget.findChildren(QPushButton)
    for button in napari_buttons:
        assert (
            button.isEnabled()
        ), f"Napari button '{button.text()}' not enabled."

    # ------------------------------------------------------------------------------------------------------------------

    # Call the helper function to verify and transfer of data to ILTIS
    check_transfer_data_napari_plugin_iltis(napari_main_widget, qtbot)

    # Check data in ILTIS
    iltis_window = napari_main_widget.iltis_window

    # Get data labels from ILTIS
    data_selector = (
        iltis_window.iltis_main_shell.MainWindow.Front_Control_Panel.Data_Selector
    )
    iltis_data_labels = data_selector.get_current_labels()

    assert (
        len(iltis_data_labels) == 1
    ), "No entry found in data manager of ILTIS after direct load with 665 and transfer to ILTIS"
    assert (
        iltis_data_labels[0] == "Fake"
    ), "Data label wrong in ILTIS after direct data load with 665 and transfer to ILTIS"


def check_transfer_data_napari_plugin_iltis(
    napari_main_widget: NapariPyViewWidget, qtbot
):
    """
    Helper function to verify the transfer of data from NapariPyViewWidget to ILTIS.
    """
    # Verify buttons in iltis_functions_widget
    iltis_functions_widget = napari_main_widget.main_function_widgets[
        "ILTIS functions"
    ]
    iltis_buttons = iltis_functions_widget.findChildren(QPushButton)
    open_iltis_button = None
    for button in iltis_buttons:
        assert (
            button.isEnabled()
        ), f"ILTIS button '{button.text()}' not enabled."

        if button.text() == "Open ILTIS and\nlaunch transfer dialog":
            open_iltis_button = button

    # ------------------------------------------------------------------------------------------------------------------

    # Transfer to ILTIS
    # Simulate user mouse click on the button among "iltis_buttons" defined above with the text ""Open ILTIS and\nlaunch transfer dialog""
    assert open_iltis_button is not None, "Open ILTIS button not found."
    qtbot.mouseClick(open_iltis_button, Qt.LeftButton)

    # Verify that NapariPyViewWidget.iltis_window is not None and of type "ILTISWindowNapari" and is open.
    iltis_window = napari_main_widget.iltis_window
    assert iltis_window is not None, "ILTIS window is None."
    assert isinstance(
        iltis_window, ILTISWindowNapari
    ), "ILTIS window is not of type ILTISWindowNapari."
    assert iltis_window.isVisible(), "ILTIS window is not visible."

    # Verify that a window of type ILTISTransferDialog has also been opened.
    transfer_dialog = napari_main_widget.findChild(ILTISTransferDialog)
    assert transfer_dialog is not None, "ILTIS transfer dialog not found."
    assert transfer_dialog.isVisible(), "ILTIS transfer dialog is not visible."

    # Simulate user click on the button with text "Import all" in the window mentioned in previous point.
    import_all_button = None
    for button in transfer_dialog.findChildren(QPushButton):
        if button.text() == "Import all":
            import_all_button = button
            break
    assert import_all_button is not None, "Import all button not found."
    qtbot.mouseClick(import_all_button, Qt.LeftButton)

    # Verify that this window is closed after this click.
    assert (
        not transfer_dialog.isVisible()
    ), "ILTIS transfer dialog is still visible after clicking Import all."


if __name__ == "__main__":
    pytest.main([__file__])
