from view.python_core.io import read_check_yml_file
import numpy as np
import pathlib as pl


class TapestryConfig(object):

    def __init__(
            self, yml_file, text_below_func, text_right_top_func=None, text_right_bottom_func=None,
    ):
        """
        :param yml_file: str, path of a yml file on the file system
        :param extra_formats: iterable of string, each representing an image extension (without the leading dot)
        :param text_below_func: a function that takes one argument - row of the measurement list for a measurement,
        and returns a string. This string will be placed below the overview frame
        :param text_right_top_func: a function that takes one argument - row of the measurement list for a measurement,
        and returns a string. This string will be placed on the top to the right of the overview. If None, the upper
        limit of the data shown in the overview image will be printed
        :param text_right_bottom_func: a function that takes one argument - row of the measurement list for
        a measurement, and returns a string. This string will be placed on the top to the right of the overview.
        If None, the lower limit of the data shown in the overview image will be printed
        """

        super().__init__()
        self.yml_file = yml_file
        self.yml_contents = read_check_yml_file(yml_file, dict)

        self.name = pl.Path(yml_file).stem

        self.text_below_func = text_below_func
        self.text_right_top_func = text_right_top_func
        self.text_right_bottom_func = text_right_bottom_func

    def iterrows(self):
        """
        Generator function
        can be used to iterate over information about rows as dictionaries
        """
        optional_entry_def = {"flags": dict,
                              "extra_formats": list,
                              "animal": str,
                              "measus": list,
                              "corresponding_movies": bool,
                              "extra_movie_flags": dict}

        yml_contents_items = list(self.yml_contents.items())
        yml_keys = self.yml_contents.keys()
        assert len(yml_keys) == len(set(yml_keys)), f"In {self.yml_file}, Duplicate row names found! Please make sure" \
                                                    f"each row has a unique name."

        first_row = yml_contents_items[0][1]
        assert "animal" in first_row, f"First row of all tapestry config files must contain the entry 'animal'." \
                                      f"This was not found in {self.yml_file}. Please add one!"
        assert "measus" in first_row, f"First row of all tapestry config files must contain the entry 'measus'." \
                                      f"This was not found in {self.yml_file}. Please add one!"
        assert len(first_row["measus"]) > 0, f"Entry 'measus' in the first row of {self.yml_file} is empty, which is " \
                                             f"invalid. Please add some measurement to it!"

        # check if all entries have the correct type
        for ind, (k, v) in enumerate(yml_contents_items):
            for entry, expected_type in optional_entry_def.items():
                if entry in v:
                    tpye = type(v[entry])
                    assert tpye is expected_type, f"Entry '{entry}' in {self.yml_file} is expected to be " \
                                                  f"a {expected_type}. Got {tpye} instead"
            yield k, v







