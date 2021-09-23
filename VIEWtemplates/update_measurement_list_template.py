from view.python_core.measurement_list import MeasurementList
from view.python_core.flags import FlagsManager
import easygui
import pandas as pd
import logging
import pathlib as pl

logging.basicConfig(level=logging.INFO)

# ------------------- Some parameters about experimental setup, data structure and output file type --------------------
# 3 for single wavelength Till Photonics Measurements
# 4 for two wavelength Till Photonics Measurements
# 20 for Zeiss Confocal Measurements
LE_loadExp = 3

# Mother of all Folders of your dataset
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_MotherOfAllFolders = r""

# path of the "Data" folder in VIEW organization containing the data
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_Datapath = r""

# path of the "Lists" folder in VIEW organization containing the list files
# On Windows, if you copy paths from the file explorer, make sure the string below is always of the form r"......"
STG_OdorInfoPath = r""

# Choose measurement list output extension among ".lst", ".lst.xls", ".settings.xls"
# please use ".lst.xls" when converting old list files
measurement_output_extension = ".lst.xls"

# ----------------------------------------------------------------------------------------------------------------------

# ----------------- A function used to add new columns to the list file ------------------------------------------------
# ----------------- This function indicates how to add new entries to a row --------------------------------------------
# ----------------- possibly using other existing row values -----------------------------------------------------------
# ----------------- The same logic is apply to all rows to create entire new columns -----------------------------------


def custom_func(list_row: pd.Series, animal_tag: str) -> pd.Series:

    # NOTE: take care when modifying column values that already exist. Old values will be lost!

    # these changes are always required when updating a .LST file used with IDL
    # ------------------------------------------------------------------------------------------------------------------
    # update to comment to indicate that the list has been imported for use with pyVIEW
    list_row["Comment"] += "_2pyVIEW"

    stim_cols = ["StimON", "StimOFF", "Stim2ON", "Stim2OFF"]

    # frames in IDL .LST files were numbered 1, 2, 3... In pyVIEW they are numbered 0, 1, 2....
    for stim_col in stim_cols:

        if stim_col in list_row:
            list_row[stim_col] -= 1
    # ------------------------------------------------------------------------------------------------------------------

    # Examples:
    # new_columns["Stim2ON"] = 25
    # list_row["Odour"] = get_odor_from_label(list_row["Label"])
    # if list_row["Measu"]
    # get Odor from another file based on the value of <animal_tag> and list_row["Label"]

    return list_row

# ----------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":

    # initialize a FlagsManager object with values specified above
    flags = FlagsManager()
    flags.update_flags({"STG_MotherOfAllFolders": STG_MotherOfAllFolders,
                        "STG_OdorInfoPath": STG_OdorInfoPath,
                        "STG_Datapath": STG_Datapath})

    # open a dialog for choosing existing list files
    existing_measurement_list_files = easygui.fileopenbox(
        msg="Choose one or more measurement list files to update", multiple=True,
        default=f"{flags.get_list_dir_str()}/*"
    )

    # make sure some files were chosen
    assert len(existing_measurement_list_files) > 0, IOError("No files were chosen!")

    for existing_measurement_list_file in existing_measurement_list_files:

        # create a measurement list object
        measurement_list = MeasurementList.create_from_lst_file(
            lst_fle=existing_measurement_list_file, LE_loadExp=LE_loadExp)

        # parse animal tag from measurement list file name
        animal_tag = measurement_list.get_STG_ReportTag()

        # inform user if no usable measurements were found
        if len(measurement_list.get_measus()) == 0:
            logging.info(f"No usable measurements found in {existing_measurement_list_file}. "
                         f"Not updating it.")
        else:

            # apply custom modifications
            measurement_list.update_from_custom_func(custom_func=custom_func, animal_tag=animal_tag)

            # set analyze to 0 if raw data files don't exist
            flags.update_flags({"STG_ReportTag": animal_tag})
            measurement_list.sanitize_based_on_loading(flags)

            # create the output file name
            existing_measurement_list_file_path = pl.Path(existing_measurement_list_file)
            ml_name_stem = existing_measurement_list_file_path.name.split(".")[0]
            output_file_path \
                = existing_measurement_list_file_path.parent / f"{ml_name_stem}{measurement_output_extension}"

            # write measurement file to list
            measurement_list.write_to_lst_file_cross_format(
                output_lst_file=str(output_file_path), backup_current_file=True
                )

            existing_measurement_list_file_path.unlink()
