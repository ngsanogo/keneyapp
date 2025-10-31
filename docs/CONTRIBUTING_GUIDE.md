# Contributing to KeneyApp

Thank you for your interest in contributing to KeneyApp! This document provides guidelines and instructions for contributing to the project.

## Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Coding Standards](#coding-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Commit Message Convention](#commit-message-convention)
7. [Pull Request Process](#pull-request-process)
8. [Issue Reporting](#issue-reporting)

## Code of Conduct

Please read and follow our [Code of Conduct](../CODE_OF_CONDUCT.md).

## Getting Started

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/keneyapp.git
cd keneyapp

# Add upstream remote
git remote add upstream https://github.com/ISData-consulting/keneyapp.git
```

### 2. Set Up Development Environment

```bash
# Backend setup
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install pre-commit hooks (must be done after activating virtual environment)
pip install pre-commit
pre-commit install

# Frontend setup
cd frontend
npm install
cd ..
```

### 3. Configure Environment

```bash
# Copy environment example
cp .env.example .env

# Update with your local settings
nano .env
```

### 4. Initialize Database

```bash
# Start PostgreSQL (via Docker or locally)
docker-compose up -d db

# Run migrations
alembic upgrade head

# Initialize with sample data (optional)
python scripts/init_db.py
```

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### Branch Naming Convention
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions or modifications
- `chore/` - Maintenance tasks

### 2. Make Your Changes

```bash
# Edit files
# Write tests
# Update documentation

# Run tests frequently
pytest tests/

# Check code style
black app tests
flake8 app tests
```

### 3. Test Your Changes

```bash
# Backend tests
pytest tests/ -v --cov=app

# Frontend tests
cd frontend
npm test
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "feat: add patient search functionality"
```

See [Commit Message Convention](#commit-message-convention) below.

### 5. Keep Your Branch Updated

```bash
# Fetch latest changes from upstream
git fetch upstream

# Rebase your branch
git rebase upstream/main

# Or merge if you prefer
git merge upstream/main
```

### 6. Push and Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

## Coding Standards

### Python (Backend)

#### Style Guide
We follow [PEP 8](https://pep8.org/) with some modifications:
- Line length: 88 characters (Black default)
- Use Black for formatting
- Use type hints where appropriate

```python
from typing import List, Optional
from datetime import datetime

def get_patients(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None
) -> List[Patient]:
    """
    Retrieve patients from database.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        
    Returns:
        List of Patient objects
    """
    query = db.query(Patient)
    if status:
        query = query.filter(Patient.status == status)
    return query.offset(skip).limit(limit).all()
```

#### Code Organization
```
app/
├── core/           # Core configuration and utilities
├── models/         # Database models
├── schemas/        # Pydantic schemas
├── routers/        # API endpoints
├── services/       # Business logic
└── tests/          # Test files
```

#### Best Practices
- Use meaningful variable names
- Write docstrings for functions and classes
- Keep functions small and focused (< 50 lines)
- Use dependency injection for database sessions
- Handle errors gracefully with proper HTTP status codes
- Log important events (avoid logging sensitive data)

### TypeScript/React (Frontend)

#### Style Guide
- Use TypeScript for type safety
- Follow [Airbnb React Style Guide](https://airbnb.io/javascript/react/)
- Use functional components with hooks
- Use Prettier for formatting

```typescript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Patient {
  id: number;
  firstName: string;
  lastName: string;
  email: string;
}

interface PatientsListProps {
  status?: string;
}

const PatientsList: React.FC<PatientsListProps> = ({ status }) => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await axios.get<Patient[]>('/api/v1/patients/', {
          params: { status },
        });
        setPatients(response.data);
      } catch (err) {
        setError('Failed to fetch patients');
      } finally {
        setLoading(false);
      }
    };

    fetchPatients();
  }, [status]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="patients-list">
      {patients.map((patient) => (
        <PatientCard key={patient.id} patient={patient} />
      ))}
    </div>
  );
};

export default PatientsList;
```

#### Component Structure
```typescript
// 1. Imports
import React from 'react';

// 2. Type definitions
interface Props {
  // ...
}

