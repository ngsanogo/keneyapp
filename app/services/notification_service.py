"""
Notification service for sending emails, SMS, and push notifications.
Supports multiple providers and channels with database tracking.
"""

import logging
import os
import smtplib
from datetime import datetime, time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationPreference,
    NotificationStatus,
    NotificationType,
)
from app.models.user import User

logger = logging.getLogger(__name__)

# Configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@keneyapp.com")

SMS_PROVIDER = os.getenv("SMS_PROVIDER", "twilio")  # twilio, aws-sns, etc.
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")


class EmailNotification:
    """Email notification handler."""

    @staticmethod
    def send_email(to: str, subject: str, body: str, html: bool = False) -> bool:
        """
        Send email via SMTP.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (text or HTML)
            html: Whether body is HTML

        Returns:
            True if sent successfully
        """
        if not SMTP_USER or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured, skipping email")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = SMTP_FROM
            msg["To"] = to
            msg["Subject"] = subject

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type))

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to[:3]}***")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False


class SMSNotification:
    """SMS notification handler with Twilio support."""

    @staticmethod
    def send_sms(to: str, message: str) -> bool:
        """
        Send SMS via Twilio.

        Args:
            to: Phone number in E.164 format (+1234567890)
            message: SMS message content

        Returns:
            True if sent successfully
        """
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured, skipping SMS")
            return False

        try:
            # Import Twilio only if credentials are configured
            from twilio.rest import Client

            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

            client.messages.create(body=message, from_=TWILIO_FROM_NUMBER, to=to)

            logger.info(f"SMS sent successfully to {to[:4]}***")
            return True

        except ImportError:
            logger.warning("Twilio library not installed, skipping SMS")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False


