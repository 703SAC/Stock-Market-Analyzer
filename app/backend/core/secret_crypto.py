"""Small encryption layer for local secret files."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

ENCRYPTED_PREFIX = "enc:v1:"
DEFAULT_KEY_FILE = ".secret.key"


class SecretCryptoError(RuntimeError):
    """Raised when an encrypted setting cannot be decrypted."""


def is_encrypted(value: Any) -> bool:
    return isinstance(value, str) and value.startswith(ENCRYPTED_PREFIX)


def generate_key() -> str:
    return base64.urlsafe_b64encode(get_random_bytes(32)).decode("ascii")


def resolve_key(root: Path | None = None) -> bytes:
    raw = os.getenv("SECRET_ENCRYPTION_KEY", "").strip()
    if not raw:
        key_file = Path(
            os.getenv(
                "SECRET_ENCRYPTION_KEY_FILE",
                str((root or Path.cwd()) / DEFAULT_KEY_FILE),
            )
        ).expanduser()
        if key_file.exists():
            raw = key_file.read_text(encoding="utf-8").strip()

    if not raw:
        raise SecretCryptoError(
            "Encrypted secrets require SECRET_ENCRYPTION_KEY or .secret.key"
        )

    try:
        decoded = base64.urlsafe_b64decode(raw.encode("ascii"))
        if len(decoded) in {16, 24, 32}:
            return decoded
    except Exception:
        pass

    return hashlib.sha256(raw.encode("utf-8")).digest()


def encrypt_secret(plaintext: str, root: Path | None = None) -> str:
    if is_encrypted(plaintext):
        return plaintext
    key = resolve_key(root)
    nonce = get_random_bytes(12)
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode("utf-8"))
    payload = base64.urlsafe_b64encode(nonce + tag + ciphertext).decode("ascii")
    return f"{ENCRYPTED_PREFIX}{payload}"


def decrypt_secret(value: str, root: Path | None = None) -> str:
    if not is_encrypted(value):
        return value
    key = resolve_key(root)
    try:
        payload = base64.urlsafe_b64decode(value[len(ENCRYPTED_PREFIX) :].encode("ascii"))
        nonce, tag, ciphertext = payload[:12], payload[12:28], payload[28:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
    except Exception as exc:
        raise SecretCryptoError("Failed to decrypt secret value") from exc


def decrypt_config_values(value: Any, root: Path | None = None) -> Any:
    if is_encrypted(value):
        return decrypt_secret(value, root)
    if isinstance(value, dict):
        return {k: decrypt_config_values(v, root) for k, v in value.items()}
    if isinstance(value, list):
        return [decrypt_config_values(v, root) for v in value]
    return value

