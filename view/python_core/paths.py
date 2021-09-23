import pathlib as pl
from itertools import product


def check_for_existing_dbb1(data_dir_path, dbb1, extension, animal_tag):

    dbb1 = str(dbb1).replace("\\", "/")  # dbb1 for settings files generated in windows can contain "\\"

    without_ORline_value_trailing = "_".join(animal_tag.split("_")[:-1])
    possible_paths = [data_dir_path / dbb1,
                      data_dir_path / f"{dbb1}{extension}",
                      data_dir_path / animal_tag / dbb1,
                      data_dir_path / animal_tag / f"{dbb1}{extension}",
                      data_dir_path / f"{animal_tag}{extension}" / f"{dbb1}{extension}",
                      # for till vision setups, structure could be
                      # {STG_Datapath} / {STG_ReportTag} / {STG_ReportTag}.pst / {dbb1}.pst
                      data_dir_path / animal_tag / f"{animal_tag}{extension}" / dbb1,
                      data_dir_path / animal_tag / f"{animal_tag}{extension}" / f"{dbb1}{extension}",
                      data_dir_path / without_ORline_value_trailing / dbb1,
                      data_dir_path / without_ORline_value_trailing / f"{dbb1}{extension}",
                      data_dir_path / without_ORline_value_trailing / f"{animal_tag}{extension}" / dbb1,
                      data_dir_path / without_ORline_value_trailing / f"{animal_tag}{extension}" / f"{dbb1}{extension}"
                      ]

    # resolution required for cross OS compatibility, i.e., for example, when settings files was generated in Windows
    # and used on linux/mac
    existences = [x.resolve(strict=False).is_file() for x in possible_paths]

    if any(existences):
        existing_path = possible_paths[existences.index(True)]
        return str(existing_path)
    else:
        return None


def get_existing_raw_data_filename(flags, dbb, extensions):

    possible_filenames = []

    # check if dbb1 is absolute and file
    dbb1_path = pl.Path(dbb)
    if dbb1_path.is_absolute() and dbb1_path.is_file():
        possible_filenames.append(str(dbb))

    if not flags.is_flag_state_default("STG_ReportTag"):
        animal_tag = flags["STG_ReportTag"]

        if not flags.is_flag_state_default("STG_Datapath"):
            data_dir_path = pl.Path(flags["STG_Datapath"])

            for extension in extensions:
                # check if dbb1 can be interpreted relative to data directory
                possible_existing_filename = check_for_existing_dbb1(
                    data_dir_path=data_dir_path, dbb1=dbb, extension=extension, animal_tag=animal_tag)
                possible_filenames.append(possible_existing_filename)

        if not flags.is_flag_state_default("STG_MotherOfAllFolders"):

            for extension in extensions:
                # check if dbb1 can be interpreted relative to mother of all folders directory
                moaf = pl.Path(flags["STG_MotherOfAllFolders"])
                possible_existing_filename = check_for_existing_dbb1(data_dir_path=moaf, dbb1=dbb, extension=extension,
                                                                     animal_tag=animal_tag)
                possible_filenames.append(possible_existing_filename)

    hits = [x is not None for x in possible_filenames]
    if any(hits):
        return possible_filenames[hits.index(True)]
    else:
        raise FileNotFoundError(f"Could not find raw file with dbb1={dbb} in {flags['STG_Datapath']}")


def convert_to_path_for_current_os(path_str):
    """
    If path_str is absolute and exists, returns a path object initialized with it. Raises an error if it is absolute
    but for the wrong operating system. If it is not absolute, returns the relative path with the separators of the
    current operating system
    :param path_str: pathlib.Path
    :return:
    """

    possible_posix_path = pl.PurePosixPath(path_str)
    possible_win_path = pl.PureWindowsPath(path_str)

    if possible_posix_path.is_absolute() or possible_win_path.is_absolute():

        possible_path = pl.Path(path_str)
        # if it exists
        if possible_path.exists():
            return possible_path

        else:
            raise OSError(f"Either the specified path {path_str} does not exist or "
                          f"cannot be interpreted for the current operating system")

    else:
        # PureWindowsPath interprets paths with only posix separators, only windows separators or a mix of the two
        return pl.Path(possible_win_path)


def check_get_file_existence_in_folder(folder, stems, possible_extensions):
    """
    Checks if the file folder / {stem}{ext} exists for all combinations of stem in <stems> and ext in
    <possible_extensions>. If any exist, returns the one at the top of the hierarchy, where the order of elements
    decides the hierarchy within <stems> and <possible_extensions> and <stems> having higher precedence than
    <possible_extensions>.
    :param folder: str, full path of the folder
    :param stems: iterable of strings
    :param possible_extensions: iterable of strings, including "."
    :return: full file path of an existing file or None, if none exist
    """

    folder_path = pl.Path(folder)
    paths = [folder_path / f"{stem}{ext}" for stem, ext in product(stems, possible_extensions)]
    existences = [x.is_file() for x in paths]

    if any(existences):
        return str(paths[existences.index(True)])
    else:
        return None
