import types

import pytest


def test_publish_event_queues_matching_webhooks(monkeypatch):
    from app.services import subscription_events as se

    # Stub matching subscriptions
    sub1 = types.SimpleNamespace(id=1)
    sub2 = types.SimpleNamespace(id=2)

    monkeypatch.setattr(se, "_find_matching_subscriptions", lambda db, tenant, rt: [sub1, sub2])

    calls = []

    class DummyTask:
        @staticmethod
        def delay(sub_id, resource):
            calls.append((sub_id, resource))

    monkeypatch.setattr(se, "deliver_subscription_webhook", DummyTask)

    payload = {"resourceType": "Patient", "id": "p1"}
    se.publish_event(db=None, tenant_id=123, resource_type="Patient", fhir_resource=payload)

    assert calls == [(1, payload), (2, payload)]


def test_publish_event_handles_queue_failure(monkeypatch):
    from app.services import subscription_events as se

    sub = types.SimpleNamespace(id=99)
    monkeypatch.setattr(se, "_find_matching_subscriptions", lambda db, tenant, rt: [sub])

    class DummyTask:
        @staticmethod
        def delay(sub_id, resource):  # simulate celery/transport failure
            raise RuntimeError("queue unavailable")

    monkeypatch.setattr(se, "deliver_subscription_webhook", DummyTask)

    # Should not raise
    se.publish_event(
        db=None,
        tenant_id=1,
        resource_type="Patient",
        fhir_resource={"resourceType": "Patient"},
    )
