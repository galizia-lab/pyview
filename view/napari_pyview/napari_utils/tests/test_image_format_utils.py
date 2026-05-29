import numpy as np
import pytest

from view.napari_pyview.napari_utils.image_format_utils import (
    convert_view_image_to_tif_2D,
    convert_view_image_to_tif_3D,
)


class TestImageFormatUtils:
    """Test cases for image format conversion utilities."""

    @classmethod
    def test_convert_view_image_to_tif_2D(cls):
        """Test 2D image conversion from VIEW to TIF format."""
        # Create a simple 2D image (XY format)
        image_xy = np.array([[1, 2], [3, 4]])

        # Convert to TIF format
        result = convert_view_image_to_tif_2D(image_xy)

        # Expected result after swapaxes and flip
        # Original: [[1, 2], [3, 4]]
        # After swapaxes: [[1, 3], [2, 4]]
        # After flip: [[2, 4], [1, 3]]
        expected = np.array([[2, 4], [1, 3]])

        np.testing.assert_array_equal(result, expected)

    @classmethod
    def test_convert_view_image_to_tif_2D_non_square(cls):
        """Test 2D image conversion with non-square dimensions."""
        # Create a non-square 2D image
        image_xy = np.array([[1, 2, 3], [4, 5, 6]])

        # Convert to TIF format
        result = convert_view_image_to_tif_2D(image_xy)

        # Expected result
        expected = np.array([[3, 6], [2, 5], [1, 4]])

        np.testing.assert_array_equal(result, expected)

    @classmethod
    def test_convert_view_image_to_tif_2D_assertion(cls):
        """Test that 2D conversion raises assertion error for non-2D input."""
        # Create a 3D image
        image_3d = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])

        # Should raise assertion error
        with pytest.raises(AssertionError):
            convert_view_image_to_tif_2D(image_3d)

    @classmethod
    def test_convert_view_image_to_tif_3D(cls):
        """Test 3D image conversion from VIEW to TIF format."""
        # Create a simple 3D image (XYT format)
        image_xyt = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])

        # Convert to TIF format
        result = convert_view_image_to_tif_3D(image_xyt)

        # Expected result after swapaxes and flip
        # Original shape: (2, 2, 2) - XYT
        # After swapaxes(0, 2): (2, 2, 2) - TYX
        # After flip(axis=1): (2, 2, 2) - TYX with Y flipped
        expected = np.array([[[3, 7], [1, 5]], [[4, 8], [2, 6]]])

        np.testing.assert_array_equal(result, expected)

    @classmethod
    def test_convert_view_image_to_tif_3D_non_cubic(cls):
        """Test 3D image conversion with non-cubic dimensions."""
        # Create a non-cubic 3D image
        image_xyt = np.random.rand(3, 4, 5)

        # Convert to TIF format
        result = convert_view_image_to_tif_3D(image_xyt)

        # Check shape is correct (should be TYX format)
        assert result.shape == (5, 4, 3)

    @classmethod
    def test_convert_view_image_to_tif_3D_assertion(cls):
        """Test that 3D conversion raises assertion error for non-3D input."""
        # Create a 2D image
        image_2d = np.array([[1, 2], [3, 4]])

        # Should raise assertion error
        with pytest.raises(AssertionError):
            convert_view_image_to_tif_3D(image_2d)
