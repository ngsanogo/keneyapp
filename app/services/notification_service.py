"""
Notification service for sending emails, SMS, and push notifications.
Supports multiple providers and channels.
"""

import os
import logging
from typing import Optional, Dict
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

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
