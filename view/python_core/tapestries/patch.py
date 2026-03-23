from __future__ import annotations

import pathlib as pl
import pprint
import typing
from dataclasses import dataclass

import pandas as pd
from PIL import Image

if typing.TYPE_CHECKING:
    from view.python_core.overviews import OverviewDataForOutput
    from view.python_core.tapestries.tapestry_config import TapestryConfig


def sanitize_formats(formats: typing.Iterable[str]) -> typing.Iterable[str]:
    formats = [x.lower().lstrip(".") for x in formats]

    if "png" not in formats:
        formats.append("png")

    return formats


@dataclass
class EmptyPatch:
    image_relative_path: str = "Excluded"
    text_below: str = ""
    text_right_bottom: str = ""
    text_right_top: str = ""
    animal: str = "Invalid"
    flag_changes: str = "Invalid"
    movie_file_for_html: str = None


@dataclass
class Patch(EmptyPatch):
    overview_data_for_output: OverviewDataForOutput = None
    measurement_row: pd.Series = None
    measu: int = None
    pil_image: Image = None
    image_relative_path: pl.Path | str = None

    def __post_init__(self):

        self.pil_image = Image.fromarray(
            self.overview_data_for_output.overview_frame_for_output
        )

        self.text_right_bottom, self.text_right_top = [
            f"{x:.3g}" for x in self.overview_data_for_output.data_limits
        ]

        self.text_below = "uninitialized"

        self.image_relative_path = "uninitialized"

        self.flag_changes = pprint.pformat(self.flag_changes).replace(
            "\n", "<br>"
        )

    def initialize_texts(self, tapestry_config: TapestryConfig):

        self.text_below = tapestry_config.text_below_func(self.measurement_row)

        if tapestry_config.text_right_top_func is not None:
            self.text_right_top = tapestry_config.text_right_top_func(
                self.measurement_row
            )

        if tapestry_config.text_right_bottom_func is not None:
            self.text_right_bottom = tapestry_config.text_right_bottom_func(
                self.measurement_row
            )

    def write_overview_movie_files(
        self,
        extra_formats: typing.Iterable[str],
        op_folder_path: pl.Path,
        row_string: str,
    ):

        assert self.text_below != "uninitialized", (
            "text_below has not been initialized! Please call the function"
            "'initialize_texts' first and try again!"
        )

        op_animal_folder_path = op_folder_path / self.animal
        op_animal_folder_path.mkdir(parents=True, exist_ok=True)

        image_op_stem = (
            op_animal_folder_path
            / f"{row_string}_{self.measu}_{self.text_below}"
        )

        self.image_relative_path = (
            f"{image_op_stem.relative_to(op_folder_path.parent)}.png"
        )

        for output_extension in sanitize_formats(extra_formats):
            measu_op_file = f"{image_op_stem}.{output_extension}"
            self.pil_image.save(measu_op_file)

        return image_op_stem


@dataclass
class PatchWithMovie(Patch):
    movie_file_to_move: str = None

    def __post_init__(self):

        super().__post_init__()

    def write_overview_movie_files(
        self,
        extra_formats: typing.Iterable[str],
        op_folder_path: pl.Path,
        row_string: str,
    ):

        image_op_stem = super().write_overview_movie_files(
            extra_formats, op_folder_path, row_string
        )

        # move movie next to the created overview files
        temp_movie_path = pl.Path(self.movie_file_to_move)
        movie_op_file_path = f"{image_op_stem}_movie{temp_movie_path.suffix}"
        temp_movie_path.replace(movie_op_file_path)

        self.movie_file_for_html = movie_op_file_path


def get_nonempty_patch(
    overview_data_for_output: OverviewDataForOutput,
    measurement_row: pd.Series,
    animal: str,
    measu: int,
    flag_changes: str,
    movie_file_to_move: str,
):

    patch_input = {
        "overview_data_for_output": overview_data_for_output,
        "measurement_row": measurement_row,
        "animal": animal,
        "measu": measu,
        "flag_changes": flag_changes,
    }
    if movie_file_to_move is None:
        return Patch(**patch_input)

    else:
        return PatchWithMovie(
            **patch_input, movie_file_to_move=movie_file_to_move
        )
