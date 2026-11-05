import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QPushButton

from view.gui.ILTIS_transfer_dialog import ILTISTransferDialog
from view.gui.tests.conftest import ListLoadTestData
from view.gui.tests.test_list_loading import load_data_yml_list
from view.napari_pyview import NapariPyViewWidget


def list_load_data_transfer_napari_helper(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    default_list_load_test_data: ListLoadTestData,
) -> dict:
    # load list data to pyview
    load_data_yml_list(
        napari_main_widget_with_mock_viewer,
        qtbot,
        monkeypatch,
        default_list_load_test_data,
    )

    # Verify buttons in napari_functions_widget
    napari_functions_widget = (
        napari_main_widget_with_mock_viewer.main_function_widgets[
            "Napari functions"
        ]
    )
    napari_buttons = napari_functions_widget.findChildren(QPushButton)
    napari_buttons_dict = {}
    for button in napari_buttons:
        assert (
            button.isEnabled()
        ), f"Napari button '{button.text()}' not enabled."

        napari_buttons_dict[button.text()] = button

    return napari_buttons_dict


def test_list_load_data_transfer_napari(
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    default_list_load_test_data: ListLoadTestData,
):
    napari_buttons_dict = list_load_data_transfer_napari_helper(
        qtbot,
        monkeypatch,
        napari_main_widget_with_mock_viewer,
        default_list_load_test_data,
    )
    transfer_button_name = (
        "Transfer raw data (post artifact correction) to Napari"
    )

    # Simulate a click on the button "Transfer raw data (post artifact correction) to Napari"
    assert (
        transfer_button_name in napari_buttons_dict
    ), f"Button '{transfer_button_name}' not found."
    qtbot.mouseClick(napari_buttons_dict[transfer_button_name], Qt.LeftButton)

    # Verify that a window of type ILTISTransferDialog has also been opened and is visible.
    iltis_transfer_dialog = napari_main_widget_with_mock_viewer.findChild(
        ILTISTransferDialog
    )
    assert (
        iltis_transfer_dialog is not None
    ), "ILTISTransferDialog (for transfer to Napari) not found."
    assert (
        iltis_transfer_dialog.isVisible()
    ), "ILTISTransferDialog (for transfer to Napari) not visible."

    # Simulate user click on the button with text "Import all" in the window mentioned in previous point.
    import_all_button = None
    for button in iltis_transfer_dialog.findChildren(QPushButton):
        if button.text() == "Import all":
            import_all_button = button
            break
    assert import_all_button is not None, "Import all button not found."
    qtbot.mouseClick(import_all_button, Qt.LeftButton)

    # Verify that this window is closed after this click.
    assert (
        not iltis_transfer_dialog.isVisible()
    ), "ILTISTransferDialog (for transfer to Napari) not closed after clicking 'Import all'."

    # Verify that an image layer has been added to napari for each row in data manager
    data_internal_labels = (
        napari_main_widget_with_mock_viewer.data_manager.get_all_internal_labels()
    )

    for name in data_internal_labels:
        assert (
            napari_main_widget_with_mock_viewer.napari_viewer.layers[name]
            is not None
        ), f"Image layer with name '{name}' not found in napari."
