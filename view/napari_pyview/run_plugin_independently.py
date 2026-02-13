from view.napari_pyview import NapariPyViewWidget
import sys
from qtpy.QtWidgets import QApplication


def main():
    # Initialize application Name, Organization Name and Domain
    # initialize_app_settings()

    app = QApplication(sys.argv)
    ex = NapariPyViewWidget()
    ex.showMaximized()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
