import sys
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.interface import FileFlowApp
from app.styles import APP_STYLE


def main():
    """Start the FileFlow desktop application."""

    # Check whether this is an automated startup test
    smoke_test = "--smoke-test" in sys.argv

    # Create the Qt application
    app = QApplication(sys.argv)

    # Apply FileFlow's visual styling
    app.setStyleSheet(APP_STYLE)

    # Create the desktop window
    window = FileFlowApp()

    # Accept filenames only during normal use
    if not smoke_test and len(sys.argv) > 1:
        window.set_selected_files(sys.argv[1:])

    # Display the main window
    window.show()

    if smoke_test:

        def check_startup():
            """Verify the main window initialized."""

            if window.isVisible():
                print(
                    "SMOKE TEST PASSED: FileFlow window initialized.",
                    flush=True
                )
                app.exit(0)
            else:
                print(
                    "SMOKE TEST FAILED: Window is not visible.",
                    flush=True
                )
                app.exit(1)

        # Check the GUI after the event loop starts
        QTimer.singleShot(500, check_startup)

    # Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
