"""KIS token/session bootstrap (calls open-trading-api kis_auth without modifying it)."""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from types import ModuleType

import requests
import yaml

from config import get_settings
from services.kis.kis_loader import _ensure_paths

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_auth_ready = False
_last_svr: str | None = None
_ka: ModuleType | None = None


def get_kis_auth_module() -> ModuleType:
    """Return the same kis_auth module used by domestic_stock_functions."""
    global _ka
    _ensure_paths()
    if _ka is None:
        import kis_auth

        _ka = kis_auth
    return _ka


def _token_path(config_root: str, svr: str) -> str:
    """Separate token files for prod vs vps (do not share)."""
    return os.path.join(config_root, f"KIS{svr}{datetime.today().strftime('%Y%m%d')}")


def _reload_kis_config(ka: ModuleType, svr: str) -> Path | None:
    """Apply workspace KIS_CONFIG_PATH and svr-specific token path."""
    settings = get_settings()
    path = settings.kis_config_resolved
    if path is None:
        return None

    config_root = str(path.parent)
    ka.config_root = config_root
    ka.token_tmp = _token_path(config_root, svr)
    with open(path, encoding="UTF-8") as f:
        ka._cfg = yaml.load(f, Loader=yaml.FullLoader)
    return path


def _key_status(cfg: dict, svr: str) -> dict[str, bool]:
    if svr == "vps":
        app_key, sec_key = "paper_app", "paper_sec"
    else:
        app_key, sec_key = "my_app", "my_sec"
    app_val = str(cfg.get(app_key, "")).strip()
    sec_val = str(cfg.get(sec_key, "")).strip()
    placeholder = {"", "앱키", "앱시크리트", "모의투자 앱키", "your_app_key"}
    return {
        "app_key_set": bool(app_val) and app_val not in placeholder,
        "app_secret_set": bool(sec_val) and sec_val not in placeholder,
    }


def _clear_auth_header(ka: ModuleType) -> None:
    ka._base_headers.pop("authorization", None)


def _read_token_safe(ka: ModuleType) -> str | None:
    """Drop empty/corrupt token files so read_token can re-issue."""
    path = ka.token_tmp
    if os.path.isfile(path) and os.path.getsize(path) == 0:
        try:
            os.remove(path)
            logger.warning("Removed empty KIS token file: %s", path)
        except OSError:
            pass
    return ka.read_token()


def _issue_token(ka: ModuleType, svr: str) -> str:
    """Request OAuth token from KIS and save to token file."""
    cfg = ka._cfg
    keys = _key_status(cfg, svr)
    if not keys["app_key_set"] or not keys["app_secret_set"]:
        raise RuntimeError(
            f"KIS yaml keys missing for svr={svr}. "
            f"Use paper_app/paper_sec for vps, my_app/my_sec for prod."
        )

    app_key = "paper_app" if svr == "vps" else "my_app"
    sec_key = "paper_sec" if svr == "vps" else "my_sec"
    payload = {
        "grant_type": "client_credentials",
        "appkey": cfg[app_key],
        "appsecret": cfg[sec_key],
    }
    url = f"{cfg[svr]}/oauth2/tokenP"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "charset": "UTF-8",
        "User-Agent": cfg.get("my_agent", "Mozilla/5.0"),
    }

    _clear_auth_header(ka)
    res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=15)

    if res.status_code != 200:
        try:
            err = res.json()
            msg = err.get("error_description") or err.get("msg1") or res.text[:200]
            code = err.get("error_code") or err.get("msg_cd")
        except Exception:
            msg = res.text[:200] or f"HTTP {res.status_code}"
            code = None
        raise RuntimeError(
            f"KIS token rejected (HTTP {res.status_code}, code={code}): {msg}. "
            f"svr={svr}, url={cfg[svr]}. "
            "모의 앱키는 paper_app/paper_sec + KIS_SVR=vps, 실전은 my_app/my_sec + prod."
        )

    body = res.json()
    token = body.get("access_token")
    expired = body.get("access_token_token_expired")
    if not token or not expired:
        raise RuntimeError("KIS token response missing access_token or expiry")

    ka.save_token(token, expired)
    logger.info("KIS token saved for svr=%s", svr)
    return token


def _apply_trading_env(ka: ModuleType, token: str, svr: str) -> None:
    product = ka._cfg.get("my_prod", "01")
    ka.changeTREnv(token, svr, product)
    ka._base_headers["authorization"] = f"Bearer {token}"
    ka._base_headers["appkey"] = ka.getTREnv().my_app
    ka._base_headers["appsecret"] = ka.getTREnv().my_sec


