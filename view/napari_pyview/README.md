# napari-pyview

A plugin for using pyView from within napari, including adding data from pyView to napari, exporting ROIs from napari,
etc.

----------------------------------

## Installation

1. Install napari with conda or uv ([guide](https://napari.org/stable/tutorials/fundamentals/installation.html)). 
2. Start this napari by running "napari" from within the conda/uv environment created for it in Step 1.
3. Installing the plugin is via napari plugin manager. Please read
   this [guide](https://napari.org/stable/plugins/start_using_plugins/finding_and_installing_plugins.html#installing-plugins-with-napari)
   first.
4. In napari plugin manager, select "PyPI" in the "Install" dropdown and provide the following manual input
   `git+https://git@github.com/galizia-lab/pyview.git@dev`.

```
NOTE:
---
You could also pull from other branches of pyview by replacing "dev" with other branches in the URL above.
``` 

## Installation for development

1. Follow steps 1-3 from "Installation" above
2. Download source code of PyView
3. [if using conda] Open terminal and activate the conda environment created for napari (`conda activate ...`)
4. Change directory into the source code of PyView downloaded (`cd ..../pyview`)
5. Install plugin in editable mode (when using conda: `pip install -e "./[dev]"`, when using uv: `uv pip install -e "./[dev]"`)

## Debugging

1. If the bug does not involve napari, run the file "view/napari_pyview/run_plugin_independently.py" to start the plugin
   outside napari. You could then debug this file using ipdb/debugger of an IDE.
2. If the bug involves napari, run the file "view/napari_pyview/launch_napari_with_pyview.py" to start napari and the
   plugin together. You could then debug this file using ipdb/debugger of an IDE.

## Contributing

Contributions are very welcome.

## License

Distributed under the terms of the [BSD-3] license,
"napari_pyview" is free and open source software

## Issues

If you encounter any problems, please file an issue in our [github repository](https://github.com/galizia-lab/pyview#)
along with a detailed description.
