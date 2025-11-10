from unittest.mock import patch, MagicMock


def test_generate_patient_report_runs():
    from app.tasks import generate_patient_report

    with patch("app.core.database.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_patient_instance = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = (
            mock_patient_instance
        )
        result = generate_patient_report(42)
        assert result["status"] == "generated"
        assert result["patient_id"] == 42
        assert "report" in result


def test_send_appointment_reminder_runs():
    from app.tasks import send_appointment_reminder

    result = send_appointment_reminder(123, "foo@example.com")
    assert result["status"] == "sent"
    assert result["appointment_id"] == 123


def test_task_functions_exist():
    from app import tasks

    assert hasattr(tasks, "generate_patient_report")
    assert hasattr(tasks, "send_appointment_reminder")


def test_generate_patient_report_handles_missing_patient():
    from app.tasks import generate_patient_report

    with patch("app.core.database.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        result = generate_patient_report(999)
        assert result["status"] == "error"
        assert result["message"] == "Patient not found"


def test_generate_patient_report_handles_exception():
    from app.tasks import generate_patient_report

    with patch("app.core.database.SessionLocal") as mock_session_local:
        mock_db = MagicMock()
        mock_session_local.return_value = mock_db
        mock_db.query.side_effect = Exception("boom")
        result = generate_patient_report(1)
        assert result["status"] == "error"
        assert result["message"] == "Report generation failed"
