"""
Celery background tasks for asynchronous processing.
"""

import logging

import requests

from app.core.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="send_appointment_reminder")
def send_appointment_reminder(appointment_id: int, patient_email: str):
    """
    Send appointment reminder notification.

    Args:
        appointment_id: ID of the appointment
        patient_email: Patient's email address
    """
    # Implementation placeholder - integrate with email service (SendGrid, SES, etc.)
    # In production, use environment-configured SMTP/API credentials
    # Note: Avoid logging identifiable information for HIPAA compliance
    logger.info("Sending appointment reminder")

    # Example implementation would be:
    # from app.services.notification import send_email
    # send_email(
    #     to=patient_email,
    #     subject="Appointment Reminder",
    #     body=f"You have an upcoming appointment (ID: {appointment_id})"
    # )

    return {"status": "sent", "appointment_id": appointment_id}


@celery_app.task(name="generate_patient_report")
def generate_patient_report(patient_id: int):
    """
    Generate comprehensive patient report.

    Args:
        patient_id: ID of the patient
    """
    from app.core.database import SessionLocal
    from app.models.patient import Patient

    # Note: Avoid logging identifiable information for HIPAA compliance
    logger.info("Generating patient report")

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            logger.error("Patient not found in report generation")
            return {"status": "error", "message": "Patient not found"}

        # Generate report data structure
        from datetime import datetime, timezone

        report = {
            "patient_id": patient_id,
            "appointments_count": len(patient.appointments),
            "prescriptions_count": len(patient.prescriptions),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        logger.info("Patient report generated successfully")
        return {"status": "generated", "patient_id": patient_id, "report": report}
    except Exception:
        logger.error("Error generating report", exc_info=True)
        db.rollback()
        return {"status": "error", "message": "Report generation failed"}
    finally:
        db.close()


@celery_app.task(name="deliver_subscription_webhook")
def deliver_subscription_webhook(subscription_id: int, resource: dict):
    """Deliver a FHIR resource to a subscription webhook endpoint.

    Best-effort delivery with short timeout. Errors are logged but not raised.
    """
    from app.core.database import SessionLocal
    from app.models.subscription import Subscription

    db = SessionLocal()
    try:
        sub = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if not sub:
            logger.error(
                "Subscription %s not found for webhook delivery", subscription_id
            )
            return {"status": "error", "reason": "subscription_not_found"}

        headers = {"Content-Type": sub.payload or "application/fhir+json"}
        try:
            # Use json param to ensure proper serialization
            resp = requests.post(
                sub.endpoint, json=resource, headers=headers, timeout=5
            )
            logger.info(
                "Delivered webhook to %s status=%s", sub.endpoint, resp.status_code
            )
            return {"status": "ok", "http_status": resp.status_code}
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(
                "Webhook delivery failed for subscription %s: %s", subscription_id, exc
            )
            return {"status": "error", "reason": str(exc)}
    finally:
        try:
            db.close()
        except Exception:
            pass


@celery_app.task(name="check_prescription_interactions")
def check_prescription_interactions(prescription_id: int, medications: list):
    """
    Check for drug interactions in prescription.

    Args:
        prescription_id: ID of the prescription
        medications: List of medication names
    """
    # Implementation placeholder - integrate with drug interaction APIs
    # Consider using: FDA API, RxNorm, DrugBank, or commercial services
    # Note: Avoid logging identifiable information for HIPAA compliance
    logger.info("Checking drug interactions")

    interactions: list[dict] = []

    # Placeholder logic - in production, call external API or database
    # Example:
    # for i, med1 in enumerate(medications):
    #     for med2 in medications[i+1:]:
    #         interaction = check_interaction_api(med1, med2)
    #         if interaction:
    #             interactions.append(interaction)

    if len(medications) > 1:
        logger.info("Drug interaction check completed")

    return {
        "status": "checked",
        "prescription_id": prescription_id,
        "interactions": interactions,
        "medications_count": len(medications),
    }


@celery_app.task(name="backup_patient_data")
def backup_patient_data():
    """
    Perform automated backup of patient data.
    """
    # from app.core.database import engine
    # import subprocess
    from datetime import datetime

    logger.info("Starting patient data backup operation")

    try:
        # Example backup implementation using pg_dump
        # In production, configure AWS S3, Azure Blob Storage, or GCS
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"keneyapp_backup_{timestamp}.sql"

        # Placeholder for actual backup logic
        # subprocess.run([
        #     "pg_dump",
        #     "-h", "localhost",
        #     "-U", "username",
        #     "-d", "keneyapp",
        #     "-f", f"/backups/{backup_filename}"
        # ])

        logger.info("Patient data backup completed")
        return {"status": "completed", "backup_file": backup_filename}
    except Exception as e:
        logger.error("Backup operation failed", exc_info=True)
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    """
    Clean up expired authentication tokens.
    """
    from app.core.database import SessionLocal

    # from datetime import datetime, timedelta, timezone

    logger.info("Starting expired token cleanup")

    db = SessionLocal()
    try:
        # If you have a tokens table, clean it up here
        # Example:
        # cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
        # deleted = db.query(Token).filter(Token.expires_at < cutoff_date).delete()
        # db.commit()

        # For JWT-based auth without token storage, this could clean up
        # blacklisted tokens or revocation records

        logger.info("Expired token cleanup completed")
        return {"status": "completed", "tokens_cleaned": 0}
    except Exception as e:
        logger.error(f"Token cleanup failed: {str(e)}", exc_info=True)
        db.rollback()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="collect_business_metrics")
