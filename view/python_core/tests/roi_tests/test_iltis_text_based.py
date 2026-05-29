#!/usr/bin/env python3
"""Test script to validate the changes made to Circle and Polygon ROI classes."""

import pytest

from view.python_core.rois.iltis_rois.text_based import (
    CircleILTISROIData,
    PolygonILTISROIData,
)


def test_circle_validation_within_bounds():
    """Test validation for CircleILTISROIData with vertices within bounds."""
    circle = CircleILTISROIData("test_circle", 10.0, 10.0, 5.0)
    vertices, shape_type = circle.to_napari_shape_vertices_and_type((100, 100))
    assert shape_type == "ellipse"
    # Expected vertices for a circle centered at (10, 10) with diameter 5.0
    expected_vertices = [
        [87.5, 7.5],
        [92.5, 7.5],
        [92.5, 12.5],
        [87.5, 12.5],
    ]
    assert vertices == expected_vertices


def test_circle_validation_outside_bounds():
    """Test validation for CircleILTISROIData with vertices outside bounds."""
    circle_outside = CircleILTISROIData(
        "test_circle_outside", 150.0, 150.0, 5.0
    )
    with pytest.raises(
        ValueError,
        match=f"This {circle_outside.__class__.__name__} object has ROIs with coordinates outside the specified frame. Please check the data.",
    ):
        circle_outside.to_napari_shape_vertices_and_type((100, 100))


def test_polygon_validation_within_bounds():
    """Test validation for PolygonILTISROIData with vertices within bounds."""
    polygon = PolygonILTISROIData(
        "test_polygon", [(10, 10), (20, 10), (20, 20), (10, 20)]
    )
    vertices, shape_type = polygon.to_napari_shape_vertices_and_type(
        (100, 100)
    )
    assert shape_type == "polygon"
    # Expected vertices for a polygon with vertices [(10, 10), (20, 10), (20, 20), (10, 20)]
    expected_vertices = [
        [90, 10],
        [90, 20],
        [80, 20],
        [80, 10],
    ]
    assert vertices == expected_vertices


def test_polygon_validation_outside_bounds():
    """Test validation for PolygonILTISROIData with vertices outside bounds."""
    polygon_outside = PolygonILTISROIData(
        "test_polygon_outside",
        [(150, 150), (200, 150), (200, 200), (150, 200)],
    )
    with pytest.raises(
        ValueError,
        match=f"This {polygon_outside.__class__.__name__} object has ROIs with coordinates outside the specified frame. Please check the data.",
    ):
        polygon_outside.to_napari_shape_vertices_and_type((100, 100))
