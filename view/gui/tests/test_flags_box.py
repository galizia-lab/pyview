#!/usr/bin/env python3
"""
Test file for FlagsDisplayChoiceTabs and related functionality.
"""

import pytest
from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt

from view.gui.flags_box import FlagsDisplayChoiceTabs
from view.gui.tests.fixtures import central_widget, flags_display_choice_tabs


def simulate_flag_selection(
    flags_display_choice_tabs: FlagsDisplayChoiceTabs,
    flag_name: str,
    target_value: str,
    qtbot: QtBot,
):
    """
    Helper function to simulate user selection of a flag value in the UI.

    Args:
        flags_display_choice_tabs: FlagsDisplayChoiceTabs object
        flag_name: Name of the flag to select
        target_value: Target value to set for the flag
        qtbot: pytest-qt bot for simulating user interactions
    """
    # Get the subgroup page for the flag using the mapping
    subgroup_name = flags_display_choice_tabs.flag_name_subgroup_mapping.get(
        flag_name
    )
    if subgroup_name is None:
        raise ValueError(f"Flag '{flag_name}' not found in subgroup mapping")

    subgroup_page = flags_display_choice_tabs.subgroup_pages[subgroup_name]

    # Get combobox and simulate user selection
    flag_combobox = subgroup_page.flag_values_descriptions_df.loc[
        flag_name, "combobox"
    ]

    qtbot.mouseClick(flag_combobox, Qt.LeftButton)
    qtbot.keyClick(
        flag_combobox, Qt.Key_A, modifier=Qt.KeyboardModifier.ControlModifier
    )  # select all, to delete
    qtbot.keyClick(flag_combobox, Qt.Key_Delete)
    qtbot.keyClicks(flag_combobox, target_value)
    qtbot.keyClick(flag_combobox, Qt.Key_Enter)

    # Verify the simulated user selection took hold
    flag_value = subgroup_page.flag_values_descriptions_df.loc[
        flag_name, "Flag Value"
    ]
    assert flag_value == target_value, (
        f"Expected flag value to be '{target_value}', but got '{flag_value}'. "
        f"Simulated user selection might not have worked."
    )


def test_simulate_flag_selection_le_loadExp(
    flags_display_choice_tabs, qtbot: QtBot
):
    """
    Test the simulate_flag_selection helper function with the flag "LE_loadExp" and target value 665.
    """
    simulate_flag_selection(
        flags_display_choice_tabs, "LE_loadExp", "665", qtbot
    )
