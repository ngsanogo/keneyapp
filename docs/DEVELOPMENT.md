# Development Guide

This guide provides detailed information for developers working on KeneyApp.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Development Workflow](#development-workflow)
- [Code Organization](#code-organization)
- [API Development](#api-development)
- [Frontend Development](#frontend-development)
- [Database Management](#database-management)
- [Testing Strategy](#testing-strategy)
- [Debugging](#debugging)
- [Performance Optimization](#performance-optimization)

## Getting Started

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/ISData-consulting/keneyapp.git
cd keneyapp

# Full setup (install dependencies + hooks + config)
make setup

# Start development environment
make docker-up
```

### Manual Setup

If you prefer manual setup without Docker:

```bash
# Backend setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Create and configure .env
cp .env.example .env
# Edit .env with your settings

# Setup database
createdb keneyapp
alembic upgrade head
python scripts/init_db.py

# Frontend setup
cd frontend
npm install
```

## Architecture Overview

KeneyApp follows a **Clean Architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│                  Frontend Layer                  │
│         (React + TypeScript + Axios)             │
└──────────────────┬──────────────────────────────┘
                   │ HTTP/REST API
┌──────────────────┴──────────────────────────────┐
│              API Layer (FastAPI)                 │
│  ┌──────────────────────────────────────────┐   │
│  │     Routers (endpoints)                  │   │
│  │  - auth.py, patients.py, etc.            │   │
│  └────────────┬─────────────────────────────┘   │
│               │                                  │
│  ┌────────────┴─────────────────────────────┐   │
│  │     Business Logic (Services)            │   │
│  │  - Authentication, Encryption            │   │
│  │  - FHIR, GraphQL, Audit                  │   │
│  └────────────┬─────────────────────────────┘   │
│               │                                  │
│  ┌────────────┴─────────────────────────────┐   │
│  │     Data Access (Models)                 │   │
│  │  - SQLAlchemy ORM Models                 │   │
│  └────────────┬─────────────────────────────┘   │
└───────────────┼──────────────────────────────────┘
                │
┌───────────────┴──────────────────────────────────┐
│           Database Layer (PostgreSQL)             │
└───────────────────────────────────────────────────┘
```

### Key Components

#### Backend (FastAPI)

- **`app/main.py`**: Application entry point, middleware setup
- **`app/core/`**: Core functionality (config, security, database)
- **`app/models/`**: SQLAlchemy database models
- **`app/schemas/`**: Pydantic validation schemas
- **`app/routers/`**: API endpoint handlers
- **`app/services/`**: Business logic and utilities
- **`app/tasks.py`**: Celery background tasks

#### Frontend (React + TypeScript)

- **`frontend/src/App.tsx`**: Main application component
- **`frontend/src/pages/`**: Page-level components
- **`frontend/src/components/`**: Reusable UI components
- **`frontend/src/contexts/`**: React context providers

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow our [coding standards](../CONTRIBUTING.md#coding-standards).

### 3. Run Quality Checks

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Run security checks
make security
```

### 4. Commit Changes

Use [conventional commits](../CONTRIBUTING.md#commit-message-convention):

```bash
git commit -m "feat(patients): add search by date of birth"
```

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Organization

### Backend Structure

```
app/
├── core/               # Core configuration
│   ├── config.py      # Application settings
│   ├── security.py    # Authentication & encryption
│   └── database.py    # Database connection
├── models/            # Database models
│   ├── user.py
│   ├── patient.py
│   ├── appointment.py
│   └── ...
├── schemas/           # Pydantic schemas
│   ├── user.py
│   ├── patient.py
│   └── ...
├── routers/           # API endpoints
│   ├── auth.py
│   ├── patients.py
│   └── ...
├── services/          # Business logic
│   ├── encryption.py
│   ├── audit.py
│   └── ...
└── main.py           # App entry point
```

### Frontend Structure

```
frontend/src/
├── components/        # Reusable components
│   ├── Header.tsx
│   ├── PatientForm.tsx
│   └── ...
├── pages/            # Page components
│   ├── LoginPage.tsx
│   ├── DashboardPage.tsx
│   └── ...
├── contexts/         # React contexts
│   └── AuthContext.tsx
├── utils/            # Utility functions
└── App.tsx          # Main component
```

## API Development

### Creating a New Endpoint

1. **Define the schema** (`app/schemas/`)

```python
# schemas/patient.py
from pydantic import BaseModel
from datetime import date

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    email: str
```

2. **Create the model** (if needed, `app/models/`)

```python
# models/patient.py
from sqlalchemy import Column, Integer, String, Date
from app.core.database import Base

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    email = Column(String, unique=True, nullable=False)
```

3. **Add the endpoint** (`app/routers/`)

```python
# routers/patients.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.patient import PatientCreate
from app.models.patient import Patient

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])

@router.post("/", response_model=PatientResponse)
def create_patient(
    patient: PatientCreate,
    db: Session = Depends(get_db)
):
    """Create a new patient."""
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient
```

4. **Add tests** (`tests/`)

```python
# tests/test_patients.py
def test_create_patient(client):
    response = client.post(
        "/api/v1/patients/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "email": "john@example.com"
        }
    )
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"
```

## Frontend Development

### Creating a New Component

```typescript
// components/PatientCard.tsx
import React from 'react';

interface PatientCardProps {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
}

const PatientCard: React.FC<PatientCardProps> = ({
  firstName,
  lastName,
  dateOfBirth
}) => {
  return (
    <div className="patient-card">
      <h3>{firstName} {lastName}</h3>
      <p>DOB: {dateOfBirth}</p>
    </div>
  );
};

export default PatientCard;
```

### Making API Calls

```typescript
// Using axios in a component
import axios from 'axios';
import { useEffect, useState } from 'react';

const PatientList: React.FC = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await axios.get('/api/v1/patients/');
        setPatients(response.data);
      } catch (error) {
        console.error('Error fetching patients:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, []);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      {patients.map(patient => (
        <PatientCard key={patient.id} {...patient} />
      ))}
    </div>
  );
};
```

## Database Management

### Creating Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add patient table"

# Review the generated migration in alembic/versions/

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Best Practices

- Always review auto-generated migrations
- Include both upgrade and downgrade operations
- Test migrations on a copy of production data
- Keep migrations small and focused

### Multi-tenant Seeding

- The `scripts/init_db.py` helper provisions a **default tenant (`slug=default`)** before inserting any sample data. This keeps the seed data aligned with the multi-tenant schema enforced by recent migrations.
- When adding new fixtures, remember to set `tenant_id` on every model instance (users, patients, appointments, prescriptions, etc.). Failing to do so will trigger NOT NULL violations once migrations have run.
- You can re-run the seed script safely; it is idempotent and will skip inserting duplicates after the first run.
- In containerised environments (`./scripts/start_stack.sh` or the CI docker smoke job), the backend container executes `alembic upgrade head` followed by `python -m scripts.init_db` automatically. Manual invocations should follow the same order.

## Testing Strategy

### Backend Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_patients.py::test_create_patient -v
```

### Test Structure

```python
# tests/test_patients.py
import pytest
from fastapi.testclient import TestClient

def test_create_patient(client: TestClient):
    # Arrange
    patient_data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01"
    }
    
    # Act
    response = client.post("/api/v1/patients/", json=patient_data)
    
    # Assert
    assert response.status_code == 201
    assert response.json()["first_name"] == "John"
```

### Frontend Testing

```bash
cd frontend
npm test
```

```typescript
// PatientCard.test.tsx
import { render, screen } from '@testing-library/react';
import PatientCard from './PatientCard';

test('renders patient information', () => {
  render(
    <PatientCard 
      firstName="John"
      lastName="Doe"
      dateOfBirth="1990-01-01"
    />
  );
  
  expect(screen.getByText('John Doe')).toBeInTheDocument();
  expect(screen.getByText('DOB: 1990-01-01')).toBeInTheDocument();
});
```

## Debugging

### Backend Debugging

**Using print statements:**
```python
print(f"Patient data: {patient}")
```

**Using Python debugger:**
```python
import pdb; pdb.set_trace()
```

**Using VS Code debugger:**
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

### Frontend Debugging

**Using browser DevTools:**
- Open Chrome/Firefox DevTools
- Use React DevTools extension
- Check Network tab for API calls
- Use Console for logging

**React component debugging:**
```typescript
console.log('Component props:', props);
console.log('Component state:', state);
```

## Performance Optimization

### Backend Optimization

**Database queries:**
```python
# Bad - N+1 query problem
patients = db.query(Patient).all()
for patient in patients:
    appointments = patient.appointments  # Separate query per patient

# Good - Eager loading
patients = db.query(Patient).options(
    joinedload(Patient.appointments)
).all()
```

**Caching with Redis:**
```python
from redis import Redis

redis_client = Redis(host='localhost', port=6379)

# Cache expensive operations
cache_key = f"patient:{patient_id}"
cached_data = redis_client.get(cache_key)

if cached_data:
    return json.loads(cached_data)

data = fetch_patient_data(patient_id)
redis_client.setex(cache_key, 3600, json.dumps(data))
return data
```

### Frontend Optimization

**Code splitting:**
```typescript
// Lazy load components
const Dashboard = React.lazy(() => import('./pages/DashboardPage'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

**Memoization:**
```typescript
import { useMemo } from 'react';

const ExpensiveComponent = ({ data }) => {
  const processedData = useMemo(() => {
    return expensiveOperation(data);
  }, [data]);
  
  return <div>{processedData}</div>;
};
```

## Useful Commands

### Development

```bash
make dev          # Start dev servers
make format       # Format code
make lint         # Run linters
make test         # Run tests
make test-cov     # Run tests with coverage
```

### Docker

```bash
make docker-up    # Start all services
make docker-down  # Stop all services
make docker-logs  # View logs
```

### Database

```bash
make db-migrate   # Run migrations
make db-init      # Initialize with sample data
make db-reset     # Reset database
```

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## Getting Help

- Check the [README](../README.md) for basic information
- Read [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines
- Create an issue on GitHub
- Contact: contact@isdataconsulting.com
