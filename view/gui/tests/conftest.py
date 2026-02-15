import matplotlib.pyplot as plt
import pytest
from pytestqt.qtbot import QtBot

from view.gui.central_widget import CentralWidget
from view.gui.loader_widgets import ListLoadWidget
from view.gui.setup_calcmethod_choice import SetupChoice
from view.gui.start_view_gui import ContainerWidget
from view.python_core.flags import FlagsManager


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
