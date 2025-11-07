"""
Configuration loader for INSDC benchmarking scripts.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "site": "nci",
    "api_endpoint": "https://api.example.com/submit",
    "api_token": "",
    "download_dir": "./downloads",
    "cleanup": True,
    "timeout": 300,
}


def _merge_defaults(user_cfg: Dict[str, Any]) -> Dict[str, Any]:
    merged = DEFAULT_CONFIG.copy()
    merged.update(user_cfg or {})
    return merged


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file if present, otherwise return defaults.
    If PyYAML is unavailable, falls back to defaults.
    """
    # Determine default path: look for a `config.yaml` two levels up from utils/
    if config_path is None:
        repo_root = Path(__file__).resolve().parents[2]
        default_path = repo_root / "config.yaml"
        config_path = default_path

    config_path = Path(config_path)

    if not config_path.exists():
        return DEFAULT_CONFIG.copy()

    # Try to parse YAML (preferred). If missing, return defaults.
    try:
        import yaml  # type: ignore
    except Exception:
        return DEFAULT_CONFIG.copy()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return DEFAULT_CONFIG.copy()
        return _merge_defaults(data)
    except Exception:
        # On any parse error, fall back to defaults
        return DEFAULT_CONFIG.copy()
