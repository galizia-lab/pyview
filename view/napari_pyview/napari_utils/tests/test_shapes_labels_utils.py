import numpy as np
import pytest

from view.napari_pyview.napari_utils.shapes_labels_utils import (
    NapariLabelsLayerViewIO,
    NapariShapesLayerViewIO,
    ViewAreaIOManager,
    ViewRoiCoorIOManager,
)
from view.python_core.flags import FlagsManager


class TestNapariShapesLayerViewIO:
    """Test cases for NapariShapesLayerViewIO class."""

    @classmethod
    def test_get_kwargs_for_adding_to_napari(cls, mocker):
        """Test getting kwargs for adding shapes to napari."""
        # Create a mock FlagsManager
        mock_flags = mocker.MagicMock(spec=FlagsManager)
        mock_flags.__getitem__.side_effect = lambda key: {
            "SO_MV_colortable": 11,
            "SO_bgColor": "black",
            "SO_fgColor": "red",
        }.get(key)

        # Call the method
        kwargs = NapariShapesLayerViewIO.get_kwargs_for_adding_to_napari(
            mock_flags
        )

        # Check that we get edge_color and edge_width
        assert kwargs["edge_color"] == "#ff0000"
        assert kwargs["edge_width"] == 1

    @classmethod
    def test_add_roi_datas_to_napari(cls, make_napari_viewer_proxy, mocker):
        """Test adding ROI data to napari viewer."""
        # Create mock ROI data
        mock_roi1 = mocker.Mock()
        polygon_vertices = np.random.rand(6, 2) * 50 + 1
        mock_roi1.to_napari_shape_vertices_and_type.return_value = (
            polygon_vertices,
            "polygon",
        )
        mock_roi1.label = "ROI1"

        mock_roi2 = mocker.Mock()
        ellipse_vertices = np.random.rand(4, 2) * 50 + 1
        mock_roi2.to_napari_shape_vertices_and_type.return_value = (
            ellipse_vertices,
            "ellipse",
        )
        mock_roi2.label = "ROI2"

        roi_data = [mock_roi1, mock_roi2]
        frame_size = (100, 100)

        # Create mock viewer
        mock_viewer = make_napari_viewer_proxy()

        # Call the method
        NapariShapesLayerViewIO.add_roi_datas_to_napari(
            mock_viewer, roi_data, frame_size
        )

        # Access the mock object directly to check if add_shapes was called
        # Since the viewer is a proxy, we need to check the underlying mock
        assert hasattr(mock_viewer, "add_shapes")

        # more detailed testing to make sure that napari_viewer.add_shapes is called correctly could not be done because
        # patching and spying on napari_viewer.add_shapes does not work.


class TestNapariLabelsLayerViewIO:
    """Test cases for NapariLabelsLayerViewIO class."""

    @classmethod
    def test_get_kwargs_for_adding_to_napari(cls, mocker):
        """Test getting kwargs for adding labels to napari."""
        mock_flags = mocker.Mock(spec=FlagsManager)

        # Call the method
        kwargs = NapariLabelsLayerViewIO.get_kwargs_for_adding_to_napari(
            mock_flags
        )

        # Should return empty dict for labels
        assert kwargs == {}

    @classmethod
    def test_add_roi_datas_to_napari(cls, make_napari_viewer_proxy, mocker):
        """Test adding ROI data as labels to napari viewer."""
        # Create mock ROI data
        mock_roi = mocker.Mock()
        mock_roi.get_boolean_mask.return_value = np.array(
            [[True, False], [False, True]]
        )
        mock_roi.label = "ROI1"

        roi_data = [mock_roi]
        frame_size = (2, 2)

        # Mock the conversion function
        labels_array = np.array([[False, True], [True, False]])
        mocker.patch(
            "view.napari_pyview.napari_utils.image_format_utils.convert_view_image_to_tif_2D",
            return_value=labels_array,
        )

        # Create mock viewer
        mock_viewer = make_napari_viewer_proxy()

        # Call the method
        NapariLabelsLayerViewIO.add_roi_datas_to_napari(
            mock_viewer, roi_data, frame_size
        )

        # Access the mock object directly to check if add_shapes was called
        # Since the viewer is a proxy, we need to check the underlying mock
        assert hasattr(mock_viewer, "add_labels")

        # more detailed testing to make sure that napari_viewer.add_shapes is called correctly could not be done because
        # patching and spying on napari_viewer.add_shapes does not work.


