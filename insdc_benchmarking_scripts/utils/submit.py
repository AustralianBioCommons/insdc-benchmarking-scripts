"""
Result submission helper.
"""

from __future__ import annotations
import json
from typing import Dict, Any


def submit_result(
    api_endpoint: str, payload: Dict[str, Any], api_token: str = ""
) -> Dict[str, Any]:
    """
    Submit a result payload to the API endpoint. If `requests` is available, POST it.
    Otherwise, just return the payload to the caller (dry-run).
    """
    try:
        import requests  # type: ignore
    except Exception:
        # Fallback: simulate submission
        return {
            "status": "skipped",
            "reason": "requests not installed",
            "payload_preview": json.dumps(payload)[:500],
        }

    headers = {"Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    try:
        r = requests.post(api_endpoint, json=payload, headers=headers, timeout=30)
        return {"status": "ok", "code": r.status_code, "text": r.text[:1000]}
    except Exception as e:
        return {"status": "error", "error": str(e)}
