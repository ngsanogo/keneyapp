"""
Tests for common schemas (pagination, filtering, sorting, responses)
"""

from datetime import date, datetime

import pytest

from app.schemas.common import (
    BulkOperationRequest,
    BulkOperationResponse,
    ErrorDetail,
    ErrorResponse,
    ExportRequest,
    FilterParams,
    PaginatedResponse,
    PaginationParams,
    SortParams,
    SuccessResponse,
)


def test_pagination_params_defaults():
    """Test default pagination parameters"""
    params = PaginationParams()
    assert params.page == 1
    assert params.page_size == 50
    assert params.skip == 0
    assert params.limit == 50


def test_pagination_params_custom():
    """Test custom pagination parameters"""
    params = PaginationParams(page=3, page_size=25)
    assert params.page == 3
    assert params.page_size == 25
    assert params.skip == 50  # (3-1) * 25
    assert params.limit == 25


def test_pagination_params_validation():
    """Test pagination validation"""
    # Page must be >= 1
    with pytest.raises(ValueError):
        PaginationParams(page=0)

    # Page size must be 1-100
    with pytest.raises(ValueError):
        PaginationParams(page_size=0)

    with pytest.raises(ValueError):
        PaginationParams(page_size=101)


def test_sort_params_defaults():
    """Test default sort parameters"""
    params = SortParams()
    assert params.sort_by is None
    assert params.sort_order == "asc"


def test_sort_params_validation():
    """Test sort parameter validation"""
    # Valid sort_by pattern
    params = SortParams(sort_by="created_at", sort_order="desc")
    assert params.sort_by == "created_at"
    assert params.sort_order == "desc"

    # Invalid sort_by (no special characters except underscore)
    with pytest.raises(ValueError):
        SortParams(sort_by="user.name")  # Dot not allowed

    # Invalid sort_order
    with pytest.raises(ValueError):
        SortParams(sort_order="invalid")


def test_filter_params():
    """Test filter parameters"""
    from datetime import datetime

    params = FilterParams(search="test", date_from=date(2024, 1, 1), date_to=date(2024, 12, 31))
    assert params.search == "test"
    # Pydantic converts date to datetime
    assert params.date_from == datetime(2024, 1, 1, 0, 0)
    assert params.date_to == datetime(2024, 12, 31, 0, 0)


def test_filter_params_date_validation():
    """Test date_from must be before date_to"""
    with pytest.raises(ValueError, match="date_from must be before date_to"):
        FilterParams(date_from=date(2024, 12, 31), date_to=date(2024, 1, 1))


def test_paginated_response():
    """Test paginated response creation"""
    items = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]

    response = PaginatedResponse.create(items=items, total=100, page=2, page_size=2)

    assert response.items == items
    assert response.total == 100
    assert response.page == 2
    assert response.page_size == 2
    assert response.total_pages == 50  # ceil(100 / 2)
    assert response.has_next is True
    assert response.has_prev is True


def test_paginated_response_edges():
    """Test paginated response at boundaries"""
    # First page
    response = PaginatedResponse.create(items=[1, 2, 3], total=10, page=1, page_size=3)
    assert response.has_prev is False
    assert response.has_next is True

    # Last page
    response = PaginatedResponse.create(items=[10], total=10, page=4, page_size=3)
    assert response.has_prev is True
    assert response.has_next is False


def test_success_response():
    """Test success response"""
    response = SuccessResponse(message="Operation completed", data={"id": 123})
    assert response.success is True
    assert response.message == "Operation completed"
    assert response.data == {"id": 123}


def test_error_response():
    """Test error response"""
    details = [ErrorDetail(field="email", message="Invalid email format", code="invalid_email")]

    response = ErrorResponse(error="Validation failed", details=details)

    assert response.success is False
    assert response.error == "Validation failed"
    assert len(response.details) == 1
    assert response.details[0].field == "email"
    assert response.timestamp is not None


def test_bulk_operation_request():
    """Test bulk operation request"""
    request = BulkOperationRequest(ids=[1, 2, 3], action="delete", params={"reason": "cleanup"})
    assert request.ids == [1, 2, 3]
    assert request.action == "delete"
    assert request.params == {"reason": "cleanup"}


def test_bulk_operation_request_validation():
    """Test bulk operation validation (1-100 ids)"""
    # Empty ids
    with pytest.raises(ValueError):
        BulkOperationRequest(ids=[], action="delete")

    # Too many ids
    with pytest.raises(ValueError):
        BulkOperationRequest(ids=list(range(101)), action="delete")


def test_bulk_operation_response():
    """Test bulk operation response"""
    errors = [{"id": 2, "error": "Not found"}, {"id": 5, "error": "Permission denied"}]

    response = BulkOperationResponse.create(success_count=8, errors=errors)

    assert response.success_count == 8
    assert response.failure_count == 2
    assert response.total == 10
    assert response.errors == errors


def test_export_request():
    """Test export request"""
    request = ExportRequest(
        format="xlsx", filters={"status": "active"}, columns=["id", "name", "email"]
    )
    assert request.format == "xlsx"
    assert request.filters == {"status": "active"}
    assert request.columns == ["id", "name", "email"]


def test_export_request_validation():
    """Test export format validation"""
    # Valid formats
    for fmt in ["csv", "xlsx", "pdf", "json"]:
        request = ExportRequest(format=fmt)
        assert request.format == fmt

    # Invalid format
    with pytest.raises(ValueError):
        ExportRequest(format="txt")
