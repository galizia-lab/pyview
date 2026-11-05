import pytest

from view.gui.tests.conftest import (
    default_list_load_test_data,
)  # propagated to tests in this folder # noqa: F401
from view.napari_pyview import ILTISWindowNapari, NapariPyViewWidget


@pytest.fixture
def napari_main_widget(
    qtbot, monkeypatch: pytest.MonkeyPatch
) -> NapariPyViewWidget:
    """
    Fixture to provide NapariPyViewWidget instance for tests
    """

    def closeEvent(self, event):
        self.iltis_main_shell.reset()
        event.accept()

    monkeypatch.setattr(ILTISWindowNapari, "closeEvent", closeEvent)

    # Create NapariPyViewWidget instance
    napari_widget = NapariPyViewWidget(parent=None)
    monkeypatch.setattr(napari_widget, "write_status", lambda x: print(x))

    qtbot.addWidget(napari_widget)

    return napari_widget


@pytest.fixture
def napari_main_widget_with_mock_viewer(
    make_napari_viewer_proxy, napari_main_widget
) -> NapariPyViewWidget:

    mock_viewer = make_napari_viewer_proxy()

    napari_main_widget.napari_viewer = mock_viewer

    return napari_main_widget
