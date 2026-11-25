
import os
import sys
import traceback
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from app.interface import FileFlowApp
from app.styles import APP_STYLE


def save_test_report(message):
    """Save automated test output for GitHub Actions."""

    report_path = os.environ.get("FILEFLOW_TEST_REPORT")

    if report_path:
        Path(report_path).write_text(
            message,
            encoding="utf-8"
        )

    # Normal console output is optional in windowed apps
    if sys.stdout is not None:
        print(message, flush=True)


def test_conversions():
    """Test conversion engines inside the packaged app."""

    import pymupdf
    from PIL import Image

    from app.converter import convert_image
    from app.pdf_converter import convert_pdf

    results = []

    with TemporaryDirectory() as temp_dir:
        folder = Path(temp_dir)

        # Test 1: JPG -> PNG
        jpg_file = folder / "test_image.jpg"

        Image.new(
            "RGB", (100, 100), "blue"
        ).save(jpg_file, format="JPEG")

        png_output = convert_image(jpg_file, "PNG")

        with Image.open(png_output) as result:
            assert result.format == "PNG"
            assert result.size == (100, 100)

        results.append("PASS: JPG to PNG")

        # Test 2: PNG -> PDF
        source_png = folder / "source_image.png"

        Image.new(
            "RGB", (100, 100), "red"
        ).save(source_png, format="PNG")

        pdf_output = convert_image(source_png, "PDF")

        with pymupdf.open(pdf_output) as document:
            assert document.page_count == 1
            assert document.is_pdf

        results.append("PASS: PNG to PDF")

        # Test 3: Single-page PDF -> JPG
        single_pdf = folder / "single_page.pdf"

        with pymupdf.open() as document:
            document.new_page(width=300, height=300)
            document.save(single_pdf)

        jpg_output = convert_pdf(single_pdf, "JPG")

        with Image.open(jpg_output) as result:
            assert result.format == "JPEG"
            assert result.width > 0
            assert result.height > 0

        results.append("PASS: Single-page PDF to JPG")

        # Test 4: Multi-page PDF -> ZIP
        multi_pdf = folder / "multi_page.pdf"

        with pymupdf.open() as document:
            for _ in range(3):
                document.new_page(
                    width=300,
                    height=300
                )

            document.save(multi_pdf)

        zip_output = convert_pdf(multi_pdf, "PNG")

        assert zip_output.suffix.lower() == ".zip"

        with ZipFile(zip_output, "r") as archive:
            filenames = archive.namelist()

            assert len(filenames) == 3
            assert archive.testzip() is None

            for filename in filenames:
                assert filename.endswith(".png")

                with Image.open(
                    BytesIO(archive.read(filename))
                ) as result:
                    assert result.format == "PNG"
                    result.verify()

        results.append("PASS: Multi-page PDF to ZIP")

    results.append("ALL WINDOWS CONVERSION TESTS PASSED")
    save_test_report("\n".join(results))


def main():
    """Start FileFlow or run automated checks."""

    # Conversion test mode
    if "--conversion-smoke-test" in sys.argv:
        try:
            test_conversions()
            return 0

        except Exception:
            save_test_report(
                "CONVERSION TEST FAILED\n"
                + traceback.format_exc()
            )
            return 1

    # GUI startup test mode
    smoke_test = "--smoke-test" in sys.argv

    try:
        app = QApplication(sys.argv)
        app.setStyleSheet(APP_STYLE)

        window = FileFlowApp()

        if not smoke_test and len(sys.argv) > 1:
            window.set_selected_files(sys.argv[1:])

        window.show()

        if smoke_test:

            def check_startup():
                try:
                    if window.isVisible():
                        save_test_report(
                            "SMOKE TEST PASSED: "
                            "FileFlow window initialized."
                        )
                        app.exit(0)
                    else:
                        save_test_report(
                            "SMOKE TEST FAILED: "
                            "Window is not visible."
                        )
                        app.exit(1)

                except Exception:
                    save_test_report(
                        "SMOKE TEST FAILED\n"
                        + traceback.format_exc()
                    )
                    app.exit(1)

            QTimer.singleShot(500, check_startup)

        return app.exec()

    except Exception:
        if smoke_test:
            save_test_report(
                "SMOKE TEST FAILED\n"
                + traceback.format_exc()
            )
            return 1

        raise


if __name__ == "__main__":
    sys.exit(main())
