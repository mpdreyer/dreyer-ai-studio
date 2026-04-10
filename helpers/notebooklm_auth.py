"""
NotebookLM auth-hjälp — sparar och kontrollerar MCP-cookies.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

AUTH_FILE = Path.home() / ".notebooklm-mcp" / "auth.json"


def save_cookies(cookie_string: str) -> bool:
    """Parsar cookie-sträng och sparar till auth-fil."""
    AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    cookies = {}
    for part in cookie_string.split(";"):
        part = part.strip()
        if "=" in part:
            key, _, val = part.partition("=")
            cookies[key.strip()] = val.strip()
    auth_data = {
        "cookies":  cookies,
        "saved_at": str(datetime.now()),
    }
    AUTH_FILE.write_text(json.dumps(auth_data, indent=2))
    return True


def check_auth_status() -> dict:
    """Returnerar auth-status och tidpunkt för senaste sparning."""
    if not AUTH_FILE.exists():
        return {"status": "no_auth", "message": "Ingen auth-fil hittad"}
    try:
        data = json.loads(AUTH_FILE.read_text())
        return {
            "status":   "ok",
            "saved_at": data.get("saved_at", "okänt"),
            "n_cookies": len(data.get("cookies", {})),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def check_mcp_process() -> bool:
    """Returnerar True om notebooklm-mcp-processen körs."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "notebooklm-mcp"],
            capture_output=True, timeout=3,
        )
        return result.returncode == 0
    except Exception:
        return False
