"""Subscription event publisher for FHIR Subscriptions (minimal).

This service finds matching subscriptions for a given resource change and
queues webhook deliveries via Celery tasks.

Matching rule (minimal):
- criteria starts with the resource type (e.g., "Patient", "Appointment", "MedicationRequest")
- tenant_id must match

Future: support search-style criteria (e.g., Patient?identifier=..., Appointment?patient=...).
"""

import logging
from typing import Dict, Iterable

from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionStatus
from app.tasks import deliver_subscription_webhook

logger = logging.getLogger(__name__)


def _find_matching_subscriptions(
    db: Session, tenant_id: int, resource_type: str
) -> Iterable[Subscription]:
    return (
        db.query(Subscription)
        .filter(
            Subscription.tenant_id == tenant_id,
            Subscription.status == SubscriptionStatus.active,
            Subscription.criteria.startswith(resource_type),
        )
        .all()
    )


def publish_event(
    db: Session, tenant_id: int, resource_type: str, fhir_resource: Dict
) -> None:
    """Publish a resource change event to all matching subscriptions.

    Args:
        db: SQLAlchemy session
        tenant_id: Tenant context for multi-tenancy
        resource_type: FHIR resourceType (e.g., "Patient", "Appointment", "MedicationRequest")
        fhir_resource: The FHIR resource payload to deliver
    """
    try:
        subs = _find_matching_subscriptions(db, tenant_id, resource_type)
        for sub in subs:
            try:
                deliver_subscription_webhook.delay(sub.id, fhir_resource)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning(
                    "Failed to queue webhook delivery for subscription %s: %s",
                    sub.id,
                    exc,
                )
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Unexpected error while publishing subscription events: %s", exc)
