from view.python_core.flags import FlagsManager
from view.python_core.utils.colors import interpret_flag_SO_MV_colortable
from common import get_example_data_root_path
from view.idl_translation_core.IDL import createPalette
import numpy as np
from matplotlib.colors import Colormap
import os
import tempfile
import pathlib as pl


def test_flags_internal():
    """
    Testing the initialization of flags with default values from definition csv
    """

    flags = FlagsManager()


def test_SO_MV_SO_MV_colortable_flags():
    """
    Testing setting SO_MV_SO_MV_colortable values
    """

    flags = FlagsManager()

    values = [11, 12, 13, 14, "jet", "autumn"]

    for value in values:
        flags.update_flags({"SO_MV_SO_MV_colortable": value})


def test_flag_fails():
    """
    Testing cases for which  flag initialization must fail
    """

    flags = FlagsManager()

    must_fail = [["SO_MV_SO_MV_colortable", True],  # expected value is int or str, bool given
                 ["VIEW_VIEW_batchmode", "whatever"],  # expected value is bool, string given
                 ["VIEW_VIEW_batchmode", 15],  # expected value is bool, incompatible integer given
                 ["LE_loadExp", "whatever"]  # expected value is integer, incompatible string given
                 ]

    for k, v in must_fail:
        try:
            flags.update_flags({k: v})
        except AssertionError as ase:
            pass


def test_flags_read_write():
    """
    Testing flags reading and writing functionalities using internal flags in FakeData test dataset
    """

    flags = FlagsManager()

    data_root = get_example_data_root_path()

    moaf_path = data_root / "FakeData"

    flags.update_flags({"STG_MotherOfAllFolders": str(moaf_path)})

    STG_flags = {"STG_OdorReportPath": "IDLoutput",
                 "STG_OdorInfoPath": "Lists",
                 "STG_OdormaskPath": "Coor",
                 "STG_Datapath": "data",
                 "STG_ProcessedDataPath": "ProcessedData",
                 "STG_OdorAreaPath": "Areas"
                 }

    flags.update_flags(STG_flags)

    flags_temp = FlagsManager()
    flags_temp.clear_flags()

    temp_yml_path = moaf_path / f"{tempfile.gettempprefix()}.yml"
    temp_yml_filename = str(temp_yml_path)
    flags.write_flags_to_yml(temp_yml_filename)
    flags_temp.read_flags_from_yml(temp_yml_filename)

    for flag_name in flags_temp.compound_path_flags:
        if flag_name in flags_temp.flags:
            path = pl.Path(flags_temp[flag_name])
            if path.is_absolute():
                flags_temp.update_flags({flag_name: os.path.relpath(path, flags_temp["STG_MotherOfAllFolders"])})

    assert len(flags_temp.flags) == len(flags.flags)
    assert len(set(flags_temp.flags.keys()) - set(flags.flags.keys())) == 0
    assert all(flags.flags[x] == flags_temp.flags[x] for x in flags.flags.keys())
    temp_yml_path.unlink()


def test_interpret_flag_SO_MV_SO_MV_colortable():
    """
    Testing view.python_core.flags.interpret_flag_SO_MV_SO_MV_colortable
    """

    valid_SO_MV_SO_MV_colortable_values = [11, 12, 13, 14, "winter", "cool", "jet"]

    invalid_SO_MV_SO_MV_colortable_value = [50, 150, "whatever", "notacolormap"]

    for value in valid_SO_MV_SO_MV_colortable_values:

        cmap, bg, fg = interpret_flag_SO_MV_colortable(value)

        assert issubclass(cmap.__class__, Colormap)
        assert len(bg) in (3, 4)
        assert len(fg) in (3, 4)

        if type(value) is int:

            original_cmap = createPalette(value)

            original_cols = original_cmap(np.linspace(0, 1, original_cmap.N))

            interpreted_cols = cmap(np.linspace(0, 1, original_cmap.N - 2))

            assert np.allclose(original_cols[1:-1, :], interpreted_cols)

    for value in invalid_SO_MV_SO_MV_colortable_value:

        it_failed = False
        try:
            interpret_flag_SO_MV_colortable(value)
        except ValueError as ve:
            it_failed = True
        except NotImplementedError as se:
            it_failed = True

        assert it_failed


if __name__ == "__main__":
    # test_flag_fails()
    test_flags_read_write()

