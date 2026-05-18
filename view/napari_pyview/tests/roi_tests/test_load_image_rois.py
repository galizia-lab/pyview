"""
Helper function to test the presence of a layer in a napari viewer.
"""

import pathlib as pl

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt

from view.gui.tests.conftest import ListLoadTestData
from view.napari_pyview.main_pyview_widget_napari import NapariPyViewWidget
from view.napari_pyview.tests.test_napari_list_load_into_image_layers import (
    list_load_data_transfer_napari_helper,
)


def assert_layer_exists(viewer, layer_class_name, layer_name):
    """
    Assert that the napari viewer has a layer of the specified name and type.

    Parameters
    ----------
    viewer : napari.Viewer
        The napari viewer instance to check.
    layer_class_name : str
        The expected class name of the layer. E.g. Shapes, Labels, Image, Points, etc.
    layer_name : str
        The name of the layer to check.

    Raises
    ------
    AssertionError
        If the layer does not exist or the type does not match.
    """
    # Check if the layer exists
    assert (
        layer_name in viewer.layers
    ), f"Layer '{layer_name}' not found in viewer layers."

    # Get the layer
    layer = viewer.layers[layer_name]

    # Check if the layer type matches
    assert layer.__class__.__name__ == layer_class_name, (
        f"Layer '{layer_name}' is not of type '{layer_class_name}'. "
        f"Found type: '{layer.__class__.__name__}'"
    )


def list_load_data_roi_area_file_helper(
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    default_list_load_test_data_with_roi_file: ListLoadTestData,
    roi_or_area_file_to_select: str,
    file_selection_description: str,
    transfer_button_name: str,
    napari_layer_name_expected: str,
    napari_layer_class_name_expected: str,
):
    """
    Test that the napari viewer has the expected layers after loading data with ROI file.
    """

    napari_buttons_dict = list_load_data_transfer_napari_helper(
        qtbot,
        monkeypatch,
        napari_main_widget_with_mock_viewer,
        default_list_load_test_data_with_roi_file,
    )

    # Simulate a click on the button "Transfer raw data (post artifact correction) to Napari"
    assert (
        transfer_button_name in napari_buttons_dict
    ), f"Button '{transfer_button_name}' not found."

    monkeypatch.setattr(
        "qtpy.compat.getopenfilename",
        lambda *args, **kwargs: (
            roi_or_area_file_to_select,
            file_selection_description,
        ),
    )

    qtbot.mouseClick(napari_buttons_dict[transfer_button_name], Qt.LeftButton)

    # Verify the layers in the napari viewer

    assert_layer_exists(
        napari_main_widget_with_mock_viewer.napari_viewer,
        napari_layer_class_name_expected,
        napari_layer_name_expected,
    )


def test_list_load_data_transfer_napari_with_roi_file(
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    default_list_load_test_data_with_roi_file: ListLoadTestData,
):
    """
    Test that the napari viewer has the expected layers after loading data with ROI file.
    """
    roi_file_to_select = str(
        default_list_load_test_data_with_roi_file.roi_path
    )
    file_selection_description = "ROI file (*.roi)"
    transfer_button_name = "Load ROIs and add to Napari"
    napari_layer_class_name_expected = "Shapes"
    napari_layer_name_expected = (
        default_list_load_test_data_with_roi_file.roi_path.name
    )

    list_load_data_roi_area_file_helper(
        napari_main_widget_with_mock_viewer,
        qtbot,
        monkeypatch,
        default_list_load_test_data_with_roi_file,
        roi_file_to_select,
        file_selection_description,
        transfer_button_name,
        napari_layer_name_expected,
        napari_layer_class_name_expected,
    )


def test_list_load_data_transfer_napari_with_roi_tif_file(
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    default_list_load_test_data_with_roi_tif_file: ListLoadTestData,
):
    """
    Test that the napari viewer has the expected layers after loading data with ROI file.
    """
    roi_file_to_select = str(
        default_list_load_test_data_with_roi_tif_file.roi_path
    )
    file_selection_description = "ROI file (*.roi.tif)"
    transfer_button_name = "Load ROIs and add to Napari"
    napari_layer_class_name_expected = "Labels"
    napari_layer_name_expected = (
        default_list_load_test_data_with_roi_tif_file.roi_path.name
    ) + "_0"

    list_load_data_roi_area_file_helper(
        napari_main_widget_with_mock_viewer,
        qtbot,
        monkeypatch,
        default_list_load_test_data_with_roi_tif_file,
        roi_file_to_select,
        file_selection_description,
        transfer_button_name,
        napari_layer_name_expected,
        napari_layer_class_name_expected,
    )


def test_list_load_data_transfer_napari_with_coor_file(
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    default_list_load_test_data_with_coor_file: ListLoadTestData,
):
    """
    Test that the napari viewer has the expected layers after loading data with ROI file.
    """
    roi_file_to_select = str(
        default_list_load_test_data_with_coor_file.roi_path
    )
    file_selection_description = "ROI file (*.coor)"
    transfer_button_name = "Load ROIs and add to Napari"
    napari_layer_class_name_expected = "Shapes"
    napari_layer_name_expected = (
        default_list_load_test_data_with_coor_file.roi_path.name
    )

    list_load_data_roi_area_file_helper(
        napari_main_widget_with_mock_viewer,
        qtbot,
        monkeypatch,
        default_list_load_test_data_with_coor_file,
        roi_file_to_select,
        file_selection_description,
        transfer_button_name,
        napari_layer_name_expected,
        napari_layer_class_name_expected,
    )


def test_list_load_data_transfer_napari_with_area_roi_file(
    napari_main_widget_with_mock_viewer: NapariPyViewWidget,
    qtbot: QtBot,
    monkeypatch: pytest.MonkeyPatch,
    default_list_load_test_data_with_area_roi_file: ListLoadTestData,
):
    """
    Test that the napari viewer has the expected layers after loading data with ROI file.
    """
    roi_file_to_select = str(
        default_list_load_test_data_with_area_roi_file.area_path
    )
    file_selection_description = "AREA file (*.roi)"
    transfer_button_name = "Load Area and add to Napari"
    napari_layer_class_name_expected = "Shapes"
    napari_layer_name_expected = (
        default_list_load_test_data_with_area_roi_file.area_path.name
    )

    list_load_data_roi_area_file_helper(
        napari_main_widget_with_mock_viewer,
        qtbot,
        monkeypatch,
        default_list_load_test_data_with_area_roi_file,
        roi_file_to_select,
        file_selection_description,
        transfer_button_name,
        napari_layer_name_expected,
        napari_layer_class_name_expected,
    )