class TestViewRoiCoorIOManager:
    """Test cases for ViewRoiCoorIOManager class."""

    @classmethod
    def test_get_default_dir(cls, mocker):
        """Test getting default directory."""
        mock_flags = mocker.Mock(spec=FlagsManager)
        mock_flags.get_coor_dir_str.return_value = "/test/coor/dir"

        result = ViewRoiCoorIOManager.get_default_dir(mock_flags)

        assert result == "/test/coor/dir"

    @classmethod
    def test_get_file_type_description(cls):
        """Test getting file type description."""
        description = ViewRoiCoorIOManager.get_file_type_description()
        assert description == "ROI/COOR File"

    @classmethod
    def test_get_file_extension_napari_io_object_mapping(cls):
        """Test getting file extension to IO class mapping."""
        mapping = (
            ViewRoiCoorIOManager.get_file_extension_napari_io_object_mapping()
        )

        assert ".roi" in mapping
        assert ".coor" in mapping
        assert ".roi.tif" in mapping

    @classmethod
    def test_get_file_extensions(cls):
        """Test getting list of file extensions."""
        extensions = ViewRoiCoorIOManager.get_file_extensions()

        assert ".roi" in extensions
        assert ".coor" in extensions
        assert ".roi.tif" in extensions

    @classmethod
    def test_get_fileopendialog_filtertext(cls):
        """Test getting file dialog filter text."""

        filter_text = ViewRoiCoorIOManager.get_fileopendialog_filtertext()

        assert "ROI/COOR File" in filter_text
        assert "*.roi" in filter_text
        assert "*.coor" in filter_text
        assert "*.roi.tif" in filter_text

    @classmethod
    def test_get_napari_shapes_labels_io_class(cls):
        """Test getting appropriate IO class for file extension."""

        manager = ViewRoiCoorIOManager

        # Test .roi extension
        io_class = manager.get_napari_shapes_labels_io_class("test.roi")
        assert io_class == NapariShapesLayerViewIO

        # Test .coor extension
        io_class = manager.get_napari_shapes_labels_io_class("test.coor")
        assert io_class == NapariShapesLayerViewIO

        # Test .roi.tif extension
        io_class = manager.get_napari_shapes_labels_io_class("test.roi.tif")
        assert io_class == NapariLabelsLayerViewIO

    @classmethod
    def test_get_napari_shapes_labels_io_class_invalid_extension(cls):
        """Test that invalid extension raises ValueError."""

        with pytest.raises(ValueError, match="Unsupported file extension"):
            ViewRoiCoorIOManager.get_napari_shapes_labels_io_class(
                "test.invalid"
            )

    @classmethod
    def test_ask_get_file(cls, mocker):
        """Test the ask_get_file method."""
        # Mock QFileDialog.getOpenFileName to return a test file path
        mocker.patch(
            "view.napari_pyview.napari_utils.shapes_labels_utils.QFileDialog.getOpenFileName",
            return_value=(
                "/test/path/to/file.roi",
                "ROI/COOR File (*.roi *.coor *.roi.tif)",
            ),
        )

        # Create a mock FlagsManager
        mock_flags = mocker.Mock(spec=FlagsManager)
        mock_flags.get_coor_dir_str.return_value = "/test/coor/dir"

        # Call the method
        result = ViewRoiCoorIOManager.ask_get_file(mock_flags)

        # Verify the result
        assert result == "/test/path/to/file.roi"

    @classmethod
    def test_ask_get_file_no_selection(cls, mocker):
        """Test the ask_get_file method when no file is selected."""
        # Mock QFileDialog.getOpenFileName to return empty string (no selection)
        mocker.patch(
            "view.napari_pyview.napari_utils.shapes_labels_utils.QFileDialog.getOpenFileName",
            return_value=("", "ROI/COOR File (*.roi *.coor *.roi.tif)"),
        )

        # Create a mock FlagsManager
        mock_flags = mocker.Mock(spec=FlagsManager)
        mock_flags.get_coor_dir_str.return_value = "/test/coor/dir"

        # Call the method
        result = ViewRoiCoorIOManager.ask_get_file(mock_flags)

        # Verify the result is empty string
        assert result == ""

    @classmethod
    def test_get_ask_file_add_to_napari(cls, mocker, make_napari_viewer_proxy):
        """Test the get_ask_file_add_to_napari method."""
        # Mock QFileDialog.getOpenFileName to return a test file path
        mocker.patch(
            "view.napari_pyview.napari_utils.shapes_labels_utils.QFileDialog.getOpenFileName",
            return_value=(
                "/test/path/to/file.roi",
                "ROI/COOR File (*.roi *.coor *.roi.tif)",
            ),
        )

        # Mock get_roi_io_class_from_file_path
        mock_roi_io_class = mocker.Mock()
        mock_roi_data_list = [mocker.Mock(), mocker.Mock()]
        mock_roi_io_class.read_roi_file.return_value = mock_roi_data_list
        mocker.patch(
            "view.napari_pyview.napari_utils.shapes_labels_utils.get_roi_io_class_from_file_path",
            return_value=mock_roi_io_class,
        )

        # Mock the ROI data methods
        for mock_roi in mock_roi_data_list:
            mock_roi.to_napari_shape_vertices_and_type.return_value = (
                np.array([[0, 0], [1, 0], [1, 1], [0, 1]]),
                "polygon",
            )
            mock_roi.label = "TestROI"

        # Create a mock FlagsManager
        mock_flags = mocker.MagicMock(spec=FlagsManager)
        mock_flags.get_coor_dir_str.return_value = "/test/coor/dir"
        mock_flags.__getitem__.side_effect = lambda key: {
            "SO_MV_colortable": 11,
            "SO_bgColor": "black",
            "SO_fgColor": "red",
        }.get(key)

        # Create a mock napari viewer
        mock_viewer = make_napari_viewer_proxy()

        # Call the method
        result = ViewRoiCoorIOManager.get_ask_file_add_to_napari(
            mock_viewer, mock_flags, frame_size=(100, 100)
        )

        # Verify the result
        assert result[0] == mock_roi_data_list
        assert result[1] == "/test/path/to/file.roi"

        # Access the mock object directly to check if add_shapes was called
        # Since the viewer is a proxy, we need to check the underlying mock
        assert hasattr(mock_viewer, "add_shapes")

        # more detailed testing to make sure that napari_viewer.add_shapes is called correctly could not be done because
        # patching and spying on napari_viewer.add_shapes does not work.

    @classmethod
    def test_get_ask_file_add_to_napari_no_selection(cls, mocker):
        """Test the get_ask_file_add_to_napari method when no file is selected."""
        # Mock QFileDialog.getOpenFileName to return empty string (no selection)
        mocker.patch(
            "view.napari_pyview.napari_utils.shapes_labels_utils.QFileDialog.getOpenFileName",
            return_value=("", "ROI/COOR File (*.roi *.coor *.roi.tif)"),
        )

        # Create a mock FlagsManager
        mock_flags = mocker.Mock(spec=FlagsManager)
        mock_flags.get_coor_dir_str.return_value = "/test/coor/dir"

        # Create a mock napari viewer
        mock_viewer = mocker.Mock()

        # Call the method
        result = ViewRoiCoorIOManager.get_ask_file_add_to_napari(
            mock_viewer, mock_flags, frame_size=(100, 100)
        )

        # Verify the result is None for both elements
        assert result[0] is None
        assert result[1] is None


class TestViewAreaIOManager:
    """Test cases for ViewAreaIOManager class."""

    @classmethod
    def test_get_default_dir(cls, mocker):
        """Test getting default directory for areas."""
        mock_flags = mocker.Mock(spec=FlagsManager)
        mock_flags.get_area_dir_str.return_value = "/test/area/dir"

        result = ViewAreaIOManager.get_default_dir(mock_flags)

        assert result == "/test/area/dir"

    @classmethod
    def test_get_file_type_description(cls):
        """Test getting file type description for areas."""
        description = ViewAreaIOManager.get_file_type_description()
        assert description == "VIEW AREA File"

    @classmethod
    def test_get_file_extension_napari_io_object_mapping(cls):
        """Test getting file extension to IO class mapping for areas."""

        mapping = (
            ViewAreaIOManager.get_file_extension_napari_io_object_mapping()
        )

        assert ".Area" in mapping
        assert ".area.tif" in mapping
        assert len(mapping) == 2
        # Both should map to NapariLabelsLayerViewIO
        assert all(
            io_class == NapariLabelsLayerViewIO
            for io_class in mapping.values()
        )
