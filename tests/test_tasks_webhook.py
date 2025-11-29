import types


class _FakeQuery:
    def __init__(self, obj):
        self._obj = obj

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._obj


class _FakeDB:
    def __init__(self, obj):
        self._obj = obj

    def query(self, *args, **kwargs):
        return _FakeQuery(self._obj)

    def close(self):
        pass


def test_deliver_subscription_webhook_success(monkeypatch):
    from app import tasks

    # Fake subscription row
    sub = types.SimpleNamespace(
        id=1, endpoint="https://example.org/hook", payload="application/fhir+json"
    )

    # Patch SessionLocal factory in the database module to return our fake DB
    import app.core.database as dbmod

    class _DummySessionLocal:
        def __call__(self):
            return _FakeDB(sub)

    monkeypatch.setattr(dbmod, "SessionLocal", _DummySessionLocal())

    # Patch requests.post
    class _Resp:
        status_code = 202

    def _post(url, json=None, headers=None, timeout=None):
        assert url == sub.endpoint
        assert headers and headers.get("Content-Type") == sub.payload
        assert json and json.get("resourceType") == "Patient"
        assert timeout == 5
        return _Resp()

    monkeypatch.setitem(tasks.__dict__, "requests", types.SimpleNamespace(post=_post))

    result = tasks.deliver_subscription_webhook(
        subscription_id=1, resource={"resourceType": "Patient"}
    )
    assert result["status"] == "ok"
    assert result["http_status"] == 202


def test_deliver_subscription_webhook_not_found(monkeypatch):
    # No subscription found
    import app.core.database as dbmod
    from app import tasks

    class _DummySessionLocal:
        def __call__(self):
            return _FakeDB(None)

    monkeypatch.setattr(dbmod, "SessionLocal", _DummySessionLocal())

    result = tasks.deliver_subscription_webhook(subscription_id=42, resource={})
    assert result["status"] == "error"
    assert result["reason"] == "subscription_not_found"
