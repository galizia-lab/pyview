#!/usr/bin/env python3
"""Test script to validate the changes made to SquareIDLROIData class."""

import pytest

from view.python_core.rois.idl_rois import SquareIDLROIData


def test_square_validation_within_bounds():
    """Test validation for SquareIDLROIData with vertices within bounds."""
    square = SquareIDLROIData("test_square", 10, 10, 5)
    vertices, shape_type = square.to_napari_shape_vertices_and_type((100, 100))
    assert shape_type == "rectangle"
    # Expected vertices for a square centered at (10, 10) with half_width 5
    expected_vertices = [
        [5, 5],
        [15, 5],
        [15, 15],
        [5, 15],
    ]
    assert vertices == expected_vertices


def test_square_validation_outside_bounds():
    """Test validation for SquareIDLROIData with vertices outside bounds."""
    square_outside = SquareIDLROIData("test_square_outside", 150, 150, 5)
    with pytest.raises(
        ValueError,
        match=f"This {square_outside.__class__.__name__} object has ROIs with coordinates outside the specified frame. Please check the data.",
    ):
        square_outside.to_napari_shape_vertices_and_type((100, 100))
