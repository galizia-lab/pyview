#!/usr/bin/env python3
"""
Test file for flag interactions in the CentralWidget.

This test verifies that:
 1. when a specific value is chosen for LE_loadExp in the setup choice box, the same is correctly updated in the flags widget
 2. when a specific value is chosen for LE_loadExp in the flags widget, the same is correctly updated in the setup choice box

"""

import pytest

from view.gui.central_widget import CentralWidget
from view.gui.tests.test_flags_box import simulate_flag_selection
from view.gui.tests.test_setup_choice import (
    select_item_and_check_in_setup_choice_box,
)


def test_setup_choice_selection_flag_updation(
    central_widget: CentralWidget, qtbot
):
    """
    Test that when the value "Synthetic data, type 665 (LE_loadExp=665)" is chosen in
    setup_choice_box.dropdown, then
    flags_widget.flag_display_choice.subgroup_pages["LoadData"].flag_values_descriptions_df.loc['LE_loadExp', 'Flag Value']
    should be "665".
    """
    # Get the setup_choice_box and flags_widget from the central_widget
    setup_choice_box = central_widget.setup_choice_box
    flags_widget = central_widget.flags_widget

    # Select target item in the dropdown
    target_text = "Synthetic data, type 665 (LE_loadExp=665)"
    select_item_and_check_in_setup_choice_box(
        setup_choice_box, qtbot, target_text
    )

    # Get the flag value from the LoadData subgroup
    load_data_subgroup = flags_widget.flag_display_choice.subgroup_pages[
        "LoadData"
    ]
    flag_value = load_data_subgroup.flag_values_descriptions_df.loc[
        "LE_loadExp", "Flag Value"
    ]

    # Verify that the flag value is "665"
    assert (
        flag_value == "665"
    ), f"Expected flag value to be '665', but got '{flag_value}'."


def test_flag_updation_when_setup_choice_selection(
    central_widget: CentralWidget, qtbot
):
    """
    Test that when "665" is selected from the dropdown in
    flags_widget.flag_display_choice.subgroup_pages["LoadData"].flag_values_descriptions_df.loc['LE_loadExp', 'combobox'],
    setup_choice_box.get_current_LE_loadExp() should return "665".
    """
    # Get the setup_choice_box and flags_widget from the central_widget
    setup_choice_box = central_widget.setup_choice_box
    flags_widget = central_widget.flags_widget

    target_text = "665"

    # Use the helper function to simulate flag selection
    simulate_flag_selection(
        flags_widget.flag_display_choice, "LE_loadExp", target_text, qtbot
    )

    # Verify that setup_choice_box.get_current_LE_loadExp() returns "665"
    assert (
        setup_choice_box.get_current_LE_loadExp() == 665
    ), f"Expected setup_choice_box.get_current_LE_loadExp() to return 665, but got {setup_choice_box.get_current_LE_loadExp()}."


if __name__ == "__main__":
    pytest.main([__file__])
