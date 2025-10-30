# Testing Guide

Comprehensive guide for testing KeneyApp.

## Table of Contents

- [Testing Philosophy](#testing-philosophy)
- [Test Structure](#test-structure)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Integration Testing](#integration-testing)
- [E2E Testing](#e2e-testing)
- [Test Coverage](#test-coverage)
- [Continuous Testing](#continuous-testing)
- [Best Practices](#best-practices)

## Testing Philosophy

Our testing approach follows the **Testing Pyramid**:

```
           /\
          /  \  E2E Tests (Few)
         /____\
        /      \
       / Integ. \ Integration Tests (Some)
      /__________\
     /            \
    /    Unit      \ Unit Tests (Many)
   /________________\
```

- **Unit Tests (70%)**: Fast, isolated tests for individual functions
- **Integration Tests (20%)**: Test interactions between components
- **E2E Tests (10%)**: Full system tests from user perspective

## Test Structure

### Backend Tests

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_api.py             # API endpoint tests
├── test_auth.py            # Authentication tests
├── test_models.py          # Database model tests
├── test_services.py        # Business logic tests
├── test_encryption.py      # Encryption tests
├── test_fhir.py           # FHIR integration tests
└── test_graphql.py        # GraphQL tests
```

### Frontend Tests

```
frontend/src/
├── components/
│   ├── Header.tsx
│   └── Header.test.tsx
├── pages/
│   ├── LoginPage.tsx
│   └── LoginPage.test.tsx
└── utils/
    ├── auth.ts
    └── auth.test.ts
```

## Backend Testing

### Setup

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov httpx

# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Watch mode (requires pytest-watch)
ptw
```

### Unit Tests

Test individual functions in isolation:

```python
# tests/test_services.py
import pytest
from app.services.encryption import encrypt_data, decrypt_data

def test_encrypt_decrypt():
    """Test data encryption and decryption."""
    # Arrange
    original_data = "Sensitive patient information"
    
    # Act
    encrypted = encrypt_data(original_data)
    decrypted = decrypt_data(encrypted)
    
    # Assert
    assert decrypted == original_data
    assert encrypted != original_data
```

### API Tests

Test API endpoints with TestClient:

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_patient():
    """Test patient creation endpoint."""
    # Arrange
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "email": "john.doe@example.com"
    }
    
    # Act
    response = client.post("/api/v1/patients/", json=patient_data)
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["last_name"] == "Doe"
    assert "id" in data


def test_get_patients_requires_auth():
    """Test that getting patients requires authentication."""
    # Act
    response = client.get("/api/v1/patients/")
    
    # Assert
    assert response.status_code == 401
```

### Database Tests

Test database models and queries:

```python
# tests/test_models.py
import pytest
from sqlalchemy.orm import Session
from app.models.patient import Patient
from app.core.database import get_db

@pytest.fixture
def db_session():
    """Create a test database session."""
    # Setup test database
    db = next(get_db())
    yield db
    # Cleanup
    db.rollback()
    db.close()


def test_create_patient_model(db_session: Session):
    """Test creating a patient in the database."""
    # Arrange
    patient = Patient(
        first_name="Jane",
        last_name="Smith",
        date_of_birth="1985-05-15",
        email="jane.smith@example.com"
    )
    
    # Act
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    
    # Assert
    assert patient.id is not None
    assert patient.first_name == "Jane"
    
    # Verify in database
    retrieved = db_session.query(Patient).filter_by(id=patient.id).first()
    assert retrieved is not None
    assert retrieved.email == "jane.smith@example.com"
```

### Async Tests

Test asynchronous code:

```python
# tests/test_async.py
import pytest
from app.services.email import send_appointment_reminder

@pytest.mark.asyncio
async def test_send_appointment_reminder():
    """Test sending appointment reminders."""
    # Arrange
    appointment_id = 1
    
    # Act
    result = await send_appointment_reminder(appointment_id)
    
    # Assert
    assert result is True
```

### Fixtures

Use fixtures for reusable test data:

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_token(client):
    """Get authentication token for tests."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}
```

## Frontend Testing

### Setup

```bash
cd frontend

# Install test dependencies (already included)
npm install

# Run tests
npm test

# With coverage
npm test -- --coverage

# Watch mode (default)
npm test
```

### Component Tests

Test React components:

```typescript
// components/PatientCard.test.tsx
import { render, screen } from '@testing-library/react';
import PatientCard from './PatientCard';

describe('PatientCard', () => {
  it('renders patient information', () => {
    // Arrange
    const patient = {
      id: 1,
      firstName: 'John',
      lastName: 'Doe',
      dateOfBirth: '1990-01-01',
      email: 'john@example.com'
    };
    
    // Act
    render(<PatientCard patient={patient} />);
    
    // Assert
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('calls onClick handler when clicked', () => {
    // Arrange
    const mockOnClick = jest.fn();
    const patient = {
      id: 1,
      firstName: 'John',
      lastName: 'Doe',
      dateOfBirth: '1990-01-01',
      email: 'john@example.com'
    };
    
    // Act
    render(<PatientCard patient={patient} onClick={mockOnClick} />);
    const card = screen.getByRole('button');
    card.click();
    
    // Assert
    expect(mockOnClick).toHaveBeenCalledWith(patient);
  });
});
```

### User Interaction Tests

Test user interactions:

```typescript
// pages/LoginPage.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import LoginPage from './LoginPage';

describe('LoginPage', () => {
  it('allows user to login', async () => {
    // Arrange
    render(<LoginPage />);
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });
    
    // Act
    await userEvent.type(usernameInput, 'admin');
    await userEvent.type(passwordInput, 'admin123');
    fireEvent.click(submitButton);
    
    // Assert
    await waitFor(() => {
      expect(screen.getByText(/welcome/i)).toBeInTheDocument();
    });
  });

  it('shows error on invalid credentials', async () => {
    // Arrange
    render(<LoginPage />);
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    const submitButton = screen.getByRole('button', { name: /login/i });
    
    // Act
    await userEvent.type(usernameInput, 'invalid');
    await userEvent.type(passwordInput, 'wrong');
    fireEvent.click(submitButton);
    
    // Assert
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
  });
});
```

### Mocking API Calls

Mock axios requests:

```typescript
// utils/api.test.ts
import axios from 'axios';
import { fetchPatients } from './api';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('API Utils', () => {
  it('fetches patients successfully', async () => {
    // Arrange
    const mockPatients = [
      { id: 1, firstName: 'John', lastName: 'Doe' },
      { id: 2, firstName: 'Jane', lastName: 'Smith' }
    ];
    mockedAxios.get.mockResolvedValue({ data: mockPatients });
    
    // Act
    const patients = await fetchPatients();
    
    // Assert
    expect(patients).toEqual(mockPatients);
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/v1/patients/');
  });

  it('handles errors gracefully', async () => {
    // Arrange
    mockedAxios.get.mockRejectedValue(new Error('Network error'));
    
    // Act & Assert
    await expect(fetchPatients()).rejects.toThrow('Network error');
  });
});
```

## Integration Testing

Test multiple components working together:

```python
# tests/test_integration.py
def test_patient_appointment_workflow(client, auth_headers):
    """Test complete patient and appointment creation workflow."""
    # 1. Create patient
    patient_response = client.post(
        "/api/v1/patients/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "email": "john@example.com"
        },
        headers=auth_headers
    )
    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]
    
    # 2. Create appointment
    appointment_response = client.post(
        "/api/v1/appointments/",
        json={
            "patient_id": patient_id,
            "doctor_id": 1,
            "appointment_date": "2024-02-01T10:00:00",
            "reason": "Annual checkup"
        },
        headers=auth_headers
    )
    assert appointment_response.status_code == 201
    appointment_id = appointment_response.json()["id"]
    
    # 3. Get patient with appointments
    patient_detail = client.get(
        f"/api/v1/patients/{patient_id}",
        headers=auth_headers
    )
    assert patient_detail.status_code == 200
    
    # 4. Verify appointment is linked
    appointments = client.get(
        f"/api/v1/appointments/?patient_id={patient_id}",
        headers=auth_headers
    )
    assert len(appointments.json()) == 1
```

## E2E Testing

End-to-end tests using Playwright or Selenium:

```python
# tests/e2e/test_patient_flow.py
from playwright.sync_api import sync_playwright

def test_create_patient_e2e():
    """Test creating a patient through the UI."""
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Login
        page.goto("http://localhost:3000/login")
        page.fill('input[name="username"]', 'admin')
        page.fill('input[name="password"]', 'admin123')
        page.click('button[type="submit"]')
        
        # Navigate to patients
        page.wait_for_url("**/dashboard")
        page.click('text=Patients')
        
        # Create new patient
        page.click('text=Add Patient')
        page.fill('input[name="firstName"]', 'John')
        page.fill('input[name="lastName"]', 'Doe')
        page.fill('input[name="dateOfBirth"]', '1990-01-01')
        page.fill('input[name="email"]', 'john@example.com')
        page.click('button:has-text("Save")')
        
        # Verify patient was created
        page.wait_for_selector('text=Patient created successfully')
        assert page.is_visible('text=John Doe')
        
        browser.close()
```

## Test Coverage

### Measure Coverage

```bash
# Backend
pytest --cov=app --cov-report=html --cov-report=term
open htmlcov/index.html

# Frontend
cd frontend
npm test -- --coverage
open coverage/lcov-report/index.html
```

### Coverage Goals

- **Overall**: Minimum 80% coverage
- **Critical paths**: 90%+ coverage
- **New code**: 100% coverage

### Coverage Report Example

```
Name                    Stmts   Miss  Cover
-------------------------------------------
app/__init__.py            12      0   100%
app/main.py               45      2    96%
app/core/security.py      67      5    93%
app/models/patient.py     89      8    91%
app/routers/patients.py  123     15    88%
-------------------------------------------
TOTAL                    336     30    91%
```

## Continuous Testing

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Runs automatically on commit
git commit -m "feat: add new feature"

# Run manually
pre-commit run --all-files
```

### CI/CD Integration

Tests run automatically on every push and PR:

```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: |
    pytest --cov=app --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Best Practices

### 1. AAA Pattern

Structure tests with Arrange, Act, Assert:

```python
def test_example():
    # Arrange - Setup test data
    data = {"key": "value"}
    
    # Act - Execute the function
    result = process_data(data)
    
    # Assert - Verify the result
    assert result == expected_value
```

### 2. Descriptive Names

Use clear, descriptive test names:

```python
# Good
def test_create_patient_with_valid_email_succeeds():
    pass

# Bad
def test_1():
    pass
```

### 3. One Assertion Per Test

Focus each test on one behavior:

```python
# Good - separate tests
def test_patient_creation_returns_201():
    response = create_patient(data)
    assert response.status_code == 201

def test_patient_creation_returns_patient_data():
    response = create_patient(data)
    assert response.json()["first_name"] == "John"

# Avoid - multiple assertions
def test_patient_creation():
    response = create_patient(data)
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"
    assert response.json()["email"] == "john@example.com"
```

### 4. Test Independence

Each test should be independent:

```python
# Good
def test_a():
    db = setup_test_db()
    # test logic
    cleanup_test_db(db)

def test_b():
    db = setup_test_db()
    # test logic
    cleanup_test_db(db)

# Bad - test_b depends on test_a
def test_a():
    global_db.create_patient("John")

def test_b():
    assert global_db.get_patient("John") is not None
```

### 5. Use Factories

Use test data factories for complex objects:

```python
# tests/factories.py
def patient_factory(**kwargs):
    """Create a test patient with default values."""
    defaults = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "email": "john@example.com"
    }
    defaults.update(kwargs)
    return defaults

# Usage
def test_create_patient():
    patient_data = patient_factory(first_name="Jane")
    response = client.post("/api/v1/patients/", json=patient_data)
    assert response.status_code == 201
```

## Troubleshooting

### Tests Failing Locally

```bash
# Check test database
echo $DATABASE_URL

# Clear cache
pytest --cache-clear

# Verbose output
pytest -vv

# Run specific test
pytest tests/test_api.py::test_create_patient -v
```

### Slow Tests

```bash
# Profile tests
pytest --durations=10

# Run in parallel
pytest -n auto
```

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Documentation](https://jestjs.io/)
- [Playwright Documentation](https://playwright.dev/)

---

For questions: contact@isdataconsulting.com
