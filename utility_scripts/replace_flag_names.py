import sys
import pathlib as pl
import pandas as pd

# run example
# python replace_flag_names.py /Users/galizia/Documents/DATA/fidor_play/Or22a_GC6m /Users/galizia/Documents/Code/Git_code/pyview/view/flags_and_metadata_definitions/view_flags_renaming_2021.csv

rename_directory = '/Users/galizia/Documents/DATA/fidor_play/Or22a_GC6m' 
rename_instructions = '/Users/galizia/Documents/Code/Git_code/pyview/view/flags_and_metadata_definitions/view_flags_renaming_2021.csv'

def main(fle_or_dir, replacement_map_csv):

    map_df = pd.read_csv(replacement_map_csv)

    path = pl.Path(fle_or_dir)

    if path.is_file():
        files = [path]
    elif path.is_dir():
        files = path.rglob("*")
    else:
        raise FileNotFoundError(f"The specified path is neither a file nor a directory!\n{fle_or_dir}")

    for file in files:
        if file.is_file() \
                and file != pl.Path(replacement_map_csv) \
                and not file.name.startswith(".")\
                and str(file).find(".git") < 0:

            changes_made = False
            with open(file, "r+") as fh:
                try:
                    s_read = fh.read()
                    s = f"{s_read:s}"
                    for ind, row in map_df.iterrows():
                        s = s.replace(row["Old Flag Name"], row["Flag Name"])
                        s = s.replace(row["Old Flag Subgroup"], row["Flag Subgroup"])
                    if s != s_read:
                        changes_made = True
                except UnicodeDecodeError as ucde:
                    pass  # happens if the file is not a text file encoded in unicode

            if changes_made:
                file.unlink()

                with open(file, "w") as fh:
                    fh.write(s)


if __name__ == '__main__':

    # assert len(sys.argv) == 3, \
    #     f"Could not understand command. Please use as\n" \
    #     f"python {__file__} <path to file or directory> <CSV file containing replacement map>"
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        main(rename_directory, rename_instructions)

