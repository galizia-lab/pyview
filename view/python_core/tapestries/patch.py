import typing
import numpy as np
import pandas as pd
import pathlib as pl
from PIL import Image
from .tapestry_config import TapestryConfig
import pprint


def sanitize_formats(formats: typing.Iterable[str]) -> typing.Iterable[str]:
    formats = [x.lower().lstrip(".") for x in formats]

    if "png" not in formats:
        formats.append("png")

    return formats


class EmptyPatch(object):

    def __init__(self):

        super().__init__()
        self.image_relative_path = "Excluded"
        self.text_below = ""
        self.text_right_bottom = ""
        self.text_right_top = ""
        self.animal = "Invalid"
        self.flag_changes = "Invalid"
        self.movie_file = None


class Patch(EmptyPatch):

    def __init__(self, overview: np.ndarray, data_limits: typing.Iterable[float],
                 measurement_row: pd.Series, animal: str, measu: int, flag_changes: dict,
                 ):

        super().__init__()
        self.overview = overview

        self.pil_image = Image.fromarray(overview)
        self.data_limits = data_limits

        self.text_right_bottom, self.text_right_top = [f"{x:.3g}" for x in data_limits]

        self.measurement_row = measurement_row

        self.text_below = "uninitialized"

        self.image_relative_path = "uninitialized"

        self.animal = animal

        self.measu = measu

        self.flag_changes = pprint.pformat(flag_changes).replace("\n", "<br>")

    def initialize_texts(self, tapestry_config: TapestryConfig):

        self.text_below = tapestry_config.text_below_func(self.measurement_row)

        if tapestry_config.text_right_top_func is not None:
            self.text_right_top = tapestry_config.text_right_top_func(self.measurement_row)

        if tapestry_config.text_right_bottom_func is not None:
            self.text_right_bottom = tapestry_config.text_right_bottom_func(self.measurement_row)

    def write_overview_movie_files(self, extra_formats: typing.Iterable[str], op_folder_path: pl.Path, row_string: str):

        assert self.text_below != "uninitialized", "text_below has not been initialized! Please call the function" \
                                                   "'initialize_texts' first and try again!"

        op_animal_folder_path = op_folder_path / self.animal
        op_animal_folder_path.mkdir(parents=True, exist_ok=True)

        image_op_stem = op_animal_folder_path / f"{row_string}_{self.measu}_{self.text_below}"

        self.image_relative_path = f"{image_op_stem.relative_to(op_folder_path.parent)}.png"

        for format in sanitize_formats(extra_formats):
            measu_op_file = f"{image_op_stem}.{format}"
            self.pil_image.save(measu_op_file)

        return image_op_stem


class PatchWithMovie(Patch):

    def __init__(self, overview: np.ndarray, data_limits: typing.Iterable[float],
                 measurement_row: pd.Series, animal: str, measu: int, flag_changes: dict,
                 op_movie_file: str):

        super().__init__(overview, data_limits, measurement_row, animal, measu, flag_changes)
        self.movie_file = op_movie_file

    def write_overview_movie_files(self, extra_formats: typing.Iterable[str], op_folder_path: pl.Path, row_string: str):

        image_op_stem = super().write_overview_movie_files(extra_formats, op_folder_path, row_string)

        # move movie next to the created overview files
        temp_movie_path = pl.Path(self.movie_file)
        movie_op_file_path = f"{image_op_stem}_movie{temp_movie_path.suffix}"
        temp_movie_path.replace(movie_op_file_path)

        self.movie_file = movie_op_file_path


def get_nonempty_patch(overview, data_limits, measurement_row, animal, measu, flag_changes, op_movie_file):

    if op_movie_file is None:

        return Patch(overview, data_limits, measurement_row, animal, measu, flag_changes)

    else:

        return PatchWithMovie(overview, data_limits, measurement_row, animal, measu, flag_changes, op_movie_file)









