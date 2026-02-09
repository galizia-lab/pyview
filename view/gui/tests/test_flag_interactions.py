#!/usr/bin/env python3
"""
Test file for flag interactions in the CentralWidget.

This test verifies that:
 1. when a specific value is chosen for LE_loadExp in the setup choice box, the same is correctly updated in the flags widget
 2. when a specific value is chosen for LE_loadExp in the flags widget, the same is correctly updated in the setup choice box

"""

import pytest
from qtpy.QtCore import Qt

from view.gui.central_widget import CentralWidget


@pytest.fixture
def central_widget(qtbot):
    """Fixture to provide a CentralWidget instance for the tests."""
    widget = CentralWidget(parent=None)
    pytest.MonkeyPatch().setattr(widget, "write_status", lambda x: print(x))
    qtbot.addWidget(widget)
    yield widget


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

    # Find the index of the target item in the dropdown
    target_text = "Synthetic data, type 665 (LE_loadExp=665)"
    index = setup_choice_box.dropdown.findText(target_text)

    # Ensure the item exists in the dropdown
    assert index >= 0, f"Item '{target_text}' not found in the dropdown."

    # Set the current index to the target item
    qtbot.mouseClick(setup_choice_box.dropdown, Qt.LeftButton)
    qtbot.keyClicks(setup_choice_box.dropdown, target_text)
    qtbot.keyClick(setup_choice_box.dropdown, Qt.Key_Enter)

    assert setup_choice_box.get_current_LE_loadExp() == 665, (
        "Simulated mouse clicks did not select test LE_loadExp."
    )

    # Get the flag value from the LoadData subgroup
    load_data_subgroup = flags_widget.flag_display_choice.subgroup_pages[
        "LoadData"
    ]
    flag_value = load_data_subgroup.flag_values_descriptions_df.loc[
        "LE_loadExp", "Flag Value"
    ]

    # Verify that the flag value is "665"
    assert flag_value == "665", (
        f"Expected flag value to be '665', but got '{flag_value}'."
    )


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

    # Get the LoadData subgroup
    load_data_subgroup = flags_widget.flag_display_choice.subgroup_pages[
        "LoadData"
    ]

    # Get combobox and simulate user selection
    flag_combobox = load_data_subgroup.flag_values_descriptions_df.loc[
        "LE_loadExp", "combobox"
    ]

    target_text = "665"

    qtbot.mouseClick(flag_combobox, Qt.LeftButton)
    qtbot.keyClick(
        flag_combobox, Qt.Key_A, modifier=Qt.KeyboardModifier.ControlModifier
    )  # select all, to delete
    qtbot.keyClick(flag_combobox, Qt.Key_Delete)
    qtbot.keyClicks(flag_combobox, target_text)
    qtbot.keyClick(flag_combobox, Qt.Key_Enter)

    # Verify the simulated user selection took hold
    flag_value = load_data_subgroup.flag_values_descriptions_df.loc[
        "LE_loadExp", "Flag Value"
    ]
    assert flag_value == "665", (
        f"Expected flag value to be '665', but got '{flag_value}'. Simulated user selection might not have worked."
    )

    # Verify that setup_choice_box.get_current_LE_loadExp() returns "665"
    assert setup_choice_box.get_current_LE_loadExp() == 665, (
        f"Expected setup_choice_box.get_current_LE_loadExp() to return 665, but got {setup_choice_box.get_current_LE_loadExp()}."
    )


if __name__ == "__main__":
    pytest.main([__file__])
