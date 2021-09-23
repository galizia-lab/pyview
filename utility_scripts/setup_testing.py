from PyQt5.QtCore import QSettings
from easygui import diropenbox, ynbox, msgbox
import pathlib as pl

from view.gui.application_settings import get_view_qsettings_manager


def main():
    settings = get_view_qsettings_manager()
    existing_test_data_path_str = None
    if settings.contains("view_test_data_path"):
        existing_test_data_path_str = settings.value("view_test_data_path")
        existing_test_data_path = pl.Path(existing_test_data_path_str)
        if existing_test_data_path.is_dir() and len(list(existing_test_data_path.iterdir())):
            ch = ynbox(
                title="Test data found!",
                msg=f"View has been previously configured to use the folder below for storing test data. "
                    f"This folder exists and is not empty, hence it most likely contains the correct test data. "
                    f"What would you like to do?"
                    f"\n\n{existing_test_data_path_str}",
                choices=["Use a new path and download test data again (~3.3GiB)", "Use the same path as above"],
                default_choice="Use the same path as above",
                cancel_choice="Use the same path as above"
            )

            if ch:
                existing_test_data_path_str = None

        else:
            existing_test_data_path_str = None

    if existing_test_data_path_str is None:
        msgbox(
            title="Info",
            msg="Please choose a folder in the next dialog for storing VIEW test data. Since it is ~3.3GiB is size, "
                "we recommend creating a new folder for it")
        file = diropenbox(title="Please choose a folder for storing VIEW test data")

        if file is None:
            raise IOError("User Abort!")

        settings.setValue("view_test_data_path", file)
        existing_test_data_path_str = file

        # raise NotImplementedError  # TODO download view test data to this folder

    msgbox(
        title="View test data path",
        msg=f"View has been configured to use data in the following folder for testing:"
            f"\n\n{existing_test_data_path_str}")


if __name__ == '__main__':

    main()
