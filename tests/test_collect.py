import pytest

from datetime import datetime

from drift.collect import compare_limits, parse_mem_limit
from drift.models import ContainerSnapshot, DriftKind


def test_megabytes():
    """'500m' converts to 524288000."""
    assert parse_mem_limit("500m") == 524288000

def test_small_megabytes():
    """'64m' converts to 67108864."""
    assert parse_mem_limit("64m") == 67108864

def test_gigabytes():
    """'1g' converts to 1073741824."""
    assert parse_mem_limit("1g") == 1073741824

def test_bad_unit_raises():
    """'lots' raises ValueError (use pytest.raises)."""
    with pytest.raises(ValueError):
        parse_mem_limit("lots")

def make_snap(name: str, mem_bytes: int) -> ContainerSnapshot:
    """A fake snapshot: only name and mem_bytes matter for compare purposes"""
    return ContainerSnapshot(
        name=name,
        image="test:latest",
        image_id="sha256:test",
        restart_count=0,
        started_at=datetime(2026, 10, 1),
        mem_bytes=mem_bytes,
        taken_at=datetime(2026, 10, 1))

def test_no_drift():
    """Compose and reality match -> empty list"""
    expected = {"pihole": 256}
    snaps = [make_snap("pihole", 256)]
    assert compare_limits(expected, snaps) == []

def test_mem_mismatch():
    """Same container, different memory -> MEM_MISMATCH"""
    expected = {"pihole": 256}
    snaps = [make_snap("pihole", 512)]
    assert compare_limits(expected, snaps) == [("pihole", DriftKind.MEM_MISMATCH)]

def test_missing():
    """When one of the items is not running"""
    expected = {"pihole": 256, "grafana": 500}
    snaps = [make_snap("pihole", 256)]
    assert compare_limits(expected, snaps) == [("grafana", DriftKind.MISSING)]

def test_unexpected():
    """Test when a service is running that's not in the expected ones"""
    expected = {"pihole": 256}
    snaps = [make_snap("pihole", 256), make_snap("dozzle", 128)]
    assert compare_limits(expected, snaps) == [("dozzle", DriftKind.UNEXPECTED)]
