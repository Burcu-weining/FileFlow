
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from api import server


def test_conversion_rate_limit(monkeypatch):
    """Check that excessive conversion requests return HTTP 429."""

    client = TestClient(server.app)

    # Simulate a successful, lightweight conversion
    def fake_conversion(input_path, output_format):
        output_path = input_path.with_suffix(".jpg")
        output_path.write_bytes(b"test output")
        return output_path

    monkeypatch.setattr(
        server,
        "convert_image",
        fake_conversion
    )

    # Clear the in-memory rate-limit counters
    # before and after this test.
    server.limiter._storage.reset()

    try:
        # Create a tiny valid PNG
        image = BytesIO()
        Image.new("RGB", (10, 10), "purple").save(
            image,
            format="PNG"
        )
        image_bytes = image.getvalue()

        responses = []

        # Send 21 conversion requests
        for _ in range(21):
            response = client.post(
                "/convert",
                files={
                    "file": (
                        "test.png",
                        BytesIO(image_bytes),
                        "image/png"
                    )
                },
                data={"output_format": "JPG"}
            )
            responses.append(response)

        # The first 20 should succeed
        for response in responses[:20]:
            assert response.status_code == 200

        # The 21st request should be blocked
        assert responses[20].status_code == 429

        assert "Too many conversions" in (
            responses[20].json()["detail"]
        )

    finally:
        server.limiter._storage.reset()