// 3. Component
const Component: React.FC<Props> = ({ prop1, prop2 }) => {
  // Hooks
  const [state, setState] = useState();

  // Event handlers
  const handleClick = () => {
    // ...
  };

  // Effects
  useEffect(() => {
    // ...
  }, []);

  // Render
  return <div>...</div>;
};

// 4. Export
export default Component;
```

## Testing Guidelines

### Writing Tests

#### Backend Tests
```python
import pytest
from fastapi.testclient import TestClient

def test_create_patient_success(client, auth_headers):
    """Test successful patient creation."""
    response = client.post(
        "/api/v1/patients/",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "date_of_birth": "1990-01-15",
            "gender": "male",
            "phone": "+1234567890"
        },
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "John"
    assert data["email"] == "john@example.com"

def test_create_patient_duplicate_email(client, auth_headers):
    """Test that duplicate email is rejected."""
    patient_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "duplicate@example.com",
        "date_of_birth": "1985-05-20",
        "gender": "female",
        "phone": "+1234567890"
    }
    
    # Create first patient
    response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Attempt to create duplicate
    response = client.post(
        "/api/v1/patients/",
        json=patient_data,
        headers=auth_headers
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()
```

#### Frontend Tests
```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import PatientsList from './PatientsList';
import axios from 'axios';

jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('PatientsList', () => {
  it('displays loading state initially', () => {
    mockedAxios.get.mockResolvedValue({ data: [] });
    
    render(<PatientsList />);
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays patients after loading', async () => {
    const mockPatients = [
      { id: 1, firstName: 'John', lastName: 'Doe', email: 'john@example.com' },
      { id: 2, firstName: 'Jane', lastName: 'Smith', email: 'jane@example.com' },
    ];
    
    mockedAxios.get.mockResolvedValue({ data: mockPatients });
    
    render(<PatientsList />);
    
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('displays error message on failure', async () => {
    mockedAxios.get.mockRejectedValue(new Error('Network error'));
    
    render(<PatientsList />);
    
    await waitFor(() => {
      expect(screen.getByText(/failed to fetch/i)).toBeInTheDocument();
    });
  });
});
```

### Test Coverage Requirements
- Minimum 80% overall coverage
- 100% coverage for new code
- All critical paths must be tested
- Include both happy path and error cases

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples
```bash
feat(patients): add patient search functionality

Implement full-text search for patients by name, email, or phone number.
Includes pagination support and filters for active/inactive status.

Closes #123

---

fix(auth): resolve token expiration issue

Token validation was failing due to timezone comparison.
Now using UTC consistently throughout the application.

Fixes #456

---

docs(api): update authentication documentation

Added examples for OAuth2 authentication flow and improved
explanation of JWT token usage.

---

test(patients): add integration tests for patient CRUD

Added comprehensive test coverage for patient creation, update,
and deletion operations including edge cases and error handling.
```

## Pull Request Process

### Before Submitting

1. **Run all tests**: Ensure all tests pass
2. **Check code style**: Run linters and formatters
3. **Update documentation**: If adding features
4. **Add tests**: For new functionality
5. **Update CHANGELOG**: If making significant changes

### PR Template

When creating a PR, use this template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All existing tests pass
- [ ] New tests added for changes
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests provide adequate coverage

## Screenshots (if applicable)
Add screenshots for UI changes

## Related Issues
Closes #issue_number
```

### Review Process

1. **Automated checks**: CI/CD pipeline runs automatically
2. **Code review**: At least one approval required
3. **Discussion**: Address review comments
4. **Merge**: Maintainer will merge after approval

## Issue Reporting

### Bug Reports

Use this template:

```markdown
**Describe the bug**
A clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What should happen

**Actual behavior**
What actually happens

**Screenshots**
If applicable

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 2.0.0]

**Additional context**
Any other relevant information
```

### Feature Requests

Use this template:

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
What you want to happen

**Describe alternatives you've considered**
Other solutions you've thought about

**Additional context**
Any other relevant information
```

## Questions?

- Check existing [documentation](../README.md)
- Search [existing issues](https://github.com/ISData-consulting/keneyapp/issues)
- Ask in [discussions](https://github.com/ISData-consulting/keneyapp/discussions)
- Email: contact@isdataconsulting.com

## Thank You!

Your contributions make KeneyApp better for everyone. We appreciate your time and effort!
