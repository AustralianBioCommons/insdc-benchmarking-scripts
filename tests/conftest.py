"""Pytest configuration and fixtures"""

import pytest


@pytest.fixture
def temp_config(tmp_path):
    """Fixture providing a temporary config file"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
        site: test
        api_endpoint: https://test.api.com/submit
        download_dir: ./test_downloads
        cleanup: false
        timeout: 60
    """)
    return config_path


@pytest.fixture
def mock_dataset():
    """Fixture providing a mock dataset ID"""
    return "SRR000001"
