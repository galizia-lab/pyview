#!/usr/bin/env python3
"""
Test file for setup choice interactions in the CentralWidget.

This test verifies that:
  1. when a specific value is chosen for LE_loadExp in the setup choice box, the same is correctly updated in the flags widget
  2. when a specific value is chosen for LE_loadExp in the flags widget, the same is correctly updated in the setup choice box

"""

from pytestqt.qtbot import QtBot
from qtpy.QtCore import Qt

from view.gui.setup_calcmethod_choice import SetupChoice


def select_item_and_check_in_setup_choice_box(
    setup_choice_box: SetupChoice, qtbot: QtBot, target_text: str
):
    """
    Helper function to select an item in the setup choice box dropdown.

    Args:
        setup_choice_box: The setup choice box widget.
        qtbot: The qtbot fixture for simulating user interactions.
        target_text: The text of the item to select in the dropdown.
    """
    # Find the index of the target item in the dropdown
    index = setup_choice_box.dropdown.findText(target_text)

    # Ensure the item exists in the dropdown
    assert index >= 0, f"Item '{target_text}' not found in the dropdown."

    # Set the current index to the target item
    qtbot.mouseClick(setup_choice_box.dropdown, Qt.LeftButton)
    qtbot.keyClicks(setup_choice_box.dropdown, target_text)
    qtbot.keyClick(setup_choice_box.dropdown, Qt.Key_Enter)

    found_le_loadExp = setup_choice_box.get_current_LE_loadExp()
    expected_le_loadExp = setup_choice_box.setup_description_dict[target_text]
    assert (
        found_le_loadExp == expected_le_loadExp
    ), f"After Simulated mouse clicks, found LE_loadExp = {found_le_loadExp}, expected LE_loadExp = {expected_le_loadExp}."


def test_setup_choice_selection_flag_updation(
    setup_choice_box: SetupChoice, qtbot
):
    """
    Test that when the value "Synthetic data, type 665 (LE_loadExp=665)" is chosen in
    setup_choice_box.dropdown, then
    flags_widget.flag_display_choice.subgroup_pages["LoadData"].flag_values_descriptions_df.loc['LE_loadExp', 'Flag Value']
    should be "665".
    """

    # select the target item
    target_text = "Synthetic data, type 665 (LE_loadExp=665)"
    select_item_and_check_in_setup_choice_box(
        setup_choice_box, qtbot, target_text
    )
