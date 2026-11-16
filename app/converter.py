
import os
import tempfile
from pathlib import Path

from PIL import Image, UnidentifiedImageError


# Supported output formats
SUPPORTED_FORMATS = {
    "JPG": "JPEG",
    "JPEG": "JPEG",
    "PNG": "PNG",
    "WEBP": "WEBP",
    "PDF": "PDF"
}

# Supported input formats
SUPPORTED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp"
}

# Maximum image size: 20 million pixels
MAX_IMAGE_PIXELS = 20_000_000


def get_unique_path(output_path):
    """Find a filename that does not already exist."""

    counter = 1
    new_path = output_path

    while new_path.exists():
        new_path = output_path.with_name(
            f"{output_path.stem}_{counter}{output_path.suffix}"
        )
        counter += 1

    return new_path


def convert_image(input_path, output_format):
    """Convert an image safely into JPG, PNG, WEBP, or PDF."""

    input_file = Path(input_path)
    output_format = output_format.strip().upper()

    # Step 1: Check that the input file exists
    if not input_file.is_file():
        raise FileNotFoundError(
            "The input file does not exist."
        )

    # Step 2: Check the input extension
    if input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            "Unsupported input file format."
        )

    # Step 3: Check the output format
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(
            "Unsupported output file format."
        )

    # Step 4: Determine the output extension
    extension = (
        "jpg" if output_format in ("JPG", "JPEG")
        else output_format.lower()
    )

    output_file = input_file.with_suffix("." + extension)

    # Avoid existing filenames
    output_file = get_unique_path(output_file)

    # Temporary output path, initially unset
    temp_path = None

    try:
        with Image.open(input_file) as img:

            # Step 5: Check image dimensions before decoding
            width, height = img.size

            if width * height > MAX_IMAGE_PIXELS:
                raise ValueError(
                    "Image is too large. "
                    "Maximum allowed size is 20 million pixels."
                )

            img.load()

            # Step 6: Handle transparency for JPG/PDF
            if output_format in ("JPG", "JPEG", "PDF"):

                rgba = img.convert("RGBA")

                background = Image.new(
                    "RGB",
                    rgba.size,
                    (255, 255, 255)
                )

                background.paste(
                    rgba,
                    mask=rgba.getchannel("A")
                )

                img = background

            # Step 7: Create a temporary file in
            # the same folder as the final output
            with tempfile.NamedTemporaryFile(
                dir=output_file.parent,
                suffix=output_file.suffix,
                delete=False
            ) as temporary:
                temp_path = Path(temporary.name)

            # Step 8: Save to the temporary file first
            img.save(
                temp_path,
                format=SUPPORTED_FORMATS[output_format]
            )

            # Step 9: Publish the completed file
            # using a new filename if necessary
            while True:
                output_file = get_unique_path(output_file)

                try:
                    # Exclusive creation prevents overwriting
                    # an existing file
                    with output_file.open("xb") as destination:
                        pass

                    break

                except FileExistsError:
                    continue

            try:
                os.replace(temp_path, output_file)
                temp_path = None

            except Exception:
                # Remove the reserved output filename
                output_file.unlink(missing_ok=True)
                raise

    except (
        UnidentifiedImageError,
        Image.DecompressionBombError,
        OSError,
        ValueError
    ) as error:
        raise ValueError(
            f"Unable to convert file: {error}"
        ) from error

    finally:
        # Delete temporary files after failures
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    return output_file
