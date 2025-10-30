# Testing Guide for KeneyApp

## Overview
This guide provides comprehensive testing strategies and best practices for KeneyApp, covering unit tests, integration tests, end-to-end tests, and performance testing.

## Table of Contents
1. [Testing Philosophy](#testing-philosophy)
2. [Backend Testing](#backend-testing)
3. [Frontend Testing](#frontend-testing)
4. [Integration Testing](#integration-testing)
5. [Performance Testing](#performance-testing)
6. [Security Testing](#security-testing)
7. [Test Coverage](#test-coverage)
8. [CI/CD Integration](#cicd-integration)
9. [Best Practices](#best-practices)

## Testing Philosophy

### Test Pyramid
```
        /\
       /  \      E2E Tests (Few)
      /----\     
     /      \    Integration Tests (Some)
    /--------\   
   /          \  Unit Tests (Many)
  /____________\
```

- **Unit Tests (70%)**: Fast, isolated, test individual functions
- **Integration Tests (20%)**: Test component interactions
- **E2E Tests (10%)**: Test complete user workflows

### Key Principles
1. **Fast**: Tests should run quickly
2. **Isolated**: Tests shouldn't depend on each other
3. **Repeatable**: Same result every time
4. **Self-validating**: Clear pass/fail
5. **Timely**: Write tests alongside code

## Backend Testing

### Setup

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_api.py -v

# Run specific test
pytest tests/test_api.py::test_root_endpoint -v
```

### Unit Tests

#### Testing Models

```python
# tests/test_models.py
import pytest
from datetime import date
from app.models.patient import Patient, Gender

def test_patient_creation():
    """Test creating a patient model."""
    patient = Patient(
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 15),
        gender=Gender.MALE,
        email="john@example.com",
        phone="+1234567890"
    )
    
    assert patient.first_name == "John"
    assert patient.last_name == "Doe"
    assert patient.gender == Gender.MALE
    
def test_patient_full_name_property():
    """Test patient full name property."""
    patient = Patient(
        first_name="Jane",
        last_name="Smith",
        date_of_birth=date(1985, 5, 20),
        gender=Gender.FEMALE,
        phone="+1234567890"
    )
    
    # If you add a full_name property
    # assert patient.full_name == "Jane Smith"
```

#### Testing Services

```python
# tests/test_services.py
import pytest
from unittest.mock import Mock, patch
from app.services.notification import NotificationService

def test_send_appointment_reminder():
    """Test sending appointment reminder."""
    # Mock email service
    with patch('app.services.notification.send_email') as mock_send:
        mock_send.return_value = True
        
        service = NotificationService()
        result = service.send_appointment_reminder(
            email="patient@example.com",
            appointment_time="2024-01-15 10:00"
        )
        
        assert result is True
        mock_send.assert_called_once()
        
def test_send_reminder_handles_failure():
    """Test handling of email send failure."""
    with patch('app.services.notification.send_email') as mock_send:
        mock_send.side_effect = Exception("SMTP error")
        
        service = NotificationService()
        result = service.send_appointment_reminder(
            email="patient@example.com",
            appointment_time="2024-01-15 10:00"
        )
        
        assert result is False
```

#### Testing Utilities

```python
# tests/test_security.py
import pytest
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_access_token
)

def test_password_hashing():
    """Test password hashing and verification."""
    password = "SecurePassword123!"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_creation():
    """Test JWT token creation and decoding."""
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data)
    
    assert token is not None
    assert isinstance(token, str)
    
    decoded = decode_access_token(token)
    assert decoded["sub"] == "testuser"
    assert decoded["role"] == "admin"

def test_jwt_token_expiration():
    """Test JWT token expiration."""
    from datetime import timedelta
    
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(seconds=1))
    
    # Wait for token to expire
    import time
    time.sleep(2)
    
    decoded = decode_access_token(token)
    assert decoded is None  # Expired token should return None
```

### Integration Tests

#### Testing API Endpoints

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Fixture to provide authentication headers."""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_and_retrieve_patient(auth_headers):
    """Test creating and retrieving a patient."""
    # Create patient
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-15",
        "gender": "male",
        "phone": "+1234567890"
    }
    
    response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    patient = response.json()
    patient_id = patient["id"]
    
    # Retrieve patient
    response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    retrieved_patient = response.json()
    assert retrieved_patient["email"] == patient_data["email"]
    assert retrieved_patient["first_name"] == patient_data["first_name"]

def test_update_patient(auth_headers):
    """Test updating patient information."""
    # Create patient first
    patient_data = {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane.smith@example.com",
        "date_of_birth": "1985-05-20",
        "gender": "female",
        "phone": "+1234567890"
    }
    
    response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers
    )
    patient_id = response.json()["id"]
    
    # Update patient
    update_data = {"phone": "+9876543210"}
    response = client.put(
        f"/api/v1/patients/{patient_id}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    updated_patient = response.json()
    assert updated_patient["phone"] == "+9876543210"

def test_delete_patient(auth_headers):
    """Test deleting a patient."""
    # Create patient
    patient_data = {
        "first_name": "Test",
        "last_name": "Delete",
        "email": "test.delete@example.com",
        "date_of_birth": "1995-03-10",
        "gender": "other",
        "phone": "+1234567890"
    }
    
    response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers
    )
    patient_id = response.json()["id"]
    
    # Delete patient
    response = client.delete(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 204
    
    # Verify deletion
    response = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404
```

#### Testing Database Operations

```python
# tests/test_database.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.patient import Patient

@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()

def test_patient_crud_operations(db_session):
    """Test CRUD operations on patient model."""
    # Create
    patient = Patient(
        first_name="Test",
        last_name="Patient",
        date_of_birth="1990-01-01",
        gender="male",
        phone="+1234567890"
    )
    db_session.add(patient)
    db_session.commit()
    
    # Read
    retrieved = db_session.query(Patient).filter_by(
        first_name="Test"
    ).first()
    assert retrieved is not None
    assert retrieved.last_name == "Patient"
    
    # Update
    retrieved.phone = "+9876543210"
    db_session.commit()
    
    updated = db_session.query(Patient).filter_by(
        first_name="Test"
    ).first()
    assert updated.phone == "+9876543210"
    
    # Delete
    db_session.delete(updated)
    db_session.commit()
    
    deleted = db_session.query(Patient).filter_by(
        first_name="Test"
    ).first()
    assert deleted is None
```

## Frontend Testing

### Setup

```bash
cd frontend

# Run tests
npm test

# Run with coverage
npm test -- --coverage --watchAll=false

# Run specific test file
npm test -- Header.test.tsx

# Update snapshots
npm test -- -u
```

### Component Tests

```typescript
// frontend/src/components/__tests__/Header.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Header from '../Header';
import { AuthContext } from '../../contexts/AuthContext';

describe('Header Component', () => {
  const mockAuthContext = {
    user: { username: 'testuser', role: 'admin' },
    login: jest.fn(),
    logout: jest.fn(),
  };

  it('renders header with user information', () => {
    render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <Header />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    expect(screen.getByText('testuser')).toBeInTheDocument();
  });

  it('shows logout button when user is authenticated', () => {
    render(
      <BrowserRouter>
        <AuthContext.Provider value={mockAuthContext}>
          <Header />
        </AuthContext.Provider>
      </BrowserRouter>
    );

    const logoutButton = screen.getByRole('button', { name: /logout/i });
    expect(logoutButton).toBeInTheDocument();
  });
});
```

### Hook Tests

```typescript
// frontend/src/__tests__/useApi.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useApi } from '../hooks/useApi';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('useApi Hook', () => {
  it('fetches data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    mockedAxios.get.mockResolvedValue({ data: mockData });

    const { result } = renderHook(() => useApi('/api/test'));

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
      expect(result.current.loading).toBe(false);
      expect(result.current.error).toBe(null);
    });
  });

  it('handles errors correctly', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(() => useApi('/api/test'));

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(result.current.loading).toBe(false);
    });
  });
});
```

## Performance Testing

### Load Testing with Locust

```python
# locustfile.py
from locust import HttpUser, task, between
import random

class KeneyAppUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks."""
        response = self.client.post("/api/v1/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_dashboard(self):
        """Test dashboard endpoint."""
        self.client.get(
            "/api/v1/dashboard/stats",
            headers=self.headers,
            name="/dashboard"
        )
    
    @task(5)
    def list_patients(self):
        """Test patient list endpoint."""
        self.client.get(
            "/api/v1/patients/",
            headers=self.headers,
            name="/patients"
        )
    
    @task(2)
    def view_patient(self):
        """Test individual patient endpoint."""
        patient_id = random.randint(1, 100)
        self.client.get(
            f"/api/v1/patients/{patient_id}",
            headers=self.headers,
            name="/patients/:id"
        )
    
    @task(1)
    def create_patient(self):
        """Test patient creation."""
        self.client.post(
            "/api/v1/patients/",
            headers=self.headers,
            json={
                "first_name": "Load",
                "last_name": "Test",
                "email": f"loadtest{random.randint(1,10000)}@example.com",
                "date_of_birth": "1990-01-01",
                "gender": "male",
                "phone": "+1234567890"
            },
            name="/patients [POST]"
        )
```

Run load test:
```bash
# Install locust
pip install locust

# Run test
locust -f locustfile.py --host=http://localhost:8000

# Access web UI at http://localhost:8089
```

## Security Testing

### SQL Injection Tests

```python
# tests/test_security_sql_injection.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sql_injection_in_patient_search(auth_headers):
    """Test that SQL injection attempts are blocked."""
    # Attempt SQL injection
    malicious_input = "'; DROP TABLE patients; --"
    
    response = client.get(
        f"/api/v1/patients/?search={malicious_input}",
        headers=auth_headers
    )
    
    # Should not cause an error or return unusual data
    assert response.status_code in [200, 400]
    
    # Verify tables still exist
    response = client.get("/api/v1/patients/", headers=auth_headers)
    assert response.status_code == 200
```

### XSS Tests

```python
def test_xss_in_patient_name(auth_headers):
    """Test that XSS attempts are sanitized."""
    xss_payload = "<script>alert('xss')</script>"
    
    response = client.post("/api/v1/patients/", json={
        "first_name": xss_payload,
        "last_name": "Test",
        "email": "test@example.com",
        "date_of_birth": "1990-01-01",
        "gender": "male",
        "phone": "+1234567890"
    }, headers=auth_headers)
    
    # Should be rejected or sanitized
    if response.status_code == 201:
        patient = response.json()
        # Verify the payload is sanitized
        assert "<script>" not in patient["first_name"]
```

## Test Coverage

### Measuring Coverage

```bash
# Backend coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# Frontend coverage  
npm test -- --coverage --watchAll=false

# View HTML reports
# Backend: open htmlcov/index.html
# Frontend: open frontend/coverage/lcov-report/index.html
```

### Coverage Goals
- **Overall**: > 80%
- **Critical paths**: > 95%
- **New code**: 100%

## CI/CD Integration

Tests run automatically on:
- Every push to main/develop
- Every pull request
- Nightly builds

See `.github/workflows/ci.yml` for configuration.

## Best Practices

### 1. AAA Pattern (Arrange-Act-Assert)

```python
def test_create_patient():
    # Arrange
    patient_data = {"first_name": "John", ...}
    
    # Act
    response = client.post("/patients/", json=patient_data)
    
    # Assert
    assert response.status_code == 201
```

### 2. Use Fixtures for Common Setup

```python
@pytest.fixture
def sample_patient():
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        ...
    }

def test_something(sample_patient):
    # Use sample_patient
    pass
```

### 3. Test Edge Cases

```python
def test_patient_creation_with_invalid_email():
    """Test validation of invalid email."""
    response = client.post("/patients/", json={
        "email": "not-an-email",
        ...
    })
    assert response.status_code == 422

def test_patient_creation_with_missing_fields():
    """Test handling of missing required fields."""
    response = client.post("/patients/", json={})
    assert response.status_code == 422
```

### 4. Use Descriptive Test Names

```python
# Bad
def test_1():
    pass

# Good
def test_patient_creation_fails_with_duplicate_email():
    pass
```

### 5. Keep Tests Independent

```python
# Bad - Tests depend on each other
def test_create():
    global patient_id
    patient_id = create_patient()

def test_update():
    update_patient(patient_id)  # Depends on test_create

# Good - Each test is independent
def test_create():
    patient_id = create_patient()
    assert patient_id is not None

def test_update():
    patient_id = create_patient()  # Create own test data
    result = update_patient(patient_id)
    assert result.success
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Locust Documentation](https://docs.locust.io/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

## Conclusion

Comprehensive testing ensures the reliability, security, and performance of KeneyApp. Follow these guidelines to maintain high code quality and catch issues before they reach production.