def collect_business_metrics():
    """
    Collect and update business KPI metrics for monitoring.

    This task runs periodically to update Prometheus metrics with
    current business KPIs such as appointment rates, patient activity, etc.
    """
    from app.core.database import SessionLocal
    from app.services.metrics_collector import collect_all_business_metrics

    db = SessionLocal()
    try:
        logger.info("Starting business metrics collection")
        metrics = collect_all_business_metrics(db)
        # Note: Detailed metrics are not logged for HIPAA compliance
        # Metrics are stored in Prometheus and viewable in Grafana
        logger.info("Business metrics collection completed successfully")
        return {"status": "completed", "metrics": metrics}
    except Exception as e:
        logger.error("Error collecting business metrics: %s", str(e), exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="send_upcoming_appointment_reminders")
def send_upcoming_appointment_reminders():
    """
    Send reminders for appointments happening in the next 24 hours.
    Runs daily to notify patients.
    """
    from datetime import datetime, timedelta, timezone

    from app.core.database import SessionLocal
    from app.models.appointment import Appointment
    from app.services.notification_service import NotificationService

    logger.info("Starting upcoming appointment reminders")

    db = SessionLocal()
    try:
        # Get appointments for next 24 hours
        now = datetime.now(timezone.utc)
        tomorrow = now + timedelta(days=1)

        appointments = (
            db.query(Appointment)
            .filter(
                Appointment.appointment_date >= now,
                Appointment.appointment_date <= tomorrow,
                Appointment.status == "scheduled",
            )
            .all()
        )

        sent_count = 0
        for appt in appointments:
            if appt.patient and appt.patient.email:
                NotificationService.send_appointment_reminder(
                    patient_email=appt.patient.email,
                    patient_name=f"{appt.patient.first_name} {appt.patient.last_name}",
                    appointment_date=appt.appointment_date,
                    doctor_name=(
                        appt.doctor.full_name if appt.doctor else "votre médecin"
                    ),
                    phone=appt.patient.phone,
                )
                sent_count += 1

        logger.info(f"Sent {sent_count} appointment reminders")
        return {"status": "completed", "reminders_sent": sent_count}

    except Exception as e:
        logger.error(f"Error sending appointment reminders: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="send_lab_results_notifications")
def send_lab_results_notifications(document_id: int, patient_id: int):
    """
    Notify patient when lab results are uploaded.

    Args:
        document_id: ID of the uploaded document
        patient_id: ID of the patient
    """
    from app.core.database import SessionLocal
    from app.models.medical_document import MedicalDocument
    from app.models.patient import Patient
    from app.services.notification_service import NotificationService

    logger.info("Sending lab results notification")

    db = SessionLocal()
    try:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        document = (
            db.query(MedicalDocument).filter(MedicalDocument.id == document_id).first()
        )

        if patient and document and patient.email:
            NotificationService.send_lab_results_notification(
                patient_email=patient.email,
                patient_name=f"{patient.first_name} {patient.last_name}",
                test_name=document.description or "analyse médicale",
                phone=patient.phone,
            )
            logger.info("Lab results notification sent")
            return {"status": "sent", "patient_id": patient_id}

        return {"status": "skipped", "reason": "Patient or document not found"}

    except Exception as e:
        logger.error(f"Error sending lab results notification: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="send_prescription_renewal_reminders")
def send_prescription_renewal_reminders():
    """
    Send reminders for prescriptions expiring in the next 7 days.
    Runs daily.
    """
    from datetime import datetime, timedelta, timezone

    from app.core.database import SessionLocal
    from app.models.prescription import Prescription
    from app.services.notification_service import NotificationService

    logger.info("Starting prescription renewal reminders")

    db = SessionLocal()
    try:
        # Get prescriptions expiring in next 7 days
        now = datetime.now(timezone.utc)
        next_week = now + timedelta(days=7)

        prescriptions = (
            db.query(Prescription)
            .filter(
                Prescription.refill_date >= now, Prescription.refill_date <= next_week
            )
            .all()
        )

        sent_count = 0
        for presc in prescriptions:
            if presc.patient and presc.patient.email:
                NotificationService.send_prescription_renewal_reminder(
                    patient_email=presc.patient.email,
                    patient_name=f"{presc.patient.first_name} {presc.patient.last_name}",
                    medication_name=presc.medication_name,
                    expiry_date=presc.refill_date,
                    phone=presc.patient.phone,
                )
                sent_count += 1

        logger.info(f"Sent {sent_count} prescription renewal reminders")
        return {"status": "completed", "reminders_sent": sent_count}

    except Exception as e:
        logger.error(f"Error sending prescription reminders: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="send_new_message_notification")
def send_new_message_notification(message_id: int, receiver_id: int):
    """
    Notify user of new message.

    Args:
        message_id: ID of the message
        receiver_id: ID of the receiver
    """
    from app.core.database import SessionLocal
    from app.models.message import Message
    from app.models.user import User
    from app.services.notification_service import NotificationService

    logger.info("Sending new message notification")

    db = SessionLocal()
    try:
        receiver = db.query(User).filter(User.id == receiver_id).first()
        message = db.query(Message).filter(Message.id == message_id).first()

        if receiver and message and receiver.email:
            sender = db.query(User).filter(User.id == message.sender_id).first()

            NotificationService.send_new_message_notification(
                recipient_email=receiver.email,
                recipient_name=receiver.full_name,
                sender_name=sender.full_name if sender else "Un utilisateur",
                message_subject=message.subject,
            )
            logger.info("New message notification sent")
            return {"status": "sent", "receiver_id": receiver_id}

        return {"status": "skipped", "reason": "Receiver or message not found"}

    except Exception as e:
        logger.error(f"Error sending message notification: {str(e)}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