def request_token(svr: str = "prod") -> dict:
    """Request OAuth token and return safe diagnostic info (no secrets)."""
    ka = get_kis_auth_module()
    config_path = _reload_kis_config(ka, svr)
    if config_path is None:
        return {
            "ok": False,
            "reason": "config_missing",
            "message": "kis_devlp.yaml not found. Set KIS_CONFIG_PATH or use ~/KIS/config/kis_devlp.yaml",
        }

    cfg = ka._cfg
    keys = _key_status(cfg, svr)
    if not keys["app_key_set"] or not keys["app_secret_set"]:
        return {
            "ok": False,
            "reason": "invalid_keys",
            "message": f"Check {svr} keys in kis_devlp.yaml (paper_* for vps, my_* for prod).",
            "svr": svr,
            **keys,
            "config_path": str(config_path),
        }

    app_key = "paper_app" if svr == "vps" else "my_app"
    sec_key = "paper_sec" if svr == "vps" else "my_sec"
    payload = {
        "grant_type": "client_credentials",
        "appkey": cfg[app_key],
        "appsecret": cfg[sec_key],
    }
    url = f"{cfg[svr]}/oauth2/tokenP"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "charset": "UTF-8",
        "User-Agent": cfg.get("my_agent", "Mozilla/5.0"),
    }

    try:
        _clear_auth_header(ka)
        res = requests.post(url, data=json.dumps(payload), headers=headers, timeout=15)
    except requests.RequestException as exc:
        return {
            "ok": False,
            "reason": "network_error",
            "message": str(exc)[:200],
            "svr": svr,
            "config_path": str(config_path),
        }

    result = {
        "ok": res.status_code == 200,
        "status_code": res.status_code,
        "svr": svr,
        "config_path": str(config_path),
        "token_file": ka.token_tmp,
        **keys,
    }

    if res.status_code == 200:
        body = res.json()
        token = body.get("access_token")
        expired = body.get("access_token_token_expired")
        if token and expired:
            ka.save_token(token, expired)
        result["message"] = "token_issued"
        result["expires"] = expired
        return result

    try:
        err = res.json()
        result["error_code"] = err.get("error_code") or err.get("msg_cd")
        result["message"] = err.get("error_description") or err.get("msg1") or res.text[:200]
    except Exception:
        result["message"] = res.text[:200] or f"HTTP {res.status_code}"

    result["reason"] = "kis_api_rejected"
    return result


def ensure_kis_authenticated(svr: str | None = None) -> None:
    """
    Issue or load OAuth token and populate KIS _TRENV.
    Does not use kis_auth.auth() (it prints and returns on failure without raising).
    """
    global _auth_ready, _last_svr
    settings = get_settings()
    svr = (svr or settings.kis_svr or "prod").lower().strip()
    if svr not in ("prod", "vps"):
        raise RuntimeError(f"Invalid KIS_SVR={svr}. Use prod or vps.")

    ka = get_kis_auth_module()
    config_path = _reload_kis_config(ka, svr)
    if config_path is None:
        raise RuntimeError(
            "kis_devlp.yaml not found. Set KIS_CONFIG_PATH or ~/KIS/config/kis_devlp.yaml"
        )

    with _lock:
        if _last_svr != svr:
            _auth_ready = False
        _last_svr = svr

        trenv = ka.getTREnv()
        if _auth_ready and hasattr(trenv, "my_url"):
            return

        token = _read_token_safe(ka)
        if not token:
            logger.info("Requesting new KIS token (svr=%s)", svr)
            token = _issue_token(ka, svr)
        else:
            logger.info("Using cached KIS token (svr=%s)", svr)

        _apply_trading_env(ka, token, svr)

        trenv = ka.getTREnv()
        if not hasattr(trenv, "my_url"):
            raise RuntimeError(
                "KIS trading environment not initialized. "
                "Check my_paper_stock (vps) or my_acct_stock (prod) in kis_devlp.yaml."
            )
        _auth_ready = True


def reset_kis_auth() -> None:
    global _auth_ready, _last_svr
    with _lock:
        _auth_ready = False
        _last_svr = None


def diagnose_kis_auth() -> dict:
    """Safe KIS auth diagnostics for /api/health (no secrets)."""
    settings = get_settings()
    svr = (settings.kis_svr or "prod").lower().strip()
    path = settings.kis_config_resolved

    if path is None:
        return {
            "status": "not_configured",
            "message": "kis_devlp.yaml not found",
        }

    ka = get_kis_auth_module()
    _reload_kis_config(ka, svr)
    keys = _key_status(ka._cfg, svr)

    if _read_token_safe(ka):
        return {
            "status": "token_cached",
            "message": "Valid token file exists for this svr",
            "svr": svr,
            "config_path": str(path),
            "token_file": ka.token_tmp,
            **keys,
        }

    token_result = request_token(svr)
    if token_result.get("ok"):
        return {
            "status": "token_ok",
            "message": "Token can be issued",
            "svr": svr,
            **token_result,
        }

    return {
        "status": "token_failed",
        "message": token_result.get("message", "unknown"),
        "reason": token_result.get("reason"),
        "status_code": token_result.get("status_code"),
        "error_code": token_result.get("error_code"),
        "svr": svr,
        "config_path": str(path),
        "token_file": token_result.get("token_file"),
        **keys,
    }
