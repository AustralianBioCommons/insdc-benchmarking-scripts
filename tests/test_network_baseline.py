"""Tests for network baseline module"""

from insdc_benchmarking_scripts.utils.network_baseline import (
    measure_latency,
    get_network_baseline,
)


def test_measure_latency_valid_host():
    """Test latency measurement to a valid host"""
    # Use a reliable public DNS server
    latency = measure_latency("8.8.8.8")

    if latency is not None:
        assert isinstance(latency, float)
        assert latency > 0
        assert latency < 1000  # Should be less than 1 second


def test_measure_latency_invalid_host():
    """Test latency measurement to invalid host"""
    latency = measure_latency("invalid.host.that.does.not.exist.local")

    # Should return None for invalid hosts
    assert latency is None


def test_get_network_baseline():
    """Test getting network baseline"""
    baseline = get_network_baseline("8.8.8.8")

    assert "network_latency_ms" in baseline
    assert "network_path" in baseline
    assert "packet_loss_percent" in baseline
