import pathlib as pl
import typing

if typing.TYPE_CHECKING:
    import napari
import qtpy.compat
from matplotlib.colors import rgb2hex

from view.napari_pyview.napari_utils.image_format_utils import (
    convert_view_image_to_tif_2D,
)
from view.python_core.flags import FlagsManager
from view.python_core.rois import SquareIDLROIData
from view.python_core.rois.iltis_rois.text_based import (
    CircleILTISROIData,
    PolygonILTISROIData,
)
from view.python_core.rois.iltis_rois.tiff_based import SpatialFootprintROIData
from view.python_core.rois.roi_io import get_roi_io_class_from_file_path
from view.python_core.utils.colors import interpret_flag_SO_MV_colortable


class NapariShapesLayerViewIO:
    """
    Class for defining IO operations between VIEW ROI data and napari shapes layer.
    """

    @staticmethod
    def get_kwargs_for_adding_to_napari(view_flags: FlagsManager):
        """
        Get kwargs for adding ROI shapes to napari viewer.

        :param view_flags: FlagsManager instance
        :return: Dictionary of kwargs
        """

        # Get edge color from SO_fgColor flag
        _, _, edge_color = interpret_flag_SO_MV_colortable(
            view_flags["SO_MV_colortable"],
            bg_color=view_flags["SO_bgColor"],
            fg_color=view_flags["SO_fgColor"],
        )

        # Convert matplotlib color to hex format
        edge_color_napari = rgb2hex(edge_color[:3])

        return {"edge_color": edge_color_napari, "edge_width": 1}

    @staticmethod
    def add_roi_datas_to_napari(
        napari_viewer: "napari.viewer.Viewer",
        roi_data: list[
            CircleILTISROIData | PolygonILTISROIData | SquareIDLROIData
        ],
        frame_size: tuple[int, int],
        edge_color: str | tuple = "red",
        edge_width: float = 1.0,
        layer_name: str = "ROI Shapes",
    ):
        """
        Add ROI data objects to napari viewer as shapes with customizable appearance.

        :param napari_viewer: napari viewer instance
        :param roi_data: list of  ROI data objects to add
        :param frame_size: Size of the frame (width, height), with which ROI is associated
        :param edge_color: Color for shape edges (napari color format)
        :param edge_width: Width of shape edges
        :param layer_name: Name of the layer to which shapes are added
        """
        shape_vertices = []
        shape_types = []

        for roi in roi_data:
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
                name=layer_name,
                face_color="transparent",
                edge_color=edge_color,
                edge_width=edge_width,
                features={"label": [roi.label for roi in roi_data]},
                text="label",
            )


class NapariLabelsLayerViewIO:
    """
    Class for defining IO operations between VIEW ROI data and napari labels layer.
    """

    @staticmethod
    def get_kwargs_for_adding_to_napari(view_flags: FlagsManager):
        """
        Get kwargs for adding ROI labels to napari viewer.

        :param view_flags: FlagsManager instance
        :return: Dictionary of kwargs
        """
        return {}

    @staticmethod
    def add_roi_datas_to_napari(
        napari_viewer: "napari.viewer.Viewer",
        roi_data: list[SpatialFootprintROIData],
        frame_size: tuple[int, int],
        layer_name: str = "ROI Labels",
    ):
        """
        Add ROI data objects to napari viewer as labels.

        :param napari_viewer: napari viewer instance
        :param roi_data: list of  ROI data objects to add
        :param frame_size: Size of the frame (width, height), with which ROI is associated
        :param layer_name: Name of the layer to which labels are added
        """

        for roi in roi_data:
            mask_view_format = roi.get_boolean_mask(frame_size)

            mask_tif_format = convert_view_image_to_tif_2D(mask_view_format)

            napari_viewer.add_labels(
                mask_tif_format, name=f"{layer_name}_{roi.label}"
            )