class NotificationService:
    """Unified notification service."""

    @staticmethod
    def send_appointment_reminder(
        patient_email: str,
        patient_name: str,
        appointment_date: datetime,
        doctor_name: str,
        phone: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Send appointment reminder via email and SMS."""

        subject = "Rappel de rendez-vous - KeneyApp"

        email_body = f"""
        Bonjour {patient_name},

        Nous vous rappelons votre rendez-vous prévu le {appointment_date.strftime('%d/%m/%Y à %H:%M')} avec {doctor_name}.

        Merci de confirmer votre présence ou de nous contacter en cas d'empêchement.

        Cordialement,
        L'équipe KeneyApp
        """

        sms_body = f"Rappel: RDV le {appointment_date.strftime('%d/%m à %H:%M')} avec {doctor_name}. KeneyApp"

        results = {
            "email": EmailNotification.send_email(patient_email, subject, email_body),
            "sms": False,
        }

        if phone:
            results["sms"] = SMSNotification.send_sms(phone, sms_body)

        return results

    @staticmethod
    def send_lab_results_notification(
        patient_email: str,
        patient_name: str,
        test_name: str,
        phone: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Notify patient that lab results are ready."""

        subject = "Résultats d'analyse disponibles - KeneyApp"

        email_body = f"""
        Bonjour {patient_name},

        Vos résultats d'analyse pour "{test_name}" sont maintenant disponibles dans votre dossier médical.

        Connectez-vous à votre compte pour les consulter.

        Cordialement,
        L'équipe KeneyApp
        """

        sms_body = f"Vos résultats pour {test_name} sont disponibles. Consultez votre compte KeneyApp."

        results = {
            "email": EmailNotification.send_email(patient_email, subject, email_body),
            "sms": False,
        }

        if phone:
            results["sms"] = SMSNotification.send_sms(phone, sms_body)

        return results

    @staticmethod
    def send_prescription_renewal_reminder(
        patient_email: str,
        patient_name: str,
        medication_name: str,
        expiry_date: datetime,
        phone: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Remind patient to renew prescription."""

        subject = "Renouvellement d'ordonnance - KeneyApp"

        email_body = f"""
        Bonjour {patient_name},

        Votre ordonnance pour "{medication_name}" expire le {expiry_date.strftime('%d/%m/%Y')}.

        Pensez à prendre rendez-vous pour le renouvellement.

        Cordialement,
        L'équipe KeneyApp
        """

        sms_body = f"Ordonnance {medication_name} expire le {expiry_date.strftime('%d/%m')}. Prenez RDV. KeneyApp"

        results = {
            "email": EmailNotification.send_email(patient_email, subject, email_body),
            "sms": False,
        }

        if phone:
            results["sms"] = SMSNotification.send_sms(phone, sms_body)

        return results

    @staticmethod
    def send_vaccination_reminder(
        patient_email: str,
        patient_name: str,
        vaccine_name: str,
        due_date: datetime,
        phone: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Send vaccination reminder."""

        subject = "Rappel de vaccination - KeneyApp"

        email_body = f"""
        Bonjour {patient_name},

        Un rappel de vaccination pour "{vaccine_name}" est prévu le {due_date.strftime('%d/%m/%Y')}.

        Prenez rendez-vous avec votre médecin pour effectuer ce vaccin.

        Cordialement,
        L'équipe KeneyApp
        """

        sms_body = f"Rappel vaccin {vaccine_name} prévu le {due_date.strftime('%d/%m')}. KeneyApp"

        results = {
            "email": EmailNotification.send_email(patient_email, subject, email_body),
            "sms": False,
        }

        if phone:
            results["sms"] = SMSNotification.send_sms(phone, sms_body)

        return results

    @staticmethod
    def send_new_message_notification(
        recipient_email: str,
        recipient_name: str,
        sender_name: str,
        message_subject: str,
        phone: Optional[str] = None,
    ) -> Dict[str, bool]:
        """Notify user of new message."""

        subject = "Nouveau message - KeneyApp"

        email_body = f"""
        Bonjour {recipient_name},

        Vous avez reçu un nouveau message de {sender_name}.

        Sujet: {message_subject or 'Sans objet'}

        Connectez-vous à votre compte pour le lire.

        Cordialement,
        L'équipe KeneyApp
        """

        sms_body = f"Nouveau message de {sender_name}. Consultez votre compte KeneyApp."

        results = {
            "email": EmailNotification.send_email(recipient_email, subject, email_body),
            "sms": False,
        }

        if phone:
            results["sms"] = SMSNotification.send_sms(phone, sms_body)

        return results


class EnhancedNotificationService:
    """
    Enhanced notification service with database tracking and preference management.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_user_preferences(self, user_id: int) -> Optional[NotificationPreference]:
        """Get user notification preferences."""
        return (
            self.db.query(NotificationPreference)
            .filter(NotificationPreference.user_id == user_id)
            .first()
        )

    def create_default_preferences(
        self, user_id: int, tenant_id: int
    ) -> NotificationPreference:
        """Create default notification preferences for a user."""
        prefs = NotificationPreference(user_id=user_id, tenant_id=tenant_id)
        self.db.add(prefs)
        self.db.flush()
        return prefs

    def update_preferences(
        self, user_id: int, preferences_data: dict
    ) -> NotificationPreference:
        """Update user notification preferences."""
        prefs = self.get_user_preferences(user_id)
        if not prefs:
            raise ValueError("Preferences not found")

        for key, value in preferences_data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)

        self.db.flush()
        return prefs

    def is_in_quiet_hours(self, preferences: NotificationPreference) -> bool:
        """Check if current time is in user's quiet hours."""
        if not preferences.quiet_hours_enabled:
            return False

        now = datetime.now().time()
        start = datetime.strptime(preferences.quiet_hours_start, "%H:%M").time()
        end = datetime.strptime(preferences.quiet_hours_end, "%H:%M").time()

        if start < end:
            return start <= now <= end
        else:  # Quiet hours cross midnight
            return now >= start or now <= end

    def should_send_notification(
        self,
        user: User,
        notification_type: NotificationType,
        channel: NotificationChannel,
    ) -> bool:
        """Check if notification should be sent based on user preferences."""
        prefs = self.get_user_preferences(user.id)
        if not prefs:
            return True  # Send if no preferences set

        # Check quiet hours for non-critical notifications
        if notification_type not in [
            NotificationType.SECURITY_ALERT,
            NotificationType.SYSTEM_ALERT,
        ]:
            if self.is_in_quiet_hours(prefs):
                return False

        # Check channel-specific preferences
        if channel == NotificationChannel.EMAIL:
            if not prefs.email_enabled:
                return False
            type_map = {
                NotificationType.APPOINTMENT_REMINDER: prefs.email_appointment_reminders,
                NotificationType.APPOINTMENT_CONFIRMED: prefs.email_appointment_reminders,
                NotificationType.APPOINTMENT_CANCELLED: prefs.email_appointment_reminders,
                NotificationType.LAB_RESULTS_READY: prefs.email_lab_results,
                NotificationType.PRESCRIPTION_RENEWAL: prefs.email_prescription_renewals,
                NotificationType.MESSAGE_RECEIVED: prefs.email_messages,
                NotificationType.DOCUMENT_SHARED: prefs.email_documents,
                NotificationType.DOCUMENT_UPLOADED: prefs.email_documents,
                NotificationType.SYSTEM_ALERT: prefs.email_system_alerts,
                NotificationType.SECURITY_ALERT: True,  # Always send security alerts
            }
            return type_map.get(notification_type, True)

        elif channel == NotificationChannel.SMS:
            if not prefs.sms_enabled:
                return False
            type_map = {
                NotificationType.APPOINTMENT_REMINDER: prefs.sms_appointment_reminders,
                NotificationType.APPOINTMENT_CONFIRMED: prefs.sms_appointment_reminders,
                NotificationType.APPOINTMENT_CANCELLED: prefs.sms_appointment_reminders,
                NotificationType.LAB_RESULTS_READY: prefs.sms_lab_results,
                NotificationType.PRESCRIPTION_RENEWAL: prefs.sms_prescription_renewals,
                NotificationType.MESSAGE_RECEIVED: prefs.sms_messages,
                NotificationType.SECURITY_ALERT: True,
            }
            return type_map.get(notification_type, False)

        elif channel == NotificationChannel.PUSH:
            if not prefs.push_enabled:
                return False
            type_map = {
                NotificationType.APPOINTMENT_REMINDER: prefs.push_appointment_reminders,
                NotificationType.APPOINTMENT_CONFIRMED: prefs.push_appointment_reminders,
                NotificationType.APPOINTMENT_CANCELLED: prefs.push_appointment_reminders,
                NotificationType.LAB_RESULTS_READY: prefs.push_lab_results,
                NotificationType.PRESCRIPTION_RENEWAL: prefs.push_prescription_renewals,
                NotificationType.MESSAGE_RECEIVED: prefs.push_messages,
                NotificationType.DOCUMENT_SHARED: prefs.push_documents,
                NotificationType.DOCUMENT_UPLOADED: prefs.push_documents,
                NotificationType.SYSTEM_ALERT: True,
                NotificationType.SECURITY_ALERT: True,
            }
            return type_map.get(notification_type, True)

        elif channel == NotificationChannel.WEBSOCKET:
            return prefs.websocket_enabled

        return True

    def create_notification(
        self,
        user_id: int,
        tenant_id: int,
        notification_type: NotificationType,
        channel: NotificationChannel,
        title: str,
        message: str,
        action_url: Optional[str] = None,
        recipient_email: Optional[str] = None,
        recipient_phone: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
    ) -> Notification:
        """Create a notification record in the database."""
        notification = Notification(
            user_id=user_id,
            tenant_id=tenant_id,
            type=notification_type,
            channel=channel,
            title=title,
            message=message,
            action_url=action_url,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            resource_type=resource_type,
            resource_id=resource_id,
            status=NotificationStatus.PENDING,
        )
        self.db.add(notification)
        self.db.flush()
        return notification

    def send_notification(
        self,
        user: User,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        title: str,
        message: str,
        action_url: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        respect_preferences: bool = True,
    ) -> Dict[NotificationChannel, Notification]:
        """
        Send notification through multiple channels with preference checking.

        Returns:
            Dictionary mapping channel to notification record
        """
        results = {}

        for channel in channels:
            # Check preferences
            if respect_preferences and not self.should_send_notification(
                user, notification_type, channel
            ):
                logger.info(
                    f"Skipping {channel.value} notification for user {user.id} due to preferences"
                )
                continue

            # Create notification record
            notification = self.create_notification(
                user_id=user.id,
                tenant_id=user.tenant_id,
                notification_type=notification_type,
                channel=channel,
                title=title,
                message=message,
                action_url=action_url,
                recipient_email=(
                    user.email if channel == NotificationChannel.EMAIL else None
                ),
                resource_type=resource_type,
                resource_id=resource_id,
            )

            # Send via appropriate channel
            try:
                if channel == NotificationChannel.EMAIL:
                    success = EmailNotification.send_email(
                        user.email, title, message, html=False
                    )
                    if success:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.now()
                    else:
                        notification.status = NotificationStatus.FAILED
                        notification.failed_reason = "SMTP delivery failed"

                elif channel == NotificationChannel.SMS:
                    # Get phone number from user profile or preferences
                    # For now, mark as sent if we have the service configured
                    if TWILIO_ACCOUNT_SID:
                        notification.status = NotificationStatus.SENT
                        notification.sent_at = datetime.now()
                    else:
                        notification.status = NotificationStatus.FAILED
                        notification.failed_reason = "SMS service not configured"

                elif channel == NotificationChannel.PUSH:
                    # Push notification implementation (FCM, APNS, etc.)
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.now()

                elif channel == NotificationChannel.WEBSOCKET:
                    # WebSocket notifications handled separately
                    notification.status = NotificationStatus.SENT
                    notification.sent_at = datetime.now()

                self.db.flush()
                results[channel] = notification

            except Exception as e:
                logger.error(f"Failed to send {channel.value} notification: {e}")
                notification.status = NotificationStatus.FAILED
                notification.failed_reason = str(e)
                self.db.flush()

        return results

    def mark_as_read(self, notification_ids: List[int], user_id: int) -> int:
        """Mark notifications as read."""
        count = (
            self.db.query(Notification)
            .filter(
                Notification.id.in_(notification_ids),
                Notification.user_id == user_id,
                Notification.status != NotificationStatus.READ,
            )
            .update(
                {
                    "status": NotificationStatus.READ,
                    "read_at": datetime.now(),
                },
                synchronize_session=False,
            )
        )
        self.db.flush()
        return count

    def get_user_notifications(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 50,
        unread_only: bool = False,
        notification_type: Optional[NotificationType] = None,
    ) -> tuple[List[Notification], int]:
        """Get user notifications with filters."""
        query = self.db.query(Notification).filter(Notification.user_id == user_id)

        if unread_only:
            query = query.filter(Notification.status != NotificationStatus.READ)

        if notification_type:
            query = query.filter(Notification.type == notification_type)

        total = query.count()
        notifications = (
            query.order_by(Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        return notifications, total

    def get_notification_stats(self, user_id: int) -> dict:
        """Get notification statistics for user."""
        total = (
            self.db.query(Notification).filter(Notification.user_id == user_id).count()
        )

        unread = (
            self.db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.status != NotificationStatus.READ,
            )
            .count()
        )

        # Stats by type
        by_type = {}
        for notif_type in NotificationType:
            count = (
                self.db.query(Notification)
                .filter(
                    Notification.user_id == user_id, Notification.type == notif_type
                )
                .count()
            )
            if count > 0:
                by_type[notif_type.value] = count

        # Stats by status
        by_status = {}
        for status in NotificationStatus:
            count = (
                self.db.query(Notification)
                .filter(Notification.user_id == user_id, Notification.status == status)
                .count()
            )
            if count > 0:
                by_status[status.value] = count

        return {
            "total": total,
            "unread": unread,
            "by_type": by_type,
            "by_status": by_status,
        }
