
import sys

from PySide6.QtWidgets import QApplication

from app.interface import FileFlowApp
from app.styles import APP_STYLE


def main():
    # Create the Qt application
    app = QApplication(sys.argv)

    # Apply FileFlow's visual styling
    app.setStyleSheet(APP_STYLE)

    # Create the desktop window
    window = FileFlowApp()

    # Accept filenames passed when launching FileFlow
    if len(sys.argv) > 1:
        window.set_selected_files(sys.argv[1:])

    # Display the main window
    window.show()

    # Start the application event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
