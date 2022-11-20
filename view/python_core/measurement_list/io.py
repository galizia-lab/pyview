import logging

import pandas as pd
import pathlib as pl


class XLSIO(object):

    def __init__(self):

        super().__init__()

    @classmethod
    def revise_file_name(cls, fle):
        """
        Irrespective of whether the extension of fle is XLS or XLSX, tries to find an existing file with the same file
        prefix and one of the two suffixes. Raises an FileNotFoundError when neither an XLS nor an XLSX file is found.
        :param str|pl.Path fle:
        :return: pl.Path
        """

        possible_suffixes = [".xls", ".xlsx"]

        fle_path = pl.Path(fle)

        if not fle_path.is_file():

            possible_suffixes.remove(fle_path.suffix)
            possible_file = fle_path.with_suffix(possible_suffixes[0])

            if possible_file.is_file():
                fle = possible_file
            else:
                raise FileNotFoundError(f"Could not find {fle} or {possible_file}!")

        return pl.Path(fle)

    @classmethod
    def read(cls, fle, **kwargs):

        fle = cls.revise_file_name(fle)

        df = pd.read_excel(fle, **kwargs).reset_index()

        # the first column may be the index called "index". In that case remove it.
        if "index" in df.columns:
            del df["index"]

        return df

    @classmethod
    def write(cls, df: pd.DataFrame, fle, **kwargs):

        fle_path = pl.Path(fle)
        assert fle_path.suffix == ".xlsx", \
            "VIEW does not support writing measurement lists in XLS format. Please try again writing to XLSX format"
        df.to_excel(fle, **kwargs)


class LSTIO(object):

    def __init__(self):

        super().__init__()

    @classmethod
    def read(cls, fle):
        # 'utf-8' codec, the default, cannot read the umlaute ä etc
        df = pd.read_csv(fle, sep="\t", encoding='latin-1', skipinitialspace=True)

        # and set all column names to lower case
        df.columns = [x.rstrip() for x in df.columns]
        return df

    @classmethod
    def write(cls, df: pd.DataFrame, fle):

        df.to_csv(fle, sep="\t")


def get_format_specific_defs():
    """
    Returns a pandas DataFrame with the columns "IOclass", "relevant column" and "extension" which
    contain information about the IO interfaces of measurement list files.
    :return:
    """

    # the order of definition here is very important. It sets the hierarchy when looking for list files.
    df = pd.DataFrame(columns=["IOclass", "relevant_column", "extension"])
    df.loc["XLS LST format", :] = [XLSIO, "LST Name", ".lst.xls"]
    df.loc["XLSX LST format", :] = [XLSIO, "LST Name", ".lst.xlsx"]
    df.loc["Legacy Text LST format"] = [LSTIO, "LST Name", ".lst"]
    df.loc["XLS FID Settings format"] = [XLSIO, "Settings Name", ".settings.xls"]
    df.loc["XLSX FID Settings format"] = [XLSIO, "Settings Name", ".settings.xlsx"]

    return df


def get_ext_based_values(lst_fle: str):

    io_defs = get_format_specific_defs()

    matches = []
    to_return = []
    for format_name, (io_class, relevant_column, ext) in io_defs.iterrows():

        if lst_fle.endswith(ext):
            matches.append(True)
            to_return.append((io_class, relevant_column, ext))
        else:
            matches.append(False)
            to_return.append(())

    if any(matches):
        return to_return[matches.index(True)]
    else:
        raise NotImplementedError(
            f"The specified measurement list ({lst_fle}) does not have a supported suffix."
            f"The supported suffixes are .lst, .lst.xls, .lst.xlsx, .settings.xls and .settings.xlsx. Sorry!")
