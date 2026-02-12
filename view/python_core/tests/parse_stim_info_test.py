import pandas as pd

from view.python_core.gdm_generation.gdm_data_classes import parse_stim_info

test_data = pd.Series(
    data={
        "StimLen": "23, 30, 40",
        "Odour": "'odor1', 'odor2', 'odor3'",
        "StimONms": "8.4, 6.5, 7.6",
    }
)


def base_io_fun(input_metadata: pd.Series, expected_output: tuple, **kwargs):

    stim_comps, stim_times, stim_durs = parse_stim_info(
        input_metadata, **kwargs
    )

    assert stim_comps == expected_output[0]
    assert stim_times == expected_output[1]
    assert stim_durs == expected_output[2]


def test_basic_functionality_one_odor():
    """
    parse_stim_info: basic functionality test one odour
    """

    base_io_fun(
        input_metadata=pd.Series(
            data={"Odour": "'odor1'", "StimONms": "5.4", "StimLen": "23"}
        ),
        expected_output=(("odor1",), (5.4,), (23,)),
    )


def test_basic_functionality_multiple_odor():
    """
    parse_stim_info: basic functionality test multiple odor (sort=True, not excluding odors)
    """

    base_io_fun(
        input_metadata=test_data,
        expected_output=(
            ("odor1", "odor2", "odor3"),
            (8.4, 6.5, 7.6),
            (23, 30, 40),
        ),
        sort=False,
    )


def test_sorting():
    """
    parse_stim_info: testing with sort=False
    """
    base_io_fun(
        input_metadata=test_data,
        expected_output=(
            ("odor2", "odor3", "odor1"),
            (6.5, 7.6, 8.4),
            (30, 40, 23),
        ),
        sort=True,
    )


def test_excluding_single_odor():
    """
    parse_stim_info: excluding single odor
    """

    base_io_fun(
        input_metadata=test_data,
        expected_output=(("odor3", "odor1"), (7.6, 8.4), (40, 23)),
        odors_to_exclude_str="odor2",
    )


def test_excluding_multiple_odors():
    """
    parse_stim_info: excluding multiple odors
    """

    base_io_fun(
        input_metadata=test_data,
        expected_output=(("odor3",), (7.6,), (40,)),
        odors_to_exclude_str="odor2, odor1",
    )
