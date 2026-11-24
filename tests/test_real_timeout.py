
from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from api import server


def test_real_subprocess_timeout(monkeypatch):
    """Verify a real conversion worker is terminated on timeout."""

    # Enable the actual subprocess conversion mode
    monkeypatch.setenv("FILEFLOW_USE_SUBPROCESS", "1")

    # Use a tiny timeout so the process cannot finish
    # starting Python before the timeout expires
    monkeypatch.setattr(
        server,
        "CONVERSION_TIMEOUT_SECONDS",
        0.001
    )

    # Track temporary folders created by the API
    original_temp_directory = server.TemporaryDirectory
    created_folders = []

    def tracked_temp_directory(*args, **kwargs):
        temp_dir = original_temp_directory(
            *args, **kwargs
        )
        created_folders.append(Path(temp_dir.name))
        return temp_dir

    monkeypatch.setattr(
        server,
        "TemporaryDirectory",
        tracked_temp_directory
    )

    # Create a valid test image in memory
    image = BytesIO()

    Image.new(
        "RGB",
        (100, 100),
        "purple"
    ).save(image, format="PNG")

    image_bytes = image.getvalue()

    # Send an actual API conversion request
    with TestClient(server.app) as client:
        response = client.post(
            "/convert",
            files={
                "file": (
                    "test.png",
                    BytesIO(image_bytes),
                    "image/png"
                )
            },
            data={
                "output_format": "JPG"
            }
        )

    # A real subprocess should exceed the tiny limit
    assert response.status_code == 504

    assert "too long" in (
        response.json()["detail"].lower()
    )

    # Confirm temporary folders were created
    assert created_folders

    # Confirm the API cleaned them up
    for folder in created_folders:
        assert not folder.exists()

    # Confirm the conversion slot was released
    assert server.conversion_slots.acquire(
        blocking=False
    )

    server.conversion_slots.release()
