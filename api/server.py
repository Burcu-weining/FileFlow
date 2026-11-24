from fastapi.responses import RedirectResponse
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import BoundedSemaphore

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask

from app.converter import convert_image, SUPPORTED_FORMATS
from app.pdf_converter import convert_pdf


# Create the FileFlow API
app = FastAPI(title="FileFlow API")


# Resource limits
MAX_FILE_SIZE = 10 * 1024 * 1024
MAX_OUTPUT_SIZE = 50 * 1024 * 1024
MAX_CONCURRENT_CONVERSIONS = 2

# Limit how many conversions can run at once
conversion_slots = BoundedSemaphore(
    MAX_CONCURRENT_CONVERSIONS
)

# Accepted input file extensions
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".pdf"
}


# Serve the FileFlow website
app.mount(
    "/web",
    StaticFiles(directory="web", html=True),
    name="web"
)


from fastapi.responses import RedirectResponse

@app.get("/")
def home():
    """Redirect visitors to the FileFlow website."""
    return RedirectResponse(url="/web/")

    
@app.get("/health")
def health_check():
    """Check whether the FileFlow API is running."""

    return {
        "status": "healthy",
        "service": "FileFlow"
    }


@app.post("/convert")
def convert_file(
    file: UploadFile = File(...),
    output_format: str = Form(...)
):
    """Upload, convert, and download a file safely."""

    # Standardize the requested output format
    output_format = output_format.strip().upper()

    # Check the output format
    if output_format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported output format."
        )

    # Safely extract the filename
    filename = Path(
        (file.filename or "upload").replace("\\", "/")
    ).name

    extension = Path(filename).suffix.lower()

    # Check the input format
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported input format."
        )

    # PDF input supports JPG and PNG output only
    if extension == ".pdf":
        if output_format not in ("PNG", "JPG"):
            raise HTTPException(
                status_code=400,
                detail="PDF can only convert to PNG or JPG."
            )

    # Check whether a conversion slot is available
    slot_acquired = conversion_slots.acquire(
        blocking=False
    )

    if not slot_acquired:
        raise HTTPException(
            status_code=503,
            detail=(
                "FileFlow is busy. "
                "Please try again shortly."
            ),
            headers={"Retry-After": "5"}
        )

    temp_dir = None

    try:
        # Create a temporary folder for the uploaded file
        temp_dir = TemporaryDirectory()
        folder = Path(temp_dir.name)

        input_path = folder / f"input{extension}"

        # Save the upload in chunks with a size limit
        total_size = 0

        with input_path.open("wb") as destination:

            while True:
                chunk = file.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Maximum file size is 10 MB."
                    )

                destination.write(chunk)

        # Convert using the appropriate engine
        if extension == ".pdf":
            output_path = convert_pdf(
                input_path,
                output_format
            )
        else:
            output_path = convert_image(
                input_path,
                output_format
            )

        output_path = Path(output_path)

        # Validate the converted output
        if not output_path.is_file():
            raise HTTPException(
                status_code=500,
                detail="Conversion did not produce a file."
            )

        # Check the final download size
        if output_path.stat().st_size > MAX_OUTPUT_SIZE:
            raise HTTPException(
                status_code=413,
                detail=(
                    "Converted file is too large. "
                    "Maximum output size is 50 MB."
                )
            )

        # Set the filename for the download
        download_name = (
            Path(filename).stem + output_path.suffix
        )

        # Identify the file type
        media_types = {
            ".zip": "application/zip",
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp"
        }

        media_type = media_types.get(
            output_path.suffix.lower(),
            "application/octet-stream"
        )

        # Clean up after the download finishes
        response = FileResponse(
            path=output_path,
            filename=download_name,
            media_type=media_type,
            background=BackgroundTask(temp_dir.cleanup)
        )

        # Cleanup now belongs to the response
        temp_dir = None

        return response

    except HTTPException:
        # Preserve the correct HTTP status code
        raise

    except (ValueError, OSError) as error:
        # Handle invalid or corrupted files
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    finally:
        # Free the conversion slot
        conversion_slots.release()

        # Close the uploaded file
        file.file.close()

        # Clean up if the request failed
        if temp_dir is not None:
            temp_dir.cleanup()
