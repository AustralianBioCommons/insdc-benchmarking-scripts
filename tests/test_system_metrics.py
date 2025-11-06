"""Tests for system metrics module"""

import pytest
import time
from insdc_benchmarking_scripts.utils.system_metrics import SystemMonitor, get_baseline_metrics


def test_system_monitor_initialization():
    """Test SystemMonitor initialization"""
    monitor = SystemMonitor()

    assert monitor.cpu_samples == []
    assert monitor.memory_samples == []
    assert monitor.start_time is None


def test_system_monitor_start():
    """Test starting monitoring"""
    monitor = SystemMonitor()
    monitor.start()

    assert monitor.start_time is not None
    assert monitor.cpu_samples == []
    assert monitor.memory_samples == []


def test_system_monitor_sample():
    """Test taking a sample"""
    monitor = SystemMonitor()
    monitor.start()

    monitor.sample()
    time.sleep(0.2)
    monitor.sample()

    assert len(monitor.cpu_samples) >= 1
    assert len(monitor.memory_samples) >= 1


def test_system_monitor_averages():
    """Test getting averages"""
    monitor = SystemMonitor()
    monitor.start()

    for _ in range(3):
        monitor.sample()
        time.sleep(0.1)

    averages = monitor.get_averages()

    assert 'cpu_usage_percent' in averages
    assert 'memory_usage_mb' in averages
    assert isinstance(averages['cpu_usage_percent'], float)
    assert isinstance(averages['memory_usage_mb'], float)


def test_system_monitor_empty_averages():
    """Test averages with no samples"""
    monitor = SystemMonitor()
    averages = monitor.get_averages()

    assert averages['cpu_usage_percent'] == 0
    assert averages['memory_usage_mb'] == 0


def test_get_baseline_metrics():
    """Test getting baseline metrics"""
    baseline = get_baseline_metrics()

    assert 'write_speed_mbps' in baseline
    # write_speed_mbps can be None if test fails, but should exist
    assert baseline['write_speed_mbps'] is None or isinstance(baseline['write_speed_mbps'], float)