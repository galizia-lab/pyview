"""
Unit tests for get_internal_files.py
"""

import pathlib as pl

import pandas as pd

from view.python_core.get_internal_files import (
    get_gdm_doc_df,
    get_internal_flags_def,
    get_internal_fonts_dir,
    get_internal_icons,
    get_internal_jinja_template,
    get_internal_test_files_path,
    get_metadata_definition,
    get_setup_description_dict,
    get_setup_info_df,
)


def test_get_metadata_definition():
    """Test that get_metadata_definition returns a DataFrame with expected structure."""
    metadata_df = get_metadata_definition()
    assert isinstance(metadata_df, pd.DataFrame)
    assert not metadata_df.empty
    assert "Settings Name" in metadata_df.columns
    assert metadata_df.index.name == "LST Name"


def test_get_internal_flags_def():
    """Test that get_internal_flags_def returns a DataFrame with expected structure."""
    flags_df = get_internal_flags_def()
    assert isinstance(flags_df, pd.DataFrame)
    assert not flags_df.empty
    assert "Flag Name" in flags_df.columns


def test_get_internal_fonts_dir():
    """Test that get_internal_fonts_dir returns a valid directory path."""
    fonts_dir = get_internal_fonts_dir()

    fonts_dir_path = pl.Path(fonts_dir)
    assert fonts_dir_path.exists()
    assert fonts_dir_path.is_dir()


def test_get_internal_icons():
    """Test that get_internal_icons returns a valid path for an existing icon."""
    icon_path_str = get_internal_icons("twotone-delete_forever-24px.svg")

    icon_path = pl.Path(icon_path_str)
    assert icon_path.exists()
    assert icon_path.is_file()
    assert icon_path.name == "twotone-delete_forever-24px.svg"


def test_get_internal_jinja_template():
    """Test that get_internal_jinja_template returns a valid path for an existing template."""
    template_path_str = get_internal_jinja_template("tapestry.html")

    template_path = pl.Path(template_path_str)
    assert template_path.exists()
    assert template_path.is_file()
    assert template_path.name == "tapestry.html"


def test_get_setup_info_df():
    """Test that get_setup_info_df returns a DataFrame with expected structure."""
    setup_df = get_setup_info_df()
    assert isinstance(setup_df, pd.DataFrame)
    assert not setup_df.empty
    assert "LE_loadExp" in setup_df.columns


def test_get_setup_description_dict():
    """Test that get_setup_description_dict returns an OrderedDict with expected structure."""
    setup_dict = get_setup_description_dict()
    assert isinstance(setup_dict, dict)
    assert len(setup_dict) > 0
    for key, value in setup_dict.items():
        assert isinstance(key, str)
        assert isinstance(value, int)


def test_get_gdm_doc_df():
    """Test that get_gdm_doc_df returns a DataFrame with expected structure."""
    gdm_df = get_gdm_doc_df()
    assert isinstance(gdm_df, pd.DataFrame)
    assert not gdm_df.empty
    assert "Column name" in gdm_df.columns


def test_get_internal_test_files_path():
    """Test that get_internal_test_files_path returns a valid directory path."""
    test_files_path_str = get_internal_test_files_path()
    test_files_path = pl.Path(test_files_path_str)
    assert test_files_path.exists()
    assert test_files_path.is_dir()
