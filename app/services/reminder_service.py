"""
Reminder service for automated appointment notifications.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models.appointment import Appointment, AppointmentStatus
from app.models.appointment_reminder import (
    AppointmentReminder,
    ReminderChannel,
    ReminderStatus,
)
from app.models.patient import Patient
from app.models.user import User
from app.services.notification_service import NotificationService, NotificationType

logger = logging.getLogger(__name__)


class ReminderService:
    """Service for managing appointment reminders."""

    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)

    def create_reminders_for_appointment(
        self,
        appointment_id: int,
        tenant_id: int,
        channels: Optional[List[ReminderChannel]] = None,
        hours_before: Optional[List[int]] = None,
    ) -> List[AppointmentReminder]:
        """
        Create automated reminders for an appointment.

        Args:
            appointment_id: ID of the appointment
            tenant_id: Tenant ID
            channels: List of channels (defaults to [EMAIL, SMS])
            hours_before: List of hours before appointment (defaults to [24, 2])

        Returns:
            List of created reminders
        """
        if channels is None:
            channels = [ReminderChannel.EMAIL, ReminderChannel.SMS]

        if hours_before is None:
            hours_before = [24, 2]  # 24 hours and 2 hours before

        appointment = (
            self.db.query(Appointment)
            .filter(
                Appointment.id == appointment_id, Appointment.tenant_id == tenant_id
            )
            .first()
        )

        if not appointment:
            raise ValueError(f"Appointment {appointment_id} not found")

        if appointment.status in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ]:
            logger.info(
                f"Skipping reminders for cancelled/completed appointment {appointment_id}"
            )
            return []

        reminders = []
        for hours in hours_before:
            scheduled_time = appointment.appointment_date - timedelta(hours=hours)

            # Don't create reminders for past times
            if scheduled_time <= datetime.now(scheduled_time.tzinfo):
                logger.warning(
                    f"Skipping past reminder time for appointment {appointment_id}"
                )
                continue

            for channel in channels:
                reminder = AppointmentReminder(
                    tenant_id=tenant_id,
                    appointment_id=appointment_id,
                    scheduled_time=scheduled_time,
                    channel=channel,
                    hours_before=hours,
                    status=ReminderStatus.PENDING,
                )
                self.db.add(reminder)
                reminders.append(reminder)

        if reminders:
            self.db.commit()
            logger.info(
                f"Created {len(reminders)} reminders for appointment {appointment_id}"
            )

        return reminders

    def get_due_reminders(
        self, tenant_id: Optional[int] = None
    ) -> List[AppointmentReminder]:
        """
        Get all reminders that are due to be sent.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            List of due reminders
        """
        query = self.db.query(AppointmentReminder).filter(
            AppointmentReminder.status == ReminderStatus.PENDING,
            AppointmentReminder.scheduled_time <= datetime.now(),
        )

        if tenant_id:
            query = query.filter(AppointmentReminder.tenant_id == tenant_id)

        return query.all()

    def send_reminder(self, reminder_id: int) -> bool:
        """
        Send a specific reminder.

        Args:
            reminder_id: ID of the reminder to send

        Returns:
            True if successful, False otherwise
        """
        reminder = (
            self.db.query(AppointmentReminder)
            .filter(AppointmentReminder.id == reminder_id)
            .first()
        )

        if not reminder:
            logger.error(f"Reminder {reminder_id} not found")
            return False

        if reminder.status != ReminderStatus.PENDING:
            logger.warning(
                f"Reminder {reminder_id} is not pending (status: {reminder.status})"
            )
            return False

        # Get appointment details
        appointment = (
            self.db.query(Appointment)
            .filter(Appointment.id == reminder.appointment_id)
            .first()
        )

        if not appointment:
            logger.error(f"Appointment {reminder.appointment_id} not found")
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = "Appointment not found"
            self.db.commit()
            return False

        # Check if appointment is still valid
        if appointment.status in [
            AppointmentStatus.CANCELLED,
            AppointmentStatus.COMPLETED,
        ]:
            logger.info(f"Cancelling reminder for {appointment.status} appointment")
            reminder.status = ReminderStatus.CANCELLED
            self.db.commit()
            return False

        # Get patient and doctor details
        patient = (
            self.db.query(Patient).filter(Patient.id == appointment.patient_id).first()
        )
        doctor = self.db.query(User).filter(User.id == appointment.doctor_id).first()

        if not patient or not doctor:
            logger.error(
                f"Patient or doctor not found for appointment {appointment.id}"
            )
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = "Patient or doctor not found"
            self.db.commit()
            return False

        # Format reminder message
        appointment_time = appointment.appointment_date.strftime(
            "%B %d, %Y at %I:%M %p"
        )
        message = (
            f"Reminder: You have an appointment with Dr. {doctor.full_name} "
            f"on {appointment_time}. Reason: {appointment.reason}. "
            f"Please arrive 10 minutes early."
        )

        try:
            # Send via notification service
            notification_type = NotificationType.APPOINTMENT_REMINDER
            success = False

            if reminder.channel == ReminderChannel.EMAIL:
                # Create notification (notification service will handle email)
                self.notification_service.create_notification(
                    tenant_id=reminder.tenant_id,
                    user_id=patient.id,  # Assuming patient has a user account
                    notification_type=notification_type,
                    title=f"Appointment Reminder - {reminder.hours_before}h",
                    message=message,
                    metadata={
                        "appointment_id": appointment.id,
                        "doctor_name": doctor.full_name,
                        "appointment_date": appointment.appointment_date.isoformat(),
                    },
                    channels=["email"],
                )
                success = True

            elif reminder.channel == ReminderChannel.SMS:
                # SMS would be sent via external service (Twilio, etc.)
                # For now, create a notification
                self.notification_service.create_notification(
                    tenant_id=reminder.tenant_id,
                    user_id=patient.id,
                    notification_type=notification_type,
                    title=f"Appointment in {reminder.hours_before}h",
                    message=message[:160],  # SMS limit
                    metadata={
                        "appointment_id": appointment.id,
                        "phone": patient.phone,
                    },
                    channels=["sms"],
                )
                success = True

            elif reminder.channel == ReminderChannel.PUSH:
                # Push notification
                self.notification_service.create_notification(
                    tenant_id=reminder.tenant_id,
                    user_id=patient.id,
                    notification_type=notification_type,
                    title="Appointment Reminder",
                    message=message,
                    metadata={"appointment_id": appointment.id},
                    channels=["push"],
                )
                success = True

            if success:
                reminder.status = ReminderStatus.SENT
                reminder.sent_at = datetime.now()
                logger.info(
                    f"Successfully sent {reminder.channel} reminder for appointment {appointment.id}"
                )
            else:
                raise Exception("Failed to send via any channel")

        except Exception as e:
            logger.error(f"Failed to send reminder {reminder_id}: {str(e)}")
            reminder.status = ReminderStatus.FAILED
            reminder.error_message = str(e)[:500]
            reminder.retry_count += 1

            # If can retry, reset to pending
            if reminder.can_retry:
                reminder.status = ReminderStatus.PENDING
                # Schedule retry in 15 minutes
                reminder.scheduled_time = datetime.now() + timedelta(minutes=15)
                logger.info(
                    f"Scheduling retry {reminder.retry_count} for reminder {reminder_id}"
                )

        self.db.commit()
        return reminder.status == ReminderStatus.SENT

    def process_due_reminders(self, tenant_id: Optional[int] = None) -> dict:
        """
        Process all due reminders.

        Args:
            tenant_id: Optional tenant filter

        Returns:
            Dictionary with success/failure counts
        """
        due_reminders = self.get_due_reminders(tenant_id)
        results = {"total": len(due_reminders), "sent": 0, "failed": 0}

        logger.info(f"Processing {len(due_reminders)} due reminders")

        for reminder in due_reminders:
            success = self.send_reminder(reminder.id)
            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

        logger.info(
            f"Processed {results['total']} reminders: "
            f"{results['sent']} sent, {results['failed']} failed"
        )

        return results

    def cancel_reminders_for_appointment(
        self, appointment_id: int, tenant_id: int
    ) -> int:
        """
        Cancel all pending reminders for an appointment.

        Args:
            appointment_id: ID of the appointment
            tenant_id: Tenant ID

        Returns:
            Number of reminders cancelled
        """
        count = (
            self.db.query(AppointmentReminder)
            .filter(
                AppointmentReminder.appointment_id == appointment_id,
                AppointmentReminder.tenant_id == tenant_id,
                AppointmentReminder.status == ReminderStatus.PENDING,
            )
            .update(
                {
                    "status": ReminderStatus.CANCELLED,
                    "updated_at": datetime.now(),
                }
            )
        )

        self.db.commit()
        logger.info(f"Cancelled {count} reminders for appointment {appointment_id}")
        return count

    def get_reminders_for_appointment(
        self, appointment_id: int, tenant_id: int
    ) -> List[AppointmentReminder]:
        """
        Get all reminders for an appointment.

        Args:
            appointment_id: ID of the appointment
            tenant_id: Tenant ID

        Returns:
            List of reminders
        """
        return (
            self.db.query(AppointmentReminder)
            .filter(
                AppointmentReminder.appointment_id == appointment_id,
                AppointmentReminder.tenant_id == tenant_id,
            )
            .order_by(AppointmentReminder.scheduled_time)
            .all()
        )
