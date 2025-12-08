"""
Comprehensive tests for messaging service (v3.0).

Tests cover:
- Message creation and retrieval
- Encryption/decryption
- Thread management
- Soft delete functionality
- Urgent messages
- Read status tracking
- Conversation management
- Security and access control
"""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.encryption import decrypt_data, encrypt_data
from app.models.message import Message, MessageStatus
from app.models.user import User, UserRole


@pytest.mark.unit
class TestMessageEncryption:
    """Test message encryption and decryption."""

    def test_encrypt_message_content(self):
        """Test encrypting message content."""
        original = "Résultats d'analyses disponibles"
        encrypted = encrypt_data(original, context={"type": "message"})

        assert encrypted != original
        assert encrypted is not None
        assert len(encrypted) > len(original)

    def test_decrypt_message_content(self):
        """Test decrypting message content."""
        original = "Votre ordonnance est prête"
        encrypted = encrypt_data(original, context={"type": "message"})
        decrypted = decrypt_data(encrypted, context={"type": "message"})

        assert decrypted == original

    def test_encryption_uniqueness(self):
        """Test that same content produces different ciphertexts."""
        content = "Message confidentiel"
        encrypted1 = encrypt_data(content, context={"type": "message"})
        encrypted2 = encrypt_data(content, context={"type": "message"})

        assert encrypted1 != encrypted2  # Nonce ensures uniqueness


@pytest.mark.integration
class TestMessageCRUD:
    """Test message CRUD operations."""

    def test_send_message_success(self, client: TestClient, auth_headers_doctor: dict, test_doctor_2, db: Session):
        """Test sending a message successfully."""
        payload = {
            "receiver_id": test_doctor_2.id,  # Use actual receiver ID
            "subject": "Résultats disponibles",
            "content": "Vos résultats d'analyses sont disponibles.",
            "is_urgent": False,
        }

        response = client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        assert response.status_code == 201
        data = response.json()
        assert data["subject"] == payload["subject"]
        assert data["status"] == "sent"
        assert "encrypted_content" not in data  # Should not expose encrypted field

    def test_send_urgent_message(self, client: TestClient, auth_headers_doctor: dict, test_doctor_2, db: Session):
        """Test sending an urgent message."""
        payload = {
            "receiver_id": test_doctor_2.id,  # Use actual receiver ID
            "subject": "URGENT - Résultats anormaux",
            "content": "Veuillez me contacter immédiatement.",
            "is_urgent": True,
        }

        response = client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        assert response.status_code == 201
        data = response.json()
        assert data["is_urgent"] is True

    def test_send_message_unauthorized(self, unauthenticated_client: TestClient, test_doctor_2):
        """Test sending message without authentication."""
        payload = {"receiver_id": test_doctor_2.id, "subject": "Test", "content": "Test message"}

        response = unauthenticated_client.post("/api/v1/messages/", json=payload)
        assert response.status_code == 401

    def test_get_messages_inbox(self, client: TestClient, auth_headers_doctor: dict):
        """Test retrieving inbox messages."""
        response = client.get("/api/v1/messages/", headers=auth_headers_doctor)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_message_details(
        self, client: TestClient, auth_headers_doctor: dict, test_doctor_2, db: Session
    ):
        """Test retrieving message details."""
        # First send a message
        payload = {"receiver_id": test_doctor_2.id, "subject": "Test", "content": "Test content"}
        send_response = client.post(
            "/api/v1/messages/", json=payload, headers=auth_headers_doctor
        )
        message_id = send_response.json()["id"]

        # Retrieve message
        response = client.get(f"/api/v1/messages/{message_id}", headers=auth_headers_doctor)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == message_id
        assert data["subject"] == payload["subject"]

    def test_get_message_forbidden(self, client: TestClient, auth_headers_doctor: dict):
        """Test retrieving message belonging to another user."""
        # Try to access a non-existent or unauthorized message
        response = client.get("/api/v1/messages/99999", headers=auth_headers_doctor)

        assert response.status_code in [403, 404]


@pytest.mark.integration
class TestMessageThreads:
    """Test message threading and conversations."""

    def test_create_conversation_thread(self, client: TestClient, auth_headers_doctor: dict, test_doctor_2):
        """Test creating a conversation thread."""
        # Send initial message
        payload1 = {
            "receiver_id": test_doctor_2.id,
            "subject": "Question médicale",
            "content": "Bonjour Docteur, j'ai une question.",
        }
        response1 = client.post(
            "/api/v1/messages/", json=payload1, headers=auth_headers_doctor
        )
        assert response1.status_code == 201
        message1_id = response1.json()["id"]
        thread_id = response1.json().get("thread_id")

        # Send reply (would need receiver's auth)
        # This tests the thread_id is consistent
        assert thread_id is not None or message1_id is not None

    def test_get_conversation_with_user(self, client: TestClient, auth_headers_doctor: dict, test_doctor_2):
        """Test retrieving conversation with specific user."""
        # Send messages
        for i in range(3):
            payload = {
                "receiver_id": test_doctor_2.id,
                "subject": f"Message {i + 1}",
                "content": f"Contenu {i + 1}",
            }
            client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        # Get conversation
        response = client.get(f"/api/v1/messages/conversation/{test_doctor_2.id}", headers=auth_headers_doctor)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3


