"""
Tests for business metrics collector service.
"""

from datetime import datetime

from app.services.metrics_collector import (
    collect_all_business_metrics,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def test_collect_all_business_metrics_with_empty_database():
    """Test collecting all business metrics with empty database."""
    db = TestingSessionLocal()
    try:
        metrics = collect_all_business_metrics(db)

        # Check top-level structure
        assert "timestamp" in metrics
        assert "daily_active_patients" in metrics
        assert "appointment_metrics" in metrics
        assert "prescription_metrics" in metrics
        assert "patient_risk_metrics" in metrics

        # Verify timestamp format
        timestamp = datetime.fromisoformat(metrics["timestamp"])
        assert isinstance(timestamp, datetime)

        # Verify nested structures
        assert isinstance(metrics["appointment_metrics"], dict)
        assert isinstance(metrics["prescription_metrics"], dict)
        assert isinstance(metrics["patient_risk_metrics"], dict)

        # Should return valid structure even with no data
        assert metrics["daily_active_patients"] >= 0

        # Rates should be 0 with no data
        appointment_metrics = metrics["appointment_metrics"]
        assert appointment_metrics["daily_completion_rate"] == 0
        assert appointment_metrics["daily_no_show_rate"] == 0

        # Check returned metrics structure
        assert "daily_completion_rate" in appointment_metrics
        assert "weekly_completion_rate" in appointment_metrics
        assert "monthly_completion_rate" in appointment_metrics
        assert "daily_no_show_rate" in appointment_metrics

        # Check prescription metrics structure
        prescription_metrics = metrics["prescription_metrics"]
        assert "daily_fulfillment_rate" in prescription_metrics
        assert "weekly_fulfillment_rate" in prescription_metrics

        # Check patient risk metrics
        patient_risk_metrics = metrics["patient_risk_metrics"]
        assert "low" in patient_risk_metrics
        assert "medium" in patient_risk_metrics
        assert "high" in patient_risk_metrics

        # All values should be non-negative
        assert patient_risk_metrics["low"] >= 0
        assert patient_risk_metrics["medium"] >= 0
        assert patient_risk_metrics["high"] >= 0

    finally:
        db.close()


def test_collect_metrics_structure():
    """Test that metrics collection returns expected structure."""
    db = TestingSessionLocal()
    try:
        metrics = collect_all_business_metrics(db)

        # Verify all required keys exist
        required_keys = [
            "timestamp",
            "daily_active_patients",
            "appointment_metrics",
            "prescription_metrics",
            "patient_risk_metrics",
        ]

        for key in required_keys:
            assert key in metrics, f"Missing required key: {key}"

        # Verify data types
        assert isinstance(metrics["timestamp"], str)
        assert isinstance(metrics["daily_active_patients"], int)
        assert isinstance(metrics["appointment_metrics"], dict)
        assert isinstance(metrics["prescription_metrics"], dict)
        assert isinstance(metrics["patient_risk_metrics"], dict)

    finally:
        db.close()