class ViewRoiCoorIOManager:
    """
    Class for managing IO operations between VIEW ROI/COOR data and napari viewer.
    """

    @classmethod
    def get_default_dir(cls, view_flags: FlagsManager) -> str:

        return view_flags.get_coor_dir_str()

    @classmethod
    def get_file_type_description(cls) -> str:

        return "ROI/COOR File"

    @classmethod
    def get_file_extension_napari_io_object_mapping(
        cls,
    ) -> dict[
        str, type[NapariShapesLayerViewIO] | type[NapariLabelsLayerViewIO]
    ]:

        return {
            ".roi": NapariShapesLayerViewIO,
            ".coor": NapariShapesLayerViewIO,
            ".roi.tif": NapariLabelsLayerViewIO,
        }

    @classmethod
    def get_file_extensions(cls) -> list[str]:

        return list(cls.get_file_extension_napari_io_object_mapping().keys())

    @classmethod
    def get_fileopendialog_filtertext(cls) -> str:

        file_type_desc = cls.get_file_type_description()
        file_extensions = cls.get_file_extensions()

        filter_text = (
            f"{file_type_desc} ({' '.join(f'*{x}' for x in file_extensions)})"
        )

        return filter_text

    @classmethod
    def ask_get_file(cls, view_flags: FlagsManager) -> str:
        """
        Open a dialog to select a ROI/COOR file using QFileDialog.getOpenFileName.
        :param view_flags: FlagsManager instance
        :return: The chosen file path, or None if no file was selected
        """
        default_dir = cls.get_default_dir(view_flags)
        file_type_desc = cls.get_file_type_description()
        filter_text = cls.get_fileopendialog_filtertext()

        file_path, _ = qtpy.compat.getopenfilename(
            None,
            f"Select {file_type_desc}",
            default_dir,
            filter_text,
        )
        return file_path

    @classmethod
    def get_napari_shapes_labels_io_class(
        cls,
        file_path: str,
    ) -> type[NapariShapesLayerViewIO] | type[NapariLabelsLayerViewIO]:
        """
        Get the appropriate IO class for napari shapes or labels based on file extension.

        :param file_path: Path to the file to be loaded
        :return: IO class for napari shapes or labels
        """

        extension_io_mapping = (
            cls.get_file_extension_napari_io_object_mapping()
        )

        for extension, io_class in extension_io_mapping.items():
            if file_path.endswith(extension):
                return io_class

        raise ValueError(f"Unsupported file extension: {file_path}")

    @classmethod
    def get_ask_file_add_to_napari(
        cls,
        napari_viewer: "napari.viewer.Viewer",
        view_flags: FlagsManager,
        frame_size: tuple[int, int],
    ) -> tuple[list | None, str | None]:
        """
        Open a dialog to select a ROI/COOR file, load the ROI data, and add it to the napari viewer.

        :param napari_viewer: The napari viewer instance
        :param view_flags: FlagsManager instance
        :param frame_size: The size of the frame to be used for the ROI data (width, height)
        """

        # Open file dialog, ask and get file path of a  ROI/COOR file

        roi_file_path = cls.ask_get_file(view_flags)
        if not roi_file_path:
            return None, None

        # Get ROI IO class based on chosen roi file
        roi_io_class = get_roi_io_class_from_file_path(roi_file_path)

        # Load ROI data
        roi_data_list = roi_io_class.read_roi_file(roi_file_path, view_flags)

        # Get Napari Shapes/Labels layer from file name
        napari_shapes_labels_io_class = cls.get_napari_shapes_labels_io_class(
            roi_file_path
        )

        # Get extra kwargs for Napari shapes/labels layer, example get edge width and color for shapes
        extra_kwargs = (
            napari_shapes_labels_io_class.get_kwargs_for_adding_to_napari(
                view_flags=view_flags
            )
        )

        # add roi data to napari
        napari_shapes_labels_io_class.add_roi_datas_to_napari(
            napari_viewer,
            roi_data_list,
            frame_size=frame_size,
            # frame_size is shape of image in view format
            layer_name=pl.Path(roi_file_path).name,
            **extra_kwargs,
            # for example looks up edge color of shapes from flags
        )

        return roi_data_list, roi_file_path


class ViewAreaIOManager(ViewRoiCoorIOManager):
    """
    Class for managing IO operations between VIEW AREA data and napari viewer.
    """

    @classmethod
    def get_default_dir(cls, view_flags: FlagsManager) -> str:
        """
        Get the default directory for the AREA file.

        :param view_flags: FlagsManager instance
        """

        return view_flags.get_area_dir_str()

    @classmethod
    def get_file_type_description(cls) -> str:

        return "VIEW AREA File"

    @classmethod
    def get_file_extension_napari_io_object_mapping(
        cls,
    ) -> dict[str, type[NapariLabelsLayerViewIO, NapariShapesLayerViewIO]]:

        return {
            ".Area": NapariLabelsLayerViewIO,
            ".area.tif": NapariLabelsLayerViewIO,
            ".roi": NapariShapesLayerViewIO,
        }
