
import sys
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QComboBox,
    QMessageBox,
    QListWidget,
    QProgressBar,
    QHBoxLayout,
)

from app.converter import convert_image
from app.pdf_converter import convert_pdf
from app.styles import APP_STYLE


ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".pdf"
}


class DropArea(QLabel):
    """Accept files dragged from Finder or Explorer."""

    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()

        self.setText(
            "↑\n\nDrag & Drop Files Here\n\n"
            "JPG • PNG • WEBP • PDF"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(100)
        self.setAcceptDrops(True)

        self.setStyleSheet("""
            QLabel {
                order: 2px dashed #AAA2F1;
        border-radius: 16px;
        background-color: #F0EEFF;
        color: #635BDB;
        font-size: 16px;
        font-weight: bold;
        padding: 24px;
    }
""")

    def get_valid_paths(self, event):
        """Extract supported local file paths."""

        if not event.mimeData().hasUrls():
            return []

        paths = []

        for url in event.mimeData().urls():
            if not url.isLocalFile():
                continue

            path = Path(url.toLocalFile())

            if (
                path.is_file()
                and path.suffix.lower() in ALLOWED_EXTENSIONS
            ):
                paths.append(str(path))

        return paths

    def dragEnterEvent(self, event):
        if self.isEnabled() and self.get_valid_paths(event):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not self.isEnabled():
            event.ignore()
            return

        paths = self.get_valid_paths(event)

        if paths:
            self.files_dropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()


class ConversionWorker(QThread):
    """Run conversions without blocking the main window."""

    progress = Signal(int, int, str)
    result = Signal(int, list)

    def __init__(self, files, output_format):
        super().__init__()

        # Take a snapshot of the current queue
        self.files = files.copy()
        self.output_format = output_format

    def run(self):
        """Convert each file on the background thread."""

        success_count = 0
        failed_files = []
        total = len(self.files)

        for index, file_path in enumerate(self.files, start=1):

            try:
                extension = Path(file_path).suffix.lower()

                if extension == ".pdf":
                    output = convert_pdf(
                        file_path,
                        self.output_format
                    )
                else:
                    output = convert_image(
                        file_path,
                        self.output_format
                    )

                success_count += 1
                print("Converted:", output)

            except Exception as error:
                failed_files.append(
                    f"{Path(file_path).name}: {error}"
                )

            # Report progress even if a file failed
            self.progress.emit(
                index,
                total,
                Path(file_path).name
            )

        # Send the final result back to the window
        self.result.emit(success_count, failed_files)


class FileFlowApp(QWidget):

    def __init__(self):
        super().__init__()
        self.setObjectName("mainWindow")

        self.selected_files = []
        self.worker = None

        self.setWindowTitle("FileFlow - Batch Converter")
        self.resize(600, 650)
        self.setMinimumSize(500, 550)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Application title
        # Main application heading
        title = QLabel("✦ FileFlow")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Your files, your format.")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        

        # Drag-and-drop zone
        self.drop_area = DropArea()
        self.drop_area.files_dropped.connect(
            self.set_selected_files
        )
        layout.addWidget(self.drop_area)

        # File selection controls
        button_row = QHBoxLayout()

        self.select_button = QPushButton("Add Files")
        self.select_button.clicked.connect(self.select_files)
        button_row.addWidget(self.select_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_files)
        button_row.addWidget(self.clear_button)

        layout.addLayout(button_row)

        # File queue
        self.queue_label = QLabel("Your Files (0)")
        self.queue_label.setObjectName("sectionTitle")
        layout.addWidget(self.queue_label)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(130)
        layout.addWidget(self.file_list)

        # Remove individual selected file
        self.remove_button = QPushButton("Remove Selected File")
        self.remove_button.clicked.connect(
            self.remove_selected_file
        )
        layout.addWidget(self.remove_button)

        # Output format selector
        layout.addWidget(QLabel("Convert all files to:"))

        self.format_dropdown = QComboBox()
        layout.addWidget(self.format_dropdown)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Status information
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Convert button
        self.convert_button = QPushButton("Convert Files")
        self.convert_button.setObjectName("convertButton")
        self.convert_button.clicked.connect(
            self.convert_files
        )
        layout.addWidget(self.convert_button)

        self.refresh_interface()

    def set_selected_files(self, paths):
        """Add new files without removing existing ones."""

        all_paths = self.selected_files + paths

        # Remove duplicates
        unique_paths = list(dict.fromkeys(all_paths))

        self.selected_files = [
            path for path in unique_paths
            if Path(path).is_file()
            and Path(path).suffix.lower()
            in ALLOWED_EXTENSIONS
        ]

        self.refresh_interface()
        self.status_label.setText("Ready to convert")
        self.progress_bar.setValue(0)

    def select_files(self):
        """Select multiple files using Finder or Explorer."""

        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select files to convert",
            "",
            "Supported Files (*.jpg *.jpeg *.png *.webp *.pdf)"
        )

        if paths:
            self.set_selected_files(paths)

    def remove_selected_file(self):
        """Remove one highlighted file from the queue."""

        row = self.file_list.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "No Selection",
                "Select a file in the list first."
            )
            return

        self.selected_files.pop(row)

        self.refresh_interface()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")

    def clear_files(self):
        """Remove every file from the queue."""

        self.selected_files = []

        self.refresh_interface()
        self.progress_bar.setValue(0)
        self.status_label.setText("Ready")

    def refresh_interface(self):
        """Update the queue and available output formats."""

        # Refresh the list of filenames
        self.file_list.clear()

        for path in self.selected_files:
            self.file_list.addItem(Path(path).name)

        total = len(self.selected_files)

        self.queue_label.setText(f"Your Files ({total})")

        self.convert_button.setText(
            f"Convert {total} File(s)"
        )

        self.convert_button.setEnabled(total > 0)
        self.remove_button.setEnabled(total > 0)
        self.clear_button.setEnabled(total > 0)

        # Choose output formats supported by the whole batch
        previous_format = self.format_dropdown.currentText()
        self.format_dropdown.clear()

        if total == 0:
            return

        has_pdf = any(
            Path(path).suffix.lower() == ".pdf"
            for path in self.selected_files
        )

        if has_pdf:
            formats = ["PNG", "JPG"]
        else:
            formats = ["PNG", "JPG", "WEBP", "PDF"]

        self.format_dropdown.addItems(formats)

        # Preserve previous format if it is still valid
        if previous_format in formats:
            self.format_dropdown.setCurrentText(
                previous_format
            )

    def set_busy(self, busy):
        """Disable queue changes while conversion runs."""

        self.select_button.setEnabled(not busy)
        self.remove_button.setEnabled(
            not busy and bool(self.selected_files)
        )
        self.clear_button.setEnabled(
            not busy and bool(self.selected_files)
        )
        self.drop_area.setEnabled(not busy)
        self.file_list.setEnabled(not busy)
        self.format_dropdown.setEnabled(not busy)
        self.convert_button.setEnabled(
            not busy and bool(self.selected_files)
        )

    def convert_files(self):
        """Start a background conversion job."""

        if not self.selected_files:
            return

        if self.worker is not None:
            return

        output_format = self.format_dropdown.currentText()

        # Start a fresh progress display
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting conversion...")

        self.set_busy(True)

        # Create the background worker
        self.worker = ConversionWorker(
            self.selected_files,
            output_format
        )

        # Connect worker signals to UI update methods
        self.worker.progress.connect(
            self.update_progress
        )

        self.worker.result.connect(
            self.show_results
        )

        self.worker.finished.connect(
            self.conversion_finished
        )

        # Begin background processing
        self.worker.start()

    def update_progress(self, completed, total, filename):
        """Update progress after each processed file."""

        percentage = int(completed / total * 100)

        self.progress_bar.setValue(percentage)

        self.status_label.setText(
            f"Processed {completed}/{total}: {filename}"
        )

    def show_results(self, success_count, failed_files):
        """Display the final batch result."""

        failed_count = len(failed_files)

        message = (
            f"Successful: {success_count}\n"
            f"Failed: {failed_count}"
        )

        if failed_files:
            message += (
                "\n\nErrors:\n"
                + "\n".join(failed_files[:5])
            )

        self.status_label.setText(
            f"Completed: {success_count} successful, "
            f"{failed_count} failed."
        )

        QMessageBox.information(
            self,
            "Batch Conversion Complete",
            message
        )

    def conversion_finished(self):
        """Restore controls after the worker stops."""

        self.set_busy(False)

        self.worker = None

    def closeEvent(self, event):
        """Prevent closing while conversions are running."""

        if self.worker is not None:
            QMessageBox.information(
                self,
                "Conversion Running",
                "Please let the current batch finish before closing."
            )
            event.ignore()
        else:
            event.accept()
            

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet(APP_STYLE)

    window = FileFlowApp()

    # Receive files passed from Finder or the terminal
    if len(sys.argv) > 1:
        window.set_selected_files(sys.argv[1:])

    window.show()

    sys.exit(app.exec())

