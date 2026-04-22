import napari

from view.python_core.rois import SquareIDLROIData
from view.python_core.rois.iltis_rois.text_based import (
    CircleILTISROIData,
    PolygonILTISROIData,
)


def add_roi_datas_to_napari(
    napari_viewer: "napari.viewer.Viewer",
    roi_data: dict[
        str, CircleILTISROIData | PolygonILTISROIData | SquareIDLROIData
    ],
    frame_size: tuple[int, int],
    edge_color: str | tuple = "red",
    edge_width: float = 1.0,
):
    """
    Add ROI data objects to napari viewer as shapes with customizable appearance.

    :param napari_viewer: napari viewer instance
    :param roi_data: Dictionary mapping ROI labels to ROI data objects to add
    :param frame_size: Size of the frame (height, width), with wich ROI is associated
    :param edge_color: Color for shape edges (napari color format)
    :param edge_width: Width of shape edges
    """
    shape_vertices = []
    shape_types = []

    for _roi_label, roi in roi_data.items():
        vertices, shape_type = roi.to_napari_shape_vertices_and_type(
            frame_size
        )
        shape_vertices.append(vertices)
        shape_types.append(shape_type)

    # Add shapes to viewer if any exist
    if shape_vertices:
        napari_viewer.add_shapes(
            shape_vertices,
            shape_type=shape_types,
            name="ROI Shapes",
            face_color="transparent",
            edge_color=edge_color,
            edge_width=edge_width,
            features={"label": list(roi_data.keys())},
            text="label",
        )
