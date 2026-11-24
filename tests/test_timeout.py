
import subprocess
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from api import server


def test_conversion_timeout(monkeypatch):
    """A timed-out worker should return HTTP 504."""

    # Enable subprocess mode for this test
    monkeypatch.setenv("FILEFLOW_USE_SUBPROCESS", "1")

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=args[0],
            timeout=25
        )

    # Simulate a subprocess that exceeds its time limit
    monkeypatch.setattr(
        server.subprocess,
        "run",
        fake_run
    )

    # Create a small valid PNG upload
    image = BytesIO()
    Image.new("RGB", (10, 10), "blue").save(
        image,
        format="PNG"
    )

    client = TestClient(server.app)

    response = client.post(
        "/convert",
        files={
            "file": (
                "sample.png",
                BytesIO(image.getvalue()),
                "image/png"
            )
        },
        data={"output_format": "JPG"}
    )

    assert response.status_code == 504
    assert "too long" in response.json()["detail"]

    # Confirm the request released its conversion slot
    assert server.conversion_slots.acquire(blocking=False)
    server.conversion_slots.release()
