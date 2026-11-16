
from app.converter import convert_image
from PIL import Image


def test_png_conversion(tmp_path):
    # Create a temporary JPG test image
    source = tmp_path / "sample.jpg"
    Image.new("RGB", (100, 100), "red").save(source)

    # Convert JPG to PNG
    output = convert_image(source, "PNG")

    # Make sure the converted file exists
    assert output.exists()
    assert output.suffix == ".png"

    # Make sure the actual format is PNG
    with Image.open(output) as img:
        assert img.format == "PNG"


def test_no_overwrite(tmp_path):
    source = tmp_path / "sample.jpg"
    Image.new("RGB", (100, 100), "blue").save(source)

    first = convert_image(source, "PNG")
    second = convert_image(source, "PNG")

    # Both conversions should create different files
    assert first != second
    assert first.exists()
    assert second.exists()
    

def test_image_to_pdf(tmp_path):
    from PIL import Image
    import fitz

    # Create a temporary image
    source = tmp_path / "sample.png"
    Image.new("RGB", (200, 200), "blue").save(source)

    # Convert the image to PDF
    output = convert_image(source, "PDF")

    # Check the output exists and has the right extension
    assert output.exists()
    assert output.suffix == ".pdf"

    # Verify the PDF contains one page
    with fitz.open(output) as document:
        assert document.page_count == 1


from app.pdf_converter import convert_pdf
from zipfile import ZipFile
import fitz


def test_single_page_pdf(tmp_path):
    # Create a PDF with one page
    source = tmp_path / "single.pdf"

    with fitz.open() as doc:
        doc.new_page()
        doc.save(source)

    # Convert PDF to PNG
    output = convert_pdf(source, "PNG")

    # Check that the image exists
    assert output.exists()
    assert output.suffix == ".png"


def test_multiple_page_pdf(tmp_path):
    # Create a PDF with three pages
    source = tmp_path / "multiple.pdf"

    with fitz.open() as doc:
        for _ in range(3):
            doc.new_page()

        doc.save(source)

    # Convert PDF to JPG
    output = convert_pdf(source, "JPG")

    # Multi-page PDFs should create ZIP files
    assert output.exists()
    assert output.suffix == ".zip"

    with ZipFile(output) as archive:
        assert archive.namelist() == [
            "page_001.jpg",
            "page_002.jpg",
            "page_003.jpg"
        ]

