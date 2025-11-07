"""Tests for FHIR utility helpers."""

# flake8: noqa: E402
import os

os.environ["TESTING"] = "true"

from app.fhir.utils import operation_outcome, make_search_bundle


def test_operation_outcome_structure():
    """Ensure operation_outcome returns valid FHIR OperationOutcome structure."""
    outcome = operation_outcome("not-found", "Patient not found")
    
    assert outcome["resourceType"] == "OperationOutcome"
    assert isinstance(outcome["issue"], list)
    assert len(outcome["issue"]) == 1
    assert outcome["issue"][0]["severity"] == "error"
    assert outcome["issue"][0]["code"] == "not-found"
    assert outcome["issue"][0]["diagnostics"] == "Patient not found"


def test_operation_outcome_without_details():
    """Ensure operation_outcome works with minimal arguments."""
    outcome = operation_outcome("invalid")
    
    assert outcome["resourceType"] == "OperationOutcome"
    assert outcome["issue"][0]["code"] == "invalid"
    assert "diagnostics" not in outcome["issue"][0] or outcome["issue"][0]["diagnostics"] is None


def test_make_search_bundle_structure():
    """Ensure make_search_bundle returns valid FHIR Bundle searchset."""
    resources = [
        {"resourceType": "Patient", "id": "1"},
        {"resourceType": "Patient", "id": "2"},
    ]
    
    bundle = make_search_bundle(
        base_url="http://test.com/api/v1/fhir",
        resource_type="Patient",
        resources=resources,
        total=10,
        page=1,
        count=2,
        query_params={"name": "Smith"},
    )
    
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] == 10
    assert len(bundle["entry"]) == 2
    assert bundle["entry"][0]["resource"]["id"] == "1"
    
    # Check links
    assert "link" in bundle
    link_rels = {link["relation"] for link in bundle["link"]}
    assert "self" in link_rels


def test_make_search_bundle_pagination_links():
    """Ensure pagination links are correct for multi-page results."""
    resources = [{"resourceType": "Patient", "id": str(i)} for i in range(20)]
    
    bundle = make_search_bundle(
        base_url="http://test.com/api/v1/fhir",
        resource_type="Patient",
        resources=resources,
        total=100,
        page=2,
        count=20,
        query_params={},
    )
    
    link_rels = {link["relation"] for link in bundle["link"]}
    assert "next" in link_rels
    assert "previous" in link_rels
