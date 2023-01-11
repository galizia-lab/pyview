from setuptools import setup, find_packages


setup(
    name="view",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    packages=find_packages(exclude=["^\."]),
    package_data={
        "view": [
            "flags_and_metadata_definitions/*.csv",
            "graphics/icons/*.svg",
            "fonts/PixelOperator/*",
            "fonts/OpenSans/*",
            "jinja_templates/*",
            "idl_folder_translation/*template.txt"
        ]
    },
    install_requires=[
        "pandas>=0.24.2",
        "openpyxl>=3.0.3",
        "scipy >=1.2.1",
        "numpy>=1.16.3",
        "matplotlib>=3.0.3",
        "pyyaml>=3.3",
        "Pillow>=6.0.0",
        "moviepy>=1.0.0",
        "scikit-image>=0.15.0",
        "appdirs>=1.4.3",
        # iltis ported to PyQt5 is needed, old iltis built using PyQt4 will not work.
        # Source code available at https://gitlab.inf.uni-konstanz.de/ag-galizia/iltis.
        # See wiki on https://gitlab.inf.uni-konstanz.de/ag-galizia/view for more info
        "iltis@git+https://git@github.com/galizia-lab/ILTIS.git@1.6",
        "tillvisionio@git+https://git@github.com/galizia-lab/tillvisionio.git@1.0",
        "tifffile>=2019.7.26",
        "easygui>=0.98.1",
        "jinja2>=2.10.3",
        "whoosh>=2.7.4",
        "seaborn>=0.10.0",
        "bokeh>=2.0.0",
        "textfsm>=1.1.0",
        "itables>=0.2.1",
        "gekko>=0.2.8",
        "quantities>=0.12.4",
        "neo>=0.9.0",
        "readlif>=0.6.5"
    ],

    entry_points={"console_scripts": ["view = view.gui.start_view_gui:main"]},

    python_requires=">=3.7"
)
