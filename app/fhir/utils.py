"""
FHIR utilities for standardized responses (OperationOutcome, Bundle, CapabilityStatement helpers).
"""

from typing import Any, Dict, Iterable, Optional


def operation_outcome(
    code: str,
    diagnostics: Optional[str] = None,
    severity: str = "error",
) -> Dict[str, Any]:
    """Build a minimal FHIR OperationOutcome resource.

    Args:
        code: FHIR issue type code (e.g., 'not-found', 'invalid', 'forbidden').
        diagnostics: Human readable details.
        severity: 'fatal' | 'error' | 'warning' | 'information'.

    Returns:
        OperationOutcome resource dict.
    """
    issue = {
        "severity": severity,
        "code": code,
    }
    if diagnostics:
        issue["diagnostics"] = diagnostics
    return {"resourceType": "OperationOutcome", "issue": [issue]}


def make_search_bundle(
    *,
    base_url: str,
    resource_type: str,
    resources: Iterable[Dict[str, Any]],
    total: int,
    page: int = 1,
    count: int = 20,
    query_params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a minimal FHIR searchset Bundle for given resources with paging links.

    Args:
        base_url: API base URL (e.g., https://host/api/v1/fhir)
        resource_type: FHIR resource type name (e.g., 'Patient')
        resources: iterable of FHIR resource dicts
        total: total number of matching resources (before pagination)
        page: current page (1-indexed)
        count: items per page
        query_params: original search query parameters (for paging links)

    Returns:
        FHIR Bundle resource dict (type=searchset) with HATEOAS paging links
    """
    entries = []
    for res in resources:
        full_url = f"{base_url}/{resource_type}/{res.get('id')}"
        entries.append(
            {
                "fullUrl": full_url,
                "resource": res,
                "search": {"mode": "match"},
            }
        )

    bundle: Dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": entries,
    }

    # Add paging links (HATEOAS)
    if query_params is not None:
        base_search_url = f"{base_url}/{resource_type}"
        links = []

        # Build query string helper
        def build_query(pg: int) -> str:
            params = dict(query_params)
            params["_page"] = str(pg)
            params["_count"] = str(count)
            qs = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            return f"{base_search_url}?{qs}"

        # self link
        links.append({"relation": "self", "url": build_query(page)})

        # first link
        links.append({"relation": "first", "url": build_query(1)})

        # next link
        last_page = (total + count - 1) // count if count > 0 else 1
        if page < last_page:
            links.append({"relation": "next", "url": build_query(page + 1)})

        # prev link
        if page > 1:
            links.append({"relation": "previous", "url": build_query(page - 1)})

        # last link
        if last_page > 1:
            links.append({"relation": "last", "url": build_query(last_page)})

        bundle["link"] = links

    return bundle
