import pytest

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
