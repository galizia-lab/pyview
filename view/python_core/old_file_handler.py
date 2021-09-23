import pathlib as pl
import datetime
import pandas as pd
import typing
import logging
from .measurement_list.io import get_ext_based_values
import shutil


def get_old_file_handler(fle: str):

    lst_path = pl.Path(fle)
    if lst_path.is_file():
        try:
            return OldFileHandlerMeasurementList(fle)
        except NotImplementedError as nie:
            return OldFileHandler(fle)
    else:
        return OldFileHandlerBlank()


class OldFileHandlerBlank(object):

    def __init__(self):
        super().__init__()
        pass

    def backup(self):

        pass

    def write_old_values(self, df, columns, measu_col_name: str = "Measu", label_col_name: str = "Label"):

        return df


class OldFileHandler(OldFileHandlerBlank):

    def __init__(self, fle: str):

        super().__init__()
        self.fle = fle

    def backup(self):

        lst_fle_path = pl.Path(self.fle)
        backup_path = \
            lst_fle_path.with_suffix(f".{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{lst_fle_path.suffix}")

        if backup_path.is_file():
            backup_path.unlink()

        shutil.copy(src=self.fle, dst=str(backup_path))
        logging.getLogger("VIEW").info(f"Backing up file to {backup_path}")


class OldFileHandlerMeasurementList(OldFileHandler):

    def __init__(self, lst_fle: str):

        super().__init__(lst_fle)

        self.io_class, _, _ = get_ext_based_values(lst_fle)
        self.old_lst_df = self.io_class.read(lst_fle)
        if "index" in self.old_lst_df.columns:
            del self.old_lst_df["index"]

    def write_old_values(self, df, columns: typing.Iterable[str], measu_col_name: str = "Measu",
                         label_col_name: str = "Label"):
        """
        For every column in <columns>, the values in the column of old measurement file, if it exists, will be copied
        into df
        :param df: pandas.DataFrame
        :param columns: iterable of strings
        :param measu_col_name: string, name of the "Measu" column
        :param label_col_name: string, name of the "Label" column
        :return: pandas.DataFrame
        """

        columns = list(columns)

        if measu_col_name not in columns:
            columns.append(measu_col_name)

        # restrict columns to be the intersection of
        columns = set(columns).intersection(set(self.old_lst_df.columns.values))

        mask = self.old_lst_df[measu_col_name].apply(lambda x: x in df[measu_col_name].values)
        indices2use = mask.index.values[mask.values].tolist()

        old_df_subset = self.old_lst_df.reindex(index=indices2use, columns=columns).set_index(measu_col_name)

        df_temp = df.set_index(measu_col_name)

        combined_df = df_temp.combine(old_df_subset, func=lambda s1, s2: s2, overwrite=False)

        return combined_df.reset_index()


def backup_if_existing(filename):

    old_file_handler = get_old_file_handler(filename)
    old_file_handler.backup()