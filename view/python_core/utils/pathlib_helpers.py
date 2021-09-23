import pathlib as pl
import re


def find_latest_file_matching_pattern(pattern, folder):

    folder_path = pl.Path(folder)

    modification_time_filename_dict = {}

    for child in folder_path.iterdir():

        pattern_matches = re.fullmatch(pattern, child.name, flags=re.I) is not None

        if child.is_file() and pattern_matches:

            modification_time_filename_dict[child.stat().st_mtime] = str(child)

    if len(modification_time_filename_dict) == 0:
        return None
    else:
        mtimes_sorted = sorted(modification_time_filename_dict.keys(), reverse=True)
        return modification_time_filename_dict[mtimes_sorted[0]]





