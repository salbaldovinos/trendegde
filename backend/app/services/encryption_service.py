"""AES-256-GCM encryption for broker credentials with per-connection key derivation."""

from __future__ import annotations

import json
import os
import uuid

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("trendedge.encryption")

# Current master key version identifier
_CURRENT_KEY_ID = "v1"


def _get_master_key() -> bytes:
    """Return the master encryption key from config."""
    raw = settings.BROKER_ENCRYPTION_MASTER_KEY
    if not raw:
        raise RuntimeError("BROKER_ENCRYPTION_MASTER_KEY is not set.")
    return bytes.fromhex(raw)


def _derive_key(master_key: bytes, connection_id: uuid.UUID) -> bytes:
    """Derive a per-connection 256-bit DEK via HKDF-SHA256."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=str(connection_id).encode(),
    )
    return hkdf.derive(master_key)


def encrypt_credentials(
    connection_id: uuid.UUID, credentials: dict
) -> tuple[bytes, bytes, str]:
    """Encrypt a credentials dict and return (ciphertext, iv, key_id).

    The ciphertext includes the GCM authentication tag (appended by AESGCM).
    """
    master_key = _get_master_key()
    dek = _derive_key(master_key, connection_id)

    plaintext = json.dumps(credentials).encode("utf-8")
    iv = os.urandom(12)  # 96-bit IV

    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(iv, plaintext, None)

    return ciphertext, iv, _CURRENT_KEY_ID


def decrypt_credentials(
    connection_id: uuid.UUID,
    ciphertext: bytes,
    iv: bytes,
    key_id: str,
) -> dict:
    """Decrypt broker credentials. Raises on tampered data or wrong key."""
    master_key = _get_master_key()
    dek = _derive_key(master_key, connection_id)

    aesgcm = AESGCM(dek)
    plaintext = aesgcm.decrypt(iv, ciphertext, None)

    return json.loads(plaintext.decode("utf-8"))
