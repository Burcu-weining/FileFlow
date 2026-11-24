
import sys
from pathlib import Path

from app.converter import convert_image
from app.pdf_converter import convert_pdf
from api.resource_limits import apply_resource_limits


def main():
    """Convert one file inside a protected worker process."""

    if len(sys.argv) != 3:
        print(
            "Invalid worker arguments.",
            file=sys.stderr
        )
        return 1

    input_path = Path(sys.argv[1])
    output_format = sys.argv[2]

    try:
        # Apply Linux resource limits to this worker
        # before processing the uploaded file.
        apply_resource_limits()

        # Choose the correct conversion engine
        if input_path.suffix.lower() == ".pdf":
            output_path = convert_pdf(
                input_path,
                output_format
            )
        else:
            output_path = convert_image(
                input_path,
                output_format
            )

        # Tell the API where the finished file is
        print(str(output_path))
        return 0

    except MemoryError:
        print(
            "RESOURCE: Conversion exceeded available memory.",
            file=sys.stderr
        )
        return 3

    except (ValueError, FileNotFoundError, OSError) as error:
        print(
            f"VALIDATION: {error}",
            file=sys.stderr
        )
        return 2

    except Exception:
        print(
            "Conversion failed unexpectedly.",
            file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
