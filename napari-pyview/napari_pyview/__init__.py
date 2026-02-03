try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

from .main_pyview_widget_napari import NapariPyViewWidget

__all__ = (
    "NapariPyViewWidget"
)
