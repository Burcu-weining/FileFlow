
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZIP_DEFLATED

import pymupdf


MAX_PAGES = 20
MAX_PIXELS = 20_000_000
DPI = 150


def publish_file(temp_path, output_path):
    """Publish a finished file without overwriting existing files."""

    counter = 0

    while True:
        if counter == 0:
            candidate = output_path
        else:
            candidate = output_path.with_name(
                f"{output_path.stem}_{counter}{output_path.suffix}"
            )

        try:
            # Create a hard link only if the filename is available.
            # The complete temporary file is already written.
            os.link(temp_path, candidate)
            return candidate

        except FileExistsError:
            counter += 1


def render_page(page, image_path):
    """Render one PDF page to an image."""

    # Calculate expected image dimensions
    width = page.rect.width * DPI / 72
    height = page.rect.height * DPI / 72

    if width <= 0 or height <= 0:
        raise ValueError("Invalid PDF page dimensions.")

    if width * height > MAX_PIXELS:
        raise ValueError("PDF page is too large.")

    # Render the page at 150 DPI
    pixmap = page.get_pixmap(
        dpi=DPI,
        colorspace=pymupdf.csRGB,
        alpha=False
    )

    # Check the actual rendered pixel count too
    if pixmap.width * pixmap.height > MAX_PIXELS:
        raise ValueError("Rendered PDF page is too large.")

    # Save as JPG or PNG according to the filename
    pixmap.save(str(image_path))


def convert_pdf(input_path, output_format):
    """Convert PDF pages into JPG or PNG images."""

    input_file = Path(input_path)
    output_format = output_format.strip().upper()

    # Check input file
    if not input_file.is_file():
        raise FileNotFoundError("PDF file not found.")

    if input_file.suffix.lower() != ".pdf":
        raise ValueError("Input must be a PDF file.")

    if output_format not in ("PNG", "JPG"):
        raise ValueError(
            "PDF can only convert to PNG or JPG."
        )

    extension = output_format.lower()

    try:
        with pymupdf.open(input_file) as document:

            # Reject password-protected PDFs
            if document.needs_pass:
                raise ValueError(
                    "Password-protected PDFs are not supported."
                )

            page_count = document.page_count

            if page_count == 0:
                raise ValueError("The PDF contains no pages.")

            if page_count > MAX_PAGES:
                raise ValueError(
                    f"Maximum {MAX_PAGES} PDF pages supported."
                )

            # Temporary files stay in the same directory
            # as the original PDF.
            with TemporaryDirectory(
                dir=input_file.parent,
                prefix=".fileflow-"
            ) as temp_dir:

                temp_folder = Path(temp_dir)

                # Single-page PDF -> JPG or PNG
                if page_count == 1:
                    temp_image = (
                        temp_folder / f"page.{extension}"
                    )

                    render_page(document[0], temp_image)

                    output_path = input_file.with_suffix(
                        "." + extension
                    )

                    # Publish only after the image is complete
                    return publish_file(
                        temp_image,
                        output_path
                    )

                # Multi-page PDF -> ZIP
                temp_zip = temp_folder / "converted.zip"

                with ZipFile(
                    temp_zip,
                    "w",
                    ZIP_DEFLATED
                ) as archive:

                    for page_number, page in enumerate(
                        document, start=1
                    ):

                        filename = (
                            f"page_{page_number:03d}.{extension}"
                        )

                        temp_image = temp_folder / filename

                        render_page(page, temp_image)

                        archive.write(
                            temp_image,
                            arcname=filename
                        )

                        # Remove the image after adding to ZIP
                        temp_image.unlink()

                output_path = input_file.with_suffix(".zip")

                # Publish the ZIP only after every page succeeds
                return publish_file(
                    temp_zip,
                    output_path
                )

    except (ValueError, FileNotFoundError):
        raise

    except Exception as error:
        raise ValueError(
            f"Unable to process PDF: {error}"
        ) from error