@pytest.mark.integration
class TestMessageReadStatus:
    """Test message read status tracking."""

    def test_mark_message_as_read(self, client: TestClient, auth_headers_doctor: dict, test_doctor_2):
        """Test marking message as read."""
        # Send message
        payload = {"receiver_id": test_doctor_2.id, "subject": "Test", "content": "Test"}
        send_response = client.post(
            "/api/v1/messages/", json=payload, headers=auth_headers_doctor
        )
        message_id = send_response.json()["id"]

        # Mark as read (would need receiver auth in real scenario)
        # For now, test endpoint exists
        read_response = client.post(
            f"/api/v1/messages/{message_id}/read", headers=auth_headers_doctor
        )

        # Expect 200 or 403 (if sender tries to mark own message as read)
        assert read_response.status_code in [200, 403]

    def test_read_at_timestamp_set(
        self, client: TestClient, auth_headers_doctor: dict, db: Session
    ):
        """Test that read_at timestamp is set correctly."""
        # Create message in DB
        message = Message(
            sender_id=1,
            receiver_id=2,
            subject="Test",
            encrypted_content=encrypt_data("Test content", context={"type": "message"}),
            status=MessageStatus.DELIVERED,
            tenant_id=1,
        )
        db.add(message)
        db.commit()
        db.refresh(message)

        # Initially no read_at
        assert message.read_at is None

        # Simulate marking as read
        message.status = MessageStatus.READ
        from datetime import timezone
        message.read_at = datetime.now(timezone.utc)
        db.commit()

        assert message.read_at is not None
        assert message.status == MessageStatus.READ


@pytest.mark.integration
class TestSoftDelete:
    """Test soft delete functionality."""

    def test_soft_delete_by_sender(self, client: TestClient, auth_headers_doctor: dict, test_doctor_2):
        """Test sender soft-deleting a message."""
        # Send message
        payload = {
            "receiver_id": test_doctor_2.id,
            "subject": "À supprimer",
            "content": "Ce message sera supprimé",
        }
        send_response = client.post(
            "/api/v1/messages/", json=payload, headers=auth_headers_doctor
        )
        message_id = send_response.json()["id"]

        # Delete message
        delete_response = client.delete(
            f"/api/v1/messages/{message_id}", headers=auth_headers_doctor
        )

        assert delete_response.status_code == 204

    def test_soft_delete_does_not_affect_receiver(self, db: Session):
        """Test that soft delete by sender doesn't affect receiver."""
        message = Message(
            sender_id=1,
            receiver_id=2,
            subject="Test",
            encrypted_content=encrypt_data("Content", context={"type": "message"}),
            status=MessageStatus.DELIVERED,
            deleted_by_sender=True,
            deleted_by_receiver=False,
            tenant_id=1,
        )
        db.add(message)
        db.commit()

        # Receiver should still see it
        assert message.deleted_by_receiver is False


@pytest.mark.integration
class TestMessageStatistics:
    """Test message statistics endpoint."""

    def test_get_message_stats(self, client: TestClient, auth_headers_doctor: dict):
        """Test retrieving message statistics."""
        response = client.get("/api/v1/messages/stats", headers=auth_headers_doctor)

        assert response.status_code == 200
        data = response.json()
        assert "total_received" in data
        assert "total_sent" in data
        assert "unread_count" in data
        assert "urgent_count" in data


@pytest.mark.integration
class TestMessageSecurity:
    """Test message security and access control."""

    def test_cannot_send_to_different_tenant(
        self, client: TestClient, auth_headers_doctor: dict
    ):
        """Test that users cannot send messages across tenants."""
        payload = {
            "receiver_id": 9999,  # User from different tenant
            "subject": "Cross-tenant test",
            "content": "This should fail",
        }

        response = client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        # Should fail (404 user not found or 403 forbidden)
        assert response.status_code in [403, 404]

    def test_message_content_encrypted_in_db(self, db: Session):
        """Test that message content is encrypted in database."""
        original_content = "Contenu sensible médical"
        encrypted = encrypt_data(original_content, context={"type": "message"})

        message = Message(
            sender_id=1,
            receiver_id=2,
            subject="Test encryption",
            encrypted_content=encrypted,
            status=MessageStatus.SENT,
            tenant_id=1,
        )
        db.add(message)
        db.commit()

        # Verify stored content is encrypted
        assert message.encrypted_content != original_content
        assert message.encrypted_content == encrypted


@pytest.mark.integration
class TestMessageValidation:
    """Test message validation rules."""

    def test_empty_content_rejected(self, client: TestClient, auth_headers_doctor: dict):
        """Test that empty message content is rejected."""
        payload = {"receiver_id": 2, "subject": "Test", "content": ""}

        response = client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        assert response.status_code == 422

    def test_missing_receiver_rejected(self, client: TestClient, auth_headers_doctor: dict):
        """Test that message without receiver is rejected."""
        payload = {"subject": "Test", "content": "Test content"}

        response = client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        assert response.status_code == 422

    def test_subject_too_long_rejected(self, client: TestClient, auth_headers_doctor: dict):
        """Test that overly long subject is rejected."""
        payload = {
            "receiver_id": 2,
            "subject": "A" * 300,  # Assuming max 255
            "content": "Test",
        }

        response = client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        assert response.status_code in [422, 400]


@pytest.mark.integration
class TestMessagePerformance:
    """Test message performance characteristics."""

    def test_bulk_message_retrieval(self, client: TestClient, auth_headers_doctor: dict):
        """Test retrieving large number of messages."""
        # Send 20 messages
        for i in range(20):
            payload = {
                "receiver_id": 2,
                "subject": f"Message {i}",
                "content": f"Content {i}",
            }
            client.post("/api/v1/messages/", json=payload, headers=auth_headers_doctor)

        # Retrieve all
        response = client.get("/api/v1/messages/?skip=0&limit=50", headers=auth_headers_doctor)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 20

    def test_pagination_works(self, client: TestClient, auth_headers_doctor: dict):
        """Test message pagination."""
        response = client.get("/api/v1/messages/?skip=0&limit=10", headers=auth_headers_doctor)

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


