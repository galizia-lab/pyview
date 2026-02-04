# napari-pyview

[![License BSD-3](https://img.shields.io/pypi/l/napari-pyview.svg?color=green)](https://github.com/galizia-lab/napari-pyview/raw/main/LICENSE)
[![PyPI](https://img.shields.io/pypi/v/napari-pyview.svg?color=green)](https://pypi.org/project/napari-pyview)
[![Python Version](https://img.shields.io/pypi/pyversions/napari-pyview.svg?color=green)](https://python.org)
[![tests](https://github.com/galizia-lab/napari-pyview/workflows/tests/badge.svg)](https://github.com/galizia-lab/napari-pyview/actions)
[![codecov](https://codecov.io/gh/galizia-lab/napari-pyview/branch/main/graph/badge.svg)](https://codecov.io/gh/galizia-lab/napari-pyview)
[![napari hub](https://img.shields.io/endpoint?url=https://api.napari-hub.org/shields/napari-pyview)](https://napari-hub.org/plugins/napari-pyview)
[![npe2](https://img.shields.io/badge/plugin-npe2-blue?link=https://napari.org/stable/plugins/index.html)](https://napari.org/stable/plugins/index.html)
[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)

A plugin for using pyView from within napari, including adding data from pyView to napari, exporting ROIs from napari, etc.

----------------------------------

This [napari] plugin was generated with [copier] using the [napari-plugin-template] (None).

<!--
Don't miss the full getting started guide to set up your new package:
https://github.com/napari/napari-plugin-template#getting-started

and review the napari docs for plugin developers:
https://napari.org/stable/plugins/index.html
-->

## Installation

1. Install napari with conda ([guide](https://napari.org/stable/tutorials/fundamentals/installation.html))
2. Start this napari by running "napari" from within the conda environment created for it in Step 1.
3. Installing the plugin is via napari plugin manager. Please read this [guide](https://napari.org/stable/plugins/start_using_plugins/finding_and_installing_plugins.html#installing-plugins-with-napari) first. 
4. In napari plugin manager, select "PyPI" in the "Install" dropdown and provide the following manual input `git+https://git@github.com/galizia-lab/pyview.git@dev#subdirectory=napari-pyview`.

```
NOTE:
---
You could also pull from other branches of pyview by replaced "dev" with other branches in the URL above.
``` 


## Installation for development
1. Follow steps 1-3 from "Installation" above
2. Download source code of PyView
3. Open terminal and activate the conda environment created for napari (`conda activate ...`)
4. Change directory into the source code of PyView downloaded (`cd ..../pyview`)
5. Install plugin in editable mode (`pip install -e ./napari-pyview`)

```
NOTE:
---
With the above editable install, the package view is not installed in editable mode.
If required, navigate into pyview source code and install with `pip install -e ./`
```

## Debugging
Run the file "napari-pyview/launch_napari_with_pyview.py" with pdb/IDE in debugger mode. See [this guide](https://napari.org/stable/plugins/building_a_plugin/debug_plugins.html) for more info.


## Contributing

Contributions are very welcome.

## License

Distributed under the terms of the [BSD-3] license,
"napari_pyview" is free and open source software

## Issues

If you encounter any problems, please [file an issue] along with a detailed description.

[napari]: https://github.com/napari/napari
[copier]: https://copier.readthedocs.io/en/stable/
[@napari]: https://github.com/napari
[MIT]: http://opensource.org/licenses/MIT
[BSD-3]: http://opensource.org/licenses/BSD-3-Clause
[GNU GPL v3.0]: http://www.gnu.org/licenses/gpl-3.0.txt
[GNU LGPL v3.0]: http://www.gnu.org/licenses/lgpl-3.0.txt
[Apache Software License 2.0]: http://www.apache.org/licenses/LICENSE-2.0
[Mozilla Public License 2.0]: https://www.mozilla.org/media/MPL/2.0/index.txt
[napari-plugin-template]: https://github.com/napari/napari-plugin-template

[napari]: https://github.com/napari/napari
[tox]: https://tox.readthedocs.io/en/latest/
[pip]: https://pypi.org/project/pip/
[PyPI]: https://pypi.org/
