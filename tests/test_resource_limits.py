
import sys
from types import SimpleNamespace

from api import resource_limits


def test_resource_limits_skipped_on_mac(monkeypatch):
    """Local macOS development should remain unrestricted."""

    monkeypatch.setattr(
        resource_limits.platform,
        "system",
        lambda: "Darwin"
    )

    result = resource_limits.apply_resource_limits()

    assert result is False


def test_resource_limits_on_linux(monkeypatch):
    """Linux workers should receive memory and CPU limits."""

    monkeypatch.setattr(
        resource_limits.platform,
        "system",
        lambda: "Linux"
    )

    applied = []

    fake_resource = SimpleNamespace(
        RLIMIT_AS=1,
        RLIMIT_CPU=2,
        RLIM_INFINITY=-1,
        getrlimit=lambda kind: (-1, -1),
        setrlimit=lambda kind, limits: applied.append(
            (kind, limits)
        )
    )

    # Simulate the Linux resource module without
    # modifying real limits on your Mac.
    monkeypatch.setitem(
        sys.modules,
        "resource",
        fake_resource
    )

    result = resource_limits.apply_resource_limits()

    assert result is True

    expected_memory = 384 * 1024 * 1024

    assert (
        1,
        (expected_memory, expected_memory)
    ) in applied

    assert (
        2,
        (20, 22)
    ) in applied
