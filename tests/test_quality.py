
from pathlib import Path

import pytest
import pymupdf
from PIL import Image

from app.converter import convert_image
from app.pdf_converter import convert_pdf


# TEST 1: A file that does not exist
def test_missing_file(tmp_path):
    missing_file = tmp_path / "missing.jpg"

    with pytest.raises(FileNotFoundError):
        convert_image(missing_file, "PNG")


# TEST 2: Unsupported output format
def test_unsupported_format(tmp_path):
    image_path = tmp_path / "photo.jpg"

    Image.new("RGB", (100, 100), "red").save(image_path)

    with pytest.raises(ValueError):
        convert_image(image_path, "MP3")


# TEST 3: A corrupted image
def test_corrupted_image(tmp_path):
    image_path = tmp_path / "broken.jpg"

    # Create a fake JPG containing invalid data
    image_path.write_bytes(b"This is not a real JPG image")

    with pytest.raises(ValueError):
        convert_image(image_path, "PNG")


# TEST 4: PDF exceeds the page limit
def test_pdf_page_limit(tmp_path):
    pdf_path = tmp_path / "large.pdf"

    # Create a PDF containing 21 pages
    with pymupdf.open() as document:
        for _ in range(21):
            document.new_page()

        document.save(pdf_path)

    # FileFlow currently allows up to 20 pages
    with pytest.raises(ValueError, match="Maximum 20"):
        convert_pdf(pdf_path, "PNG")


# TEST 5: Existing output files remain unchanged
def test_existing_file_not_overwritten(tmp_path):
    source = tmp_path / "photo.jpg"
    existing_output = tmp_path / "photo.png"

    Image.new("RGB", (100, 100), "blue").save(source)
    Image.new("RGB", (100, 100), "green").save(existing_output)

    original_bytes = existing_output.read_bytes()

    # Convert JPG to PNG
    new_output = convert_image(source, "PNG")

    # A different output filename should be created
    assert new_output != existing_output
    assert new_output.exists()

    # The existing file must remain unchanged
    assert existing_output.read_bytes() == original_bytes
    

def test_oversized_image_dimensions(tmp_path, monkeypatch):
    """Reject oversized images before decoding their pixels."""

    from PIL import Image
    from app.converter import convert_image

    source = tmp_path / "oversized.png"
    source.write_bytes(b"fake image for testing")

    class FakeImage:
        size = (5000, 5000)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def load(self):
            raise AssertionError(
                "Oversized image must not be decoded."
            )

    # Simulate opening a 25-million-pixel image
    monkeypatch.setattr(
        Image,
        "open",
        lambda *args, **kwargs: FakeImage()
    )

    # FileFlow should reject it before calling load()
    with pytest.raises(ValueError, match="too large"):
        convert_image(source, "JPG")


def test_temporary_file_cleanup(tmp_path, monkeypatch):
    """Check that failed conversions remove temporary files."""

    from PIL import Image
    from app.converter import convert_image

    # Create a valid source image
    source = tmp_path / "sample.jpg"
    Image.new("RGB", (100, 100), "blue").save(source)

    # Remember the files that existed before conversion
    files_before = set(tmp_path.iterdir())

    # Simulate a failure while saving the image
    def fake_save(self, fp, *args, **kwargs):
        # Write incomplete data to the temporary file
        with open(fp, "wb") as file:
            file.write(b"incomplete data")

        raise OSError("Simulated disk write failure")

    # Replace Pillow's save function during this test
    monkeypatch.setattr(Image.Image, "save", fake_save)

    # The conversion should fail
    with pytest.raises(ValueError, match="Simulated disk write failure"):
        convert_image(source, "PNG")

    # No temporary or incomplete files should remain
    files_after = set(tmp_path.iterdir())

    assert files_after == files_before
    

def test_pdf_cleanup_after_failure(tmp_path, monkeypatch):
    """Check that a failed PDF conversion leaves no partial ZIP."""

    import pytest
    import pymupdf
    from app import pdf_converter

    # Create a PDF with three pages
    source = tmp_path / "document.pdf"

    with pymupdf.open() as document:
        for _ in range(3):
            document.new_page()
        document.save(source)

    # Create an existing ZIP that must not be overwritten
    existing_zip = tmp_path / "document.zip"
    existing_zip.write_bytes(b"existing file")

    # Remember all files before the conversion
    files_before = set(tmp_path.iterdir())

    # Keep the real rendering function
    original_render = pdf_converter.render_page
    calls = 0

    def failing_render(page, image_path):
        nonlocal calls
        calls += 1

        # Let the first page convert successfully
        if calls == 1:
            return original_render(page, image_path)

        # Simulate a failure on the second page
        raise OSError("Simulated PDF rendering failure")

    # Temporarily replace the rendering function
    monkeypatch.setattr(
        pdf_converter,
        "render_page",
        failing_render
    )

    # Conversion should raise an error
    with pytest.raises(
        ValueError,
        match="Simulated PDF rendering failure"
    ):
        pdf_converter.convert_pdf(source, "PNG")

    # Check no new files or temporary folders remain
    files_after = set(tmp_path.iterdir())

    assert files_after == files_before

    # Existing ZIP must remain unchanged
    assert existing_zip.read_bytes() == b"existing file"

    # Confirm the test actually reached page 2
    assert calls == 2

