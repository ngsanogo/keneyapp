"""
Data encryption utilities for KeneyApp.
Provides encryption at rest for sensitive patient data using AES-256.
"""

from typing import Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64

from app.core.config import settings


class DataEncryption:
    """Handle encryption and decryption of sensitive data."""
    
    def __init__(self, key: Optional[str] = None):
        """
        Initialize encryption with a key.
        
        Args:
            key: Encryption key (defaults to SECRET_KEY from settings)
        """
        self.key = key or settings.SECRET_KEY
        # Derive a 32-byte key using PBKDF2
        self.derived_key = PBKDF2(
            self.key.encode('utf-8'),
            b'keneyapp-salt',  # Salt for key derivation
            dkLen=32,
            count=100000
        )
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt
            
        Returns:
            Base64-encoded encrypted data with nonce
        """
        if not plaintext:
            return plaintext
        
        try:
            # Generate random nonce
            nonce = get_random_bytes(12)
            
            # Create AES cipher in GCM mode
            cipher = AES.new(self.derived_key, AES.MODE_GCM, nonce=nonce)
            
            # Encrypt and get authentication tag
            ciphertext, tag = cipher.encrypt_and_digest(plaintext.encode('utf-8'))
            
            # Combine nonce + tag + ciphertext and encode as base64
            encrypted_data = nonce + tag + ciphertext
            return base64.b64encode(encrypted_data).decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt AES-256-GCM encrypted data.
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            
        Returns:
            Decrypted plaintext
        """
        if not encrypted_data:
            return encrypted_data
        
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extract nonce (12 bytes), tag (16 bytes), and ciphertext
            nonce = encrypted_bytes[:12]
            tag = encrypted_bytes[12:28]
            ciphertext = encrypted_bytes[28:]
            
            # Create AES cipher in GCM mode
            cipher = AES.new(self.derived_key, AES.MODE_GCM, nonce=nonce)
            
            # Decrypt and verify authentication tag
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode('utf-8')
            
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


# Global encryption instance
encryption = DataEncryption()


# Helper functions for direct use
def encrypt_sensitive_data(plaintext: str) -> str:
    """Encrypt sensitive data."""
    return encryption.encrypt(plaintext)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data."""
    return encryption.decrypt(encrypted_data)


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
        'medical_history',
        'allergies',
        'emergency_contact',
        'emergency_phone',
        'address',
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
        'medical_history',
        'allergies',
        'emergency_contact',
        'emergency_phone',
        'address',
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
    'DataEncryption',
    'encryption',
    'encrypt_sensitive_data',
    'decrypt_sensitive_data',
    'encrypt_patient_data',
    'decrypt_patient_data',
]
