import pathlib as pl

import jinja2 as j2

from view.python_core.get_internal_files import get_internal_jinja_template
from view.python_core.utils.colors import mpl_color_to_css
from view.python_core.view_object import VIEW
from .patch import get_nonempty_patch, EmptyPatch
from .tapestry_config import TapestryConfig


class TapestryCreater(object):

    def __init__(self, tapestry_config, init_yml_flags_file, terminal_output_verbose=True):

        super().__init__()
        self.tapestry_config = tapestry_config

        self.view = VIEW(terminal_output_verbose=terminal_output_verbose)

        self.view.update_flags_from_ymlfile(init_yml_flags_file)

        tapestries_dir_path = pl.Path(self.view.flags.get_op_tapestries_dir())

        self.current_tapestry_dir_path = tapestries_dir_path / tapestry_config.name
        self.current_tapestry_dir_path.mkdir(parents=True, exist_ok=True)

    def update_row_animal_measus(self, row, current_measus):

        # initialize the animal, to the value if specified, else to that of previous patch
        if "animal" in row:
            self.view.initialize_animal(row["animal"])
            current_animal = row["animal"]
        else:
            current_animal = self.view.flags["STG_ReportTag"]

        # if measus in current row, set current_measus to it
        if "measus" in row:
            current_measus = row["measus"]

        return current_animal, current_measus

    def interpret_row_settings_for_overviews(self, row, current_overview_flags, current_extra_formats):

        # update flags for this row, if specified
        if "flags" in row:
            flag_changes = row["flags"]
        else:
            flag_changes = current_overview_flags

        # initialize extra formats to use
        if "extra_formats" in row:
            extra_formats = row["extra_formats"]
        else:
            extra_formats = current_extra_formats

        return extra_formats, flag_changes

    def interpret_row_settings_for_movies(self, row, current_create_movies, current_movie_flags):

        # interpret whether movies are to be created
        if "corresponding_movies" in row:
            create_movies = row["corresponding_movies"]
        else:
            create_movies = current_create_movies

        flag_changes = current_movie_flags

        # update movie flags analogous to those specified for overviews
        if "flags" in row:
            analogous_movie_flags = {f"mv{k[2:]}" if k.startswith("SO") else k: v for k, v in row["flags"].items()}
            flag_changes.update(analogous_movie_flags)

        # update additional movie flags, if specified
        if "extra_movie_flags" in row:
            flag_changes.update(row["extra_movie_flags"])

        return create_movies, flag_changes

    def generate_overview_movies(self, measu: int, overview_flag_changes: dict, create_movies: bool,
                                 movie_flag_changes: dict):

        # update flags for loading and overviews
        self.view.update_flags(overview_flag_changes)

        # load measurement data
        self.view.load_measurement_data_from_current_animal(measu=measu)

        # calculate signals
        self.view.calculate_signals()

        # set scalebar on and set SO_xgap if not set
        flags2update = {"CTV_scalebar": True}
        if self.view.flags.is_flag_state_default("SO_xgap"):
            flags2update["SO_xgap"] = self.view.p1.metadata.format_x / 6
        self.view.update_flags(flags2update)

        # generate overview, data limits and return them
        overview, data_limits = self.view.generate_overview_for_output_for_current_measurement()

        if create_movies:
            # update flags for movies
            self.view.update_flags(movie_flag_changes)

            # create movie
            op_file = self.view.export_movie_for_current_measurement()

        else:
            op_file = None

        return overview, data_limits, op_file

    def save_all_overviews_preparing_for_tapestry(self):
        """
        Generates and saves overviews for the tapestry as specified by tapestry config. By default, overviews are saved in PNG
        format. In addition, collects and returns text to be placed around overviews in tapestries as
        a pandas.DataFrame object
        :return: pandas.DataFrame, with measurement labels as indices and columns "Text below", "Text top right",
        "Text bottom right" and "Image Name"
        """

        patches_collection = []
        current_measus = []
        current_overview_flags = {}
        current_movie_flags = {}
        current_create_movies = False
        current_extra_formats = []

        # iterate over measurements
        # row is guaranteed to contain one key called 'measus', which is ensured to be a non empty.
        # Could contain one or more of these: 'flags', 'extra_formats' and 'animal', which are ensured respectively
        # to be dict, list and str.
        for row_name, row in self.tapestry_config.iterrows():

            current_animal, current_measus = self.update_row_animal_measus(row, current_measus)

            current_extra_formats, current_overview_flags = self.interpret_row_settings_for_overviews(row,
                                                                                              current_overview_flags,
                                                                                              current_extra_formats)

            current_create_movies, current_movie_flags = self.interpret_row_settings_for_movies(row,
                                                                                                current_create_movies,
                                                                                                current_movie_flags)

            patches_row = []

            for measu in current_measus:

                if measu not in self.view.get_measus_for_current_animal():
                    patch = EmptyPatch()

                else:

                    # generate an overview and optionally a movie, updating flags before generation
                    overview, data_limits, op_movie_file = self.generate_overview_movies(measu, current_overview_flags,
                                                                                         current_create_movies,
                                                                                         current_movie_flags)

                    # pull out the row of measurement list file
                    measurement_row = self.view.measurement_list.get_row_by_measu(measu)

                    patch = get_nonempty_patch(overview=overview, data_limits=data_limits,
                                               measurement_row=measurement_row,
                                               animal=current_animal, measu=measu, flag_changes=current_overview_flags,
                                               op_movie_file=op_movie_file)

                    patch.initialize_texts(self.tapestry_config)
                    patch.write_overview_movie_files(extra_formats=current_extra_formats,
                                                     op_folder_path=self.current_tapestry_dir_path,
                                                     row_string=row_name)

                    # save aspect ratio as it is needed later for arranging overviews
                    # overview_for_output has format YX
                    aspect_ratio = overview.shape[1] / overview.shape[0]

                    # ratio: (padding for colorbar / overview width)
                    # overview_for_output has format YX
                    colorbar2width = 1 - (self.view.p1.metadata.format_x / overview.shape[1])

                patches_row.append(patch)

            patches_collection.append(patches_row)

        # initialize dummy values if no patches were initialized
        if len(patches_collection) == 0:
            aspect_ratio = 1
            colorbar2width = 0.3

        # convert bg and fg colors to css
        bg_color_css = mpl_color_to_css(self.view.flags["SO_bgColor"])
        fg_color_css = mpl_color_to_css(self.view.flags["SO_fgColor"])

        return patches_collection, aspect_ratio, colorbar2width, bg_color_css, fg_color_css

    def create_html(self, patches_collection, aspect_ratio, colorbar2width, bg_color, fg_color):

        # get the internal jinja template file
        jinja_template_file = get_internal_jinja_template("tapestry.html")

        # read the template and initialize a jinja2.Template object
        with open(jinja_template_file) as fh:
            template = j2.Template(fh.read())

        all_upper_limits = []
        all_lower_limits = []

        for row in patches_collection:
            for patch in row:
                if hasattr(patch, "data_limits"):
                    all_upper_limits.append(patch.data_limits[1])
                    all_lower_limits.append(patch.data_limits[0])

        all_data_limits = [round(min(all_lower_limits), 3), round(max(all_upper_limits), 3)]

        # render tapestry html with specified values in <overviews_text_df>
        html_str = template.render(patches_collection=patches_collection,
                                   aspect_ratio=aspect_ratio, colorbar2width=colorbar2width,
                                   fg_color=fg_color, bg_color=bg_color,
                                   nrows=len(patches_collection), ncols=max(len(x) for x in patches_collection),
                                   all_data_limits=all_data_limits)

        # initialize output filename
        op_html_file = str(self.current_tapestry_dir_path.parent / f"{self.tapestry_config.name}.html")

        # write html file
        with open(op_html_file, 'w') as fh:
            fh.write(html_str)

        return op_html_file


def create_tapestry(
        tapestry_config_file, init_yml_flags_file, text_below_func,
        text_right_top_func=None, text_right_bottom_func=None, terminal_output_verbose=True):
    
    tapestry_config = TapestryConfig(
        yml_file=tapestry_config_file, text_below_func=text_below_func,
        text_right_top_func=text_right_top_func,
        text_right_bottom_func=text_right_bottom_func,
    )

    tc = TapestryCreater(
        tapestry_config=tapestry_config, init_yml_flags_file=init_yml_flags_file,
        terminal_output_verbose=terminal_output_verbose
    )

    patches_collection, aspect_ratio, colorbar2width, bg_color, fg_color \
        = tc.save_all_overviews_preparing_for_tapestry()

    html_out_file = tc.create_html(patches_collection=patches_collection, aspect_ratio=aspect_ratio,
                                   colorbar2width=colorbar2width, bg_color=bg_color, fg_color=fg_color)

    return html_out_file, tc.view




