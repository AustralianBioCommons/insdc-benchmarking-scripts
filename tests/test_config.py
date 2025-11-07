"""Tests for configuration module"""

from insdc_benchmarking_scripts.utils.config import load_config, DEFAULT_CONFIG


def test_load_default_config(tmp_path):
    """Test loading default config when file doesn't exist"""
    config_path = tmp_path / "nonexistent.yaml"
    config = load_config(config_path)

    assert config == DEFAULT_CONFIG
    assert config["site"] == "nci"


def test_load_custom_config(tmp_path):
    """Test loading custom config from file"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("""
        site: pawsey
        api_endpoint: https://custom.api.com/submit
        timeout: 600
            """)

    config = load_config(config_path)

    assert config["site"] == "pawsey"
    assert config["api_endpoint"] == "https://custom.api.com/submit"
    assert config["timeout"] == 600
    # Should merge with defaults
    assert config["cleanup"]  # From default


def test_config_merge_with_defaults(tmp_path):
    """Test that custom config merges with defaults"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("site: test_site")

    config = load_config(config_path)

    # Custom value
    assert config["site"] == "test_site"
    # Default values
    assert "download_dir" in config
    assert "cleanup" in config
    assert "timeout" in config
