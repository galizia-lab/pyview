# To be run with ipdb for debugging
# launches napari and loads plugin

# launch_napari.py
from napari import Viewer, run
from napari_pyview import NapariPyViewWidget

viewer = Viewer()
dock_widget, plugin_widget = viewer.window.add_plugin_dock_widget(
    "napari_pyview", None # "napari_pyview.NapariPyViewWidget"
)
# Optional steps to setup your plugin to a state of failure
# E.g. plugin_widget.parameter_name.value = "some value"
# E.g. plugin_widget.button.click()
run()