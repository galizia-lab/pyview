import pathlib as pl
from dataclasses import dataclass

import matplotlib.pyplot as plt
import pytest
from pytestqt.qtbot import QtBot

from view.gui.central_widget import CentralWidget
from view.gui.loader_widgets import ListLoadWidget
from view.gui.setup_calcmethod_choice import SetupChoice
from view.gui.start_view_gui import ContainerWidget
from view.python_core.flags import FlagsManager
from view.python_core.tests.common import get_synthetic_data_yml_path


@pytest.fixture
def central_widget(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> CentralWidget:
    """Fixture to provide a CentralWidget instance for the tests."""
    widget = CentralWidget(parent=None)
    monkeypatch.setattr(widget, "write_status", lambda x: print(x))
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def setup_choice_box(qtbot: QtBot):
    """Fixture to provide a SetupChoice instance for tests."""
    widget = SetupChoice(parent=None)
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def flags_display_choice_tabs(central_widget: CentralWidget):
    """Fixture to provide a FlagsDisplayChoiceTabs instance for the tests."""
    return central_widget.flags_widget.flag_display_choice


@pytest.fixture
def main_container_widget(qtbot):
    """Fixture to provide a ContainerWidget instance for the tests."""
    widget = ContainerWidget()

    def closeEvent(event):
        plt.close("all")
        event.accept()

    pytest.MonkeyPatch().setattr(widget, "closeEvent", closeEvent)

    central_widget = widget.view_main_window.centralWidget()
    pytest.MonkeyPatch().setattr(
        central_widget, "write_status", lambda x: print(x)
    )
    qtbot.addWidget(widget)
    return widget


@pytest.fixture
def list_load_widget(qtbot):
    """Fixture to provide a ListLoadWidget instance for the tests."""

    flags = FlagsManager()

    widget = ListLoadWidget(parent=None, default_flags=flags.flags)

    qtbot.addWidget(widget)
    yield widget

    widget.close()


@dataclass
class ListLoadTestData:
    test_yml_path: pl.Path
    lst_path: pl.Path
    measurement_rows_to_select: tuple[int, ...]
    roi_path: pl.Path | None = None
    area_path: pl.Path | None = None


@pytest.fixture
def default_list_load_test_data() -> ListLoadTestData:

    test_yml_path = get_synthetic_data_yml_path()
    lst_path = (
        pl.Path(get_synthetic_data_yml_path()).parent
        / "02_LISTS"
        / "Synthetic_data_strip.lst.xls"
    )
    measurement_rows_to_select = (2, 3, 5, 6)

    return ListLoadTestData(
        test_yml_path=test_yml_path,
        lst_path=lst_path,
        measurement_rows_to_select=measurement_rows_to_select,
    )
