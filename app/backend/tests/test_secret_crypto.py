from __future__ import annotations

import base64

from Crypto.Random import get_random_bytes

from config import Settings
from core.secret_crypto import (
    decrypt_config_values,
    decrypt_secret,
    encrypt_secret,
    is_encrypted,
)


def _test_key() -> str:
    return base64.urlsafe_b64encode(get_random_bytes(32)).decode("ascii")


def test_secret_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", _test_key())

    encrypted = encrypt_secret("very-secret-token")

    assert is_encrypted(encrypted)
    assert encrypted != "very-secret-token"
    assert decrypt_secret(encrypted) == "very-secret-token"


def test_decrypt_config_values_nested(monkeypatch):
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", _test_key())
    encrypted = encrypt_secret("kis-secret")

    data = {
        "my_app": encrypted,
        "nested": ["plain", encrypted],
    }

    assert decrypt_config_values(data) == {
        "my_app": "kis-secret",
        "nested": ["plain", "kis-secret"],
    }


def test_settings_decrypts_encrypted_env_values(monkeypatch):
    monkeypatch.setenv("SECRET_ENCRYPTION_KEY", _test_key())
    encrypted = encrypt_secret("naver-secret")

    # _env_file=None: 실제 .env(다른 키로 암호화됨)와 격리 — 이 테스트 키로만 복호화
    settings = Settings(_env_file=None, naver_client_secret=encrypted)

    assert settings.naver_client_secret == "naver-secret"

