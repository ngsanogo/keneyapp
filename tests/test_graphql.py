"""Tests for GraphQL API."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_graphql_endpoint_accessible():
    """Test that GraphQL endpoint is accessible."""
    query = """
    query {
        hello
    }
    """
    
    response = client.post(
        "/graphql",
        json={"query": query}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert data['data']['hello'] == "Hello from KeneyApp GraphQL API!"


def test_graphql_api_version():
    """Test GraphQL API version query."""
    query = """
    query {
        apiVersion
    }
    """
    
    response = client.post(
        "/graphql",
        json={"query": query}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data['data']['apiVersion'] == "1.0.0"


def test_graphql_invalid_query():
    """Test GraphQL with invalid query."""
    query = """
    query {
        nonExistentField
    }
    """
    
    response = client.post(
        "/graphql",
        json={"query": query}
    )
    
    # Should return 400 or have errors
    data = response.json()
    assert 'errors' in data


def test_graphql_introspection():
    """Test GraphQL introspection query."""
    query = """
    {
        __schema {
            types {
                name
            }
        }
    }
    """
    
    response = client.post(
        "/graphql",
        json={"query": query}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert 'data' in data
    assert '__schema' in data['data']
