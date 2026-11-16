
from io import BytesIO

from fastapi.testclient import TestClient
from api.server import app


client = TestClient(app)


def test_oversized_upload():
    # Create a fake 11 MB image upload
    oversized_file = BytesIO(
        b"x" * (11 * 1024 * 1024)
    )

    response = client.post(
        "/convert",
        files={
            "file": (
                "large.jpg",
                oversized_file,
                "image/jpeg"
            )
        },
        data={
            "output_format": "PNG"
        }
    )
    print("Status:", response.status_code)
    print("Response:", response.json())
    
    # The API should reject the oversized upload
    assert response.status_code == 413


def test_server_busy():
    """Reject conversions when both slots are occupied."""

    from io import BytesIO

    from fastapi.testclient import TestClient
    from PIL import Image

    from api.server import app, conversion_slots

    client = TestClient(app)

    # Create a small valid image
    image = BytesIO()
    Image.new("RGB", (20, 20), "blue").save(
        image,
        format="PNG"
    )
    image.seek(0)

    # Simulate two ongoing conversions
    conversion_slots.acquire()
    conversion_slots.acquire()

    try:
        response = client.post(
            "/convert",
            files={
                "file": (
                    "test.png",
                    image,
                    "image/png"
                )
            },
            data={"output_format": "JPG"}
        )

        # The server should reject another conversion
        assert response.status_code == 503
        assert "busy" in response.json()["detail"].lower()

    finally:
        # Always release the slots after testing
        conversion_slots.release()
        conversion_slots.release()


def test_output_size_limit(tmp_path, monkeypatch):
    """Reject converted outputs larger than 50 MB."""

    from io import BytesIO
    import importlib

    from fastapi.testclient import TestClient
    from PIL import Image

    server = importlib.import_module("api.server")
    client = TestClient(server.app)

    # Create a small valid uploaded image
    image = BytesIO()
    Image.new("RGB", (20, 20), "red").save(
        image,
        format="PNG"
    )
    image.seek(0)

    # Simulate a converter producing a very large file
    def fake_conversion(input_path, output_format):
        output_path = input_path.with_suffix(".jpg")

        # Create a large file without allocating 51 MB
        # of data in memory
        with output_path.open("wb") as output:
            output.truncate(51 * 1024 * 1024)

        return output_path

    monkeypatch.setattr(
        server,
        "convert_image",
        fake_conversion
    )

    response = client.post(
        "/convert",
        files={
            "file": (
                "test.png",
                image,
                "image/png"
            )
        },
        data={"output_format": "JPG"}
    )

    assert response.status_code == 413
    assert "50 MB" in response.json()["detail"]

