"""KIS authentication status (no secrets exposed)."""

from pathlib import Path

from config import get_settings


def check_kis_status() -> dict[str, str | bool]:
    settings = get_settings()
    config_path = settings.kis_config_resolved
    token_dir = Path.home() / "KIS" / "config"
    token_files = list(token_dir.glob("KIS20*")) if token_dir.exists() else []

    if config_path is None:
        return {
            "configured": False,
            "config_file_exists": False,
            "token_file_exists": len(token_files) > 0,
            "status": "not_configured",
            "message": "KIS config file not found. Set KIS_CONFIG_PATH or install ~/KIS/config/kis_devlp.yaml",
        }

    return {
        "configured": True,
        "config_file_exists": True,
        "token_file_exists": len(token_files) > 0,
        "status": "configured" if token_files else "config_only",
        "message": "KIS config found" if token_files else "Config found; run KIS auth to create token",
    }
