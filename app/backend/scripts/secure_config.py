"""Encrypt local .env and KIS config values.

Usage from app/backend:
  python scripts/secure_config.py generate-key
  python scripts/secure_config.py encrypt-env --env-file ../../.env
  python scripts/secure_config.py encrypt-kis
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = BACKEND_ROOT.parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from core.secret_crypto import (  # noqa: E402
    DEFAULT_KEY_FILE,
    decrypt_secret,
    encrypt_secret,
    generate_key,
    is_encrypted,
)

ENV_SECRET_KEYS = {
    "NAVER_CLIENT_ID",
    "NAVER_CLIENT_SECRET",
    "OPENDART_API_KEY",
    "OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "ANTHROPIC_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
}

KIS_SECRET_KEYS = {
    "my_app",
    "my_sec",
    "paper_app",
    "paper_sec",
    "my_acct_stock",
    "my_paper_stock",
    "my_htsid",
}

ENV_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _strip_env_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _atomic_write(path: Path, text: str) -> None:
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def generate_key_file(path: Path) -> None:
    if path.exists():
        raise SystemExit(f"Key file already exists: {path}")
    path.write_text(f"{generate_key()}\n", encoding="utf-8")
    path.chmod(0o600)
    print(f"created {path}")


def encrypt_env_file(path: Path, keys: Iterable[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    target_keys = set(keys)
    changed = 0
    out: list[str] = []

    for line in lines:
        newline = "\n" if line.endswith("\n") else ""
        body = line[:-1] if newline else line
        match = ENV_LINE_RE.match(body)
        if not match:
            out.append(line)
            continue

        key, raw_value = match.groups()
        value = _strip_env_quotes(raw_value)
        if key not in target_keys or not value or is_encrypted(value):
            out.append(line)
            continue

        out.append(f"{key}={encrypt_secret(value, WORKSPACE_ROOT)}{newline}")
        changed += 1

    _atomic_write(path, "".join(out))
    print(f"encrypted {changed} env value(s) in {path}")


def encrypt_kis_file(path: Path, keys: Iterable[str]) -> None:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    target_keys = set(keys)
    changed = 0

    for key in target_keys:
        value = data.get(key)
        if isinstance(value, str) and value and not is_encrypted(value):
            data[key] = encrypt_secret(value, WORKSPACE_ROOT)
            changed += 1

    _atomic_write(path, yaml.safe_dump(data, allow_unicode=True, sort_keys=False))
    print(f"encrypted {changed} KIS value(s) in {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Encrypt/decrypt local secret config values.")
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-key", help="create a local encryption key file")
    gen.add_argument("--key-file", default=str(WORKSPACE_ROOT / DEFAULT_KEY_FILE))

    enc_value = sub.add_parser("encrypt-value", help="print one encrypted value")
    enc_value.add_argument("value")

    dec_value = sub.add_parser("decrypt-value", help="print one decrypted value")
    dec_value.add_argument("value")

    enc_env = sub.add_parser("encrypt-env", help="encrypt sensitive values in .env")
    enc_env.add_argument("--env-file", default=str(WORKSPACE_ROOT / ".env"))

    enc_kis = sub.add_parser("encrypt-kis", help="encrypt sensitive values in KIS YAML")
    enc_kis.add_argument(
        "--kis-config",
        default=str(Path.home() / "KIS" / "config" / "kis_devlp.yaml"),
    )

    args = parser.parse_args()
    if args.command == "generate-key":
        generate_key_file(Path(args.key_file).expanduser())
    elif args.command == "encrypt-value":
        print(encrypt_secret(args.value, WORKSPACE_ROOT))
    elif args.command == "decrypt-value":
        print(decrypt_secret(args.value, WORKSPACE_ROOT))
    elif args.command == "encrypt-env":
        encrypt_env_file(Path(args.env_file).expanduser(), ENV_SECRET_KEYS)
    elif args.command == "encrypt-kis":
        encrypt_kis_file(Path(args.kis_config).expanduser(), KIS_SECRET_KEYS)


if __name__ == "__main__":
    main()
