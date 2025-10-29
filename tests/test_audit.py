"""
Tests for audit logging functionality.
"""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.audit import log_audit_event, get_audit_logs
from app.models.audit_log import AuditLog

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Create tables
Base.metadata.create_all(bind=engine)

# Create test client
client = TestClient(app)


def test_log_audit_event():
    """Test logging an audit event."""
    db = TestingSessionLocal()
    
    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="patient",
        status="success",
        user_id=1,
        username="test_user",
        resource_id=100,
        details={"field": "value"}
    )
    
    # Verify the log was created
    logs = db.query(AuditLog).all()
    assert len(logs) == 1
    assert logs[0].action == "CREATE"
    assert logs[0].resource_type == "patient"
    assert logs[0].username == "test_user"
    
    db.close()


def test_get_audit_logs():
    """Test retrieving audit logs with filtering."""
    # Create a fresh database for this test
    engine_test = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine_test)
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)
    db = TestSession()
    
    # Create multiple audit logs
    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="patient",
        status="success",
        user_id=1,
        username="user1"
    )
    
    log_audit_event(
        db=db,
        action="UPDATE",
        resource_type="patient",
        status="success",
        user_id=1,
        username="user1"
    )
    
    log_audit_event(
        db=db,
        action="CREATE",
        resource_type="appointment",
        status="success",
        user_id=2,
        username="user2"
    )
    
    # Test filtering by user_id
    user_logs = get_audit_logs(db, user_id=1)
    assert len(user_logs) == 2
    
    # Test filtering by resource_type
    patient_logs = get_audit_logs(db, resource_type="patient")
    assert len(patient_logs) == 2
    
    # Test filtering by action
    create_logs = get_audit_logs(db, action="CREATE")
    assert len(create_logs) == 2
    
    db.close()


def test_metrics_endpoint():
    """Test that metrics endpoint is accessible."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Check for prometheus metrics format
    assert "# HELP" in response.text or "# TYPE" in response.text
