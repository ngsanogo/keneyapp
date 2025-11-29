"""
Data encryption utilities for KeneyApp.
Provides encryption at rest for sensitive patient data using AES-256-GCM.

Uses the modern 'cryptography' library (FIPS 140-2 compliant, actively maintained).
Migrated from deprecated PyCrypto library for security and compliance.
"""

import base64
import os
from typing import Optional

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings


class DataEncryption:
    """Handle encryption and decryption of sensitive data using AES-256-GCM."""

    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption with a key.

        Args:
            key: Encryption key (defaults to SECRET_KEY from settings)
        """
        self.key = key or settings.ENCRYPTION_KEY or settings.SECRET_KEY

        if not self.key:
            raise ValueError("Encryption key is required to initialize DataEncryption.")

        if len(self.key) < 32:
            raise ValueError("Encryption key must be at least 32 characters long.")

        salt_material = settings.ENCRYPTION_SALT or "keneyapp-salt"
        salt_hasher = hashes.Hash(hashes.SHA256())
        salt_hasher.update(salt_material.encode("utf-8"))
        salt = salt_hasher.finalize()[:16]

        # Derive a 32-byte key using PBKDF2-HMAC-SHA256
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend(),
        )
        self.derived_key = kdf.derive(self.key.encode("utf-8"))

        # Create AESGCM instance for encryption/decryption
        self.aesgcm = AESGCM(self.derived_key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext data using AES-256-GCM.

        Args:
            plaintext: Data to encrypt

        Returns:
            Base64-encoded encrypted data with nonce

        Raises:
            ValueError: If encryption fails
        """
        if not plaintext:
            return plaintext

        try:
            # Generate random 96-bit nonce (12 bytes) for GCM
            nonce = os.urandom(12)

            # Encrypt using AESGCM (automatically handles tag)
            ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

            # Combine nonce + ciphertext (tag is embedded) and encode as base64
            encrypted_data = nonce + ciphertext
            return base64.b64encode(encrypted_data).decode("utf-8")

        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data.

        Args:
            encrypted_data: Base64-encoded encrypted data

        Returns:
            Decrypted plaintext

        Raises:
            ValueError: If decryption or authentication fails
        """
        if not encrypted_data:
            return encrypted_data

        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode("utf-8"))

            # Extract nonce (12 bytes) and ciphertext (includes embedded tag)
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            # Decrypt using AESGCM (automatically verifies tag)
            plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext.decode("utf-8")

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_field(self, data: Optional[str]) -> Optional[str]:
        """
        Encrypt a database field (handles None values).

        Args:
            data: Field value to encrypt

        Returns:
            Encrypted value or None
        """
        if data is None:
            return None
        return self.encrypt(str(data))

    def decrypt_field(self, data: Optional[str]) -> Optional[str]:
        """
        Decrypt a database field (handles None values).

        Args:
            data: Encrypted field value

        Returns:
            Decrypted value or None
        """
        if data is None:
            return None
        return self.decrypt(data)


# Global encryption instance (lazy-loaded)
_encryption: Optional[DataEncryption] = None


def get_encryption() -> DataEncryption:
    """Get or create the global encryption instance."""
    global _encryption
    if _encryption is None:
        _encryption = DataEncryption()
    return _encryption


# Helper functions for direct use
def encrypt_sensitive_data(plaintext: str) -> str:
    """Encrypt sensitive data."""
    return get_encryption().encrypt(plaintext)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return get_encryption().decrypt(encrypted_data)


# Backward-compatible wrappers used by services; optional context is ignored for now
def encrypt_data(plaintext: str, context: Optional[dict] = None) -> str:
    """Encrypt data with optional context (reserved for future key scoping)."""
    return encrypt_sensitive_data(plaintext)


def decrypt_data(encrypted_data: str, context: Optional[dict] = None) -> str:
    """Decrypt data with optional context (reserved for future key scoping)."""
    return decrypt_sensitive_data(encrypted_data)


def encrypt_patient_data(data: dict) -> dict:
    """
    Encrypt sensitive fields in patient data.

    Args:
        data: Patient data dictionary

    Returns:
        Dictionary with encrypted sensitive fields
    """
    encrypted = data.copy()

    # Fields that should be encrypted
    sensitive_fields = [
        "medical_history",
        "allergies",
        "emergency_contact",
        "emergency_phone",
        "address",
    ]

    for field in sensitive_fields:
        if field in encrypted and encrypted[field]:
            encrypted[field] = encryption.encrypt_field(encrypted[field])

    return encrypted


def decrypt_patient_data(data: dict) -> dict:
    """
    Decrypt sensitive fields in patient data.

    Args:
        data: Patient data dictionary with encrypted fields

    Returns:
        Dictionary with decrypted sensitive fields
    """
    decrypted = data.copy()

    # Fields that should be decrypted
    sensitive_fields = [
        "medical_history",
        "allergies",
        "emergency_contact",
        "emergency_phone",
        "address",
    ]

    for field in sensitive_fields:
        if field in decrypted and decrypted[field]:
            try:
                decrypted[field] = encryption.decrypt_field(decrypted[field])
            except ValueError:
                # Field might not be encrypted, leave as is
                pass

    return decrypted


__all__ = [
    "DataEncryption",
    "encryption",
    "encrypt_sensitive_data",
    "decrypt_sensitive_data",
    "encrypt_data",
    "decrypt_data",
    "encrypt_patient_data",
    "decrypt_patient_data",
]
