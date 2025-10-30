"""Tests for data encryption module."""

import pytest
from app.core.encryption import (
    encryption,
    encrypt_sensitive_data,
    decrypt_sensitive_data,
    encrypt_patient_data,
    decrypt_patient_data,
)


def test_encrypt_decrypt_basic():
    """Test basic encryption and decryption."""
    plaintext = "Sensitive medical data"
    
    # Encrypt
    encrypted = encrypt_sensitive_data(plaintext)
    assert encrypted != plaintext
    assert len(encrypted) > len(plaintext)
    
    # Decrypt
    decrypted = decrypt_sensitive_data(encrypted)
    assert decrypted == plaintext


def test_encrypt_decrypt_empty_string():
    """Test encryption with empty string."""
    encrypted = encryption.encrypt("")
    assert encrypted == ""
    
    decrypted = encryption.decrypt("")
    assert decrypted == ""


def test_encrypt_decrypt_unicode():
    """Test encryption with unicode characters."""
    plaintext = "Patient allergies: 🥜 nuts, 🥚 eggs"
    
    encrypted = encrypt_sensitive_data(plaintext)
    decrypted = decrypt_sensitive_data(encrypted)
    
    assert decrypted == plaintext


def test_encrypt_patient_data():
    """Test encrypting sensitive patient fields."""
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "medical_history": "Diabetes Type 2",
        "allergies": "Penicillin",
        "emergency_contact": "Jane Doe",
        "emergency_phone": "+15551234567",
        "address": "123 Main St",
        "email": "john@example.com",  # Not encrypted
    }
    
    encrypted = encrypt_patient_data(patient_data)
    
    # Check that sensitive fields are encrypted
    assert encrypted["medical_history"] != patient_data["medical_history"]
    assert encrypted["allergies"] != patient_data["allergies"]
    assert encrypted["emergency_contact"] != patient_data["emergency_contact"]
    assert encrypted["emergency_phone"] != patient_data["emergency_phone"]
    assert encrypted["address"] != patient_data["address"]
    
    # Check that non-sensitive fields are not encrypted
    assert encrypted["first_name"] == patient_data["first_name"]
    assert encrypted["last_name"] == patient_data["last_name"]
    assert encrypted["email"] == patient_data["email"]


def test_decrypt_patient_data():
    """Test decrypting sensitive patient fields."""
    original_data = {
        "first_name": "John",
        "last_name": "Doe",
        "medical_history": "Diabetes Type 2",
        "allergies": "Penicillin",
        "emergency_contact": "Jane Doe",
        "emergency_phone": "+15551234567",
        "address": "123 Main St",
    }
    
    # Encrypt
    encrypted = encrypt_patient_data(original_data)
    
    # Decrypt
    decrypted = decrypt_patient_data(encrypted)
    
    # Verify all sensitive fields are correctly decrypted
    assert decrypted["medical_history"] == original_data["medical_history"]
    assert decrypted["allergies"] == original_data["allergies"]
    assert decrypted["emergency_contact"] == original_data["emergency_contact"]
    assert decrypted["emergency_phone"] == original_data["emergency_phone"]
    assert decrypted["address"] == original_data["address"]


def test_encrypt_field_none():
    """Test encrypting None values."""
    result = encryption.encrypt_field(None)
    assert result is None


def test_decrypt_field_none():
    """Test decrypting None values."""
    result = encryption.decrypt_field(None)
    assert result is None


def test_encryption_unique_ciphertext():
    """Test that same plaintext produces different ciphertext (due to nonce)."""
    plaintext = "Test data"
    
    encrypted1 = encrypt_sensitive_data(plaintext)
    encrypted2 = encrypt_sensitive_data(plaintext)
    
    # Different ciphertexts (different nonces)
    assert encrypted1 != encrypted2
    
    # But same plaintext when decrypted
    assert decrypt_sensitive_data(encrypted1) == plaintext
    assert decrypt_sensitive_data(encrypted2) == plaintext


def test_invalid_ciphertext_raises_error():
    """Test that invalid ciphertext raises ValueError."""
    with pytest.raises(ValueError):
        decrypt_sensitive_data("invalid_ciphertext")
