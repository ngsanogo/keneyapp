# Contributing to KeneyApp

Thank you for your interest in contributing to KeneyApp! This document provides guidelines and instructions for contributing to the project.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Message Convention](#commit-message-convention)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)

## 📜 Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** for backend development
- **Node.js 18+** for frontend development
- **PostgreSQL 15+** for database
- **Redis 7+** for caching and task queue
- **Docker & Docker Compose** (recommended for local development)

### Setting Up Development Environment

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/keneyapp.git
   cd keneyapp
   ```

2. **Install pre-commit hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

3. **Start development environment**
   ```bash
   # Using Docker Compose (recommended)
   ./scripts/start_stack.sh

   # Or manual setup - see README.md
   ```

## 🔄 Development Workflow

### Branch Strategy

We follow **Git Flow** branching model:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features (branch from `develop`)
- `bugfix/*` - Bug fixes (branch from `develop`)
- `hotfix/*` - Urgent production fixes (branch from `main`)
- `release/*` - Release preparation (branch from `develop`)

### Creating a Feature Branch

```bash
# Ensure you're on develop and it's up to date
git checkout develop
git pull origin develop

# Create your feature branch
git checkout -b feature/your-feature-name
```

## 📝 Coding Standards

### Python (Backend)

- **Style Guide**: Follow [PEP 8](https://pep8.org/)
- **Formatter**: Use **Black** (line length: 88)
- **Linter**: Use **Flake8** with Black-compatible settings
- **Type Hints**: Use type hints for function parameters and return values
- **Imports**: Sort with **isort** (Black profile)

```python
# Good example
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

def get_patients(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Patient]:
    """Retrieve a list of patients with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of patient objects
    """
    return db.query(Patient).offset(skip).limit(limit).all()
```

**Run linting and formatting:**
```bash
# Format code
black app tests

# Check linting
flake8 app tests

# Sort imports
isort app tests

# Type checking
mypy app
```

### JavaScript/TypeScript (Frontend)

- **Style Guide**: Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- **Formatter**: Use **Prettier**
- **Linter**: Use **ESLint** with TypeScript support
- **TypeScript**: Use strict mode, provide type annotations

```typescript
// Good example
interface Patient {
  id: number;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
}

const fetchPatients = async (limit: number = 100): Promise<Patient[]> => {
  try {
    const response = await axios.get('/api/v1/patients', {
      params: { limit },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching patients:', error);
    throw error;
  }
};
```

**Run linting and formatting:**
```bash
cd frontend

# Format code
npm run format

# Check formatting
npm run format:check

# Lint code
npm run lint
```

### General Guidelines

- **Naming Conventions**:
  - Use descriptive variable and function names
  - Classes: `PascalCase` (e.g., `PatientService`)
  - Functions/Variables: `camelCase` (e.g., `getUserById`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RETRY_ATTEMPTS`)
  - Files: `snake_case` for Python, `PascalCase` for React components

- **Code Comments**:
  - Write self-documenting code when possible
  - Add comments to explain **why**, not **what**
  - Document complex algorithms or business logic
  - Use docstrings for Python functions and classes
  - Use JSDoc for TypeScript functions

- **Module Organization**:
  - Keep files focused and single-purpose
  - Maximum file length: ~300-400 lines
  - Group related functionality together
  - Use clear folder structure

## 🧪 Testing Guidelines

### Backend Testing

- Write tests for all new features and bug fixes
- Aim for **>80% code coverage**
- Use **pytest** for backend tests
- Follow AAA pattern: Arrange, Act, Assert

```python
# Example test
import pytest
from fastapi.testclient import TestClient

def test_create_patient(client: TestClient, db_session):
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

**Run tests:**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_patients.py -v
```

### Frontend Testing

- Write tests for all React components
- Use **Jest** and **React Testing Library**
- Test user interactions, not implementation details

```typescript
// Example test
import { render, screen, fireEvent } from '@testing-library/react';
import PatientList from './PatientList';

test('displays patient list', async () => {
  render(<PatientList />);
  
  const patientName = await screen.findByText('John Doe');
  expect(patientName).toBeInTheDocument();
});
```

**Run tests:**
```bash
cd frontend

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage
```

## 📋 Commit Message Convention

We follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring without changing functionality
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates
- `perf`: Performance improvements
- `ci`: CI/CD changes
- `build`: Build system changes

### Examples

```bash
# Feature
git commit -m "feat(patients): add search functionality"

# Bug fix
git commit -m "fix(auth): correct token expiration validation"

# Documentation
git commit -m "docs(api): update authentication endpoints"

# With body
git commit -m "feat(appointments): add reminder notifications

Implemented email and SMS reminders for upcoming appointments.
Reminders are sent 24 hours before the scheduled time.

Closes #123"
```

## 🔀 Pull Request Process

### Before Creating a PR

1. **Ensure your code is up to date**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout your-feature-branch
   git rebase develop
   ```

2. **Run all checks locally**
   ```bash
   # Backend
   black app tests
   flake8 app tests
   pytest --cov=app

   # Frontend
   cd frontend
   npm run format
   npm run lint
   npm test -- --watchAll=false
   ```

3. **Update documentation** if needed

4. **Add/update tests** for your changes

### Creating the PR

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request** on GitHub
   - Use a descriptive title following commit conventions
   - Fill out the PR template completely
   - Link related issues using `Closes #issue-number`
   - Add appropriate labels
   - Request reviewers

### PR Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe the tests you added or ran

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] No new warnings
```

## 👀 Code Review Guidelines

### For Reviewers

- **Be respectful and constructive**
- **Review promptly** (within 24-48 hours)
- **Test the changes** when possible
- **Check for**:
  - Code quality and style
  - Test coverage
  - Documentation
  - Security vulnerabilities
  - Performance implications
  - Breaking changes

### Review Checklist

- [ ] Code is clean and readable
- [ ] Follows project conventions
- [ ] Tests are adequate
- [ ] No hardcoded credentials or secrets
- [ ] Error handling is appropriate
- [ ] Performance is acceptable
- [ ] Documentation is updated
- [ ] No unnecessary dependencies added

### For Authors

- **Respond to feedback promptly**
- **Be open to suggestions**
- **Explain your decisions** when needed
- **Update the PR** based on feedback
- **Request re-review** after changes

## 🔒 Security Guidelines

- **Never commit secrets** (API keys, passwords, tokens)
- Use **environment variables** for sensitive data
- **Validate all user inputs**
- Follow **OWASP** security best practices
- Run `npm audit` and `pip-audit` regularly
- Report security vulnerabilities privately to contact@isdataconsulting.com

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Don%27t_Do_This)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)

## 🙋 Questions?

If you have questions or need help:

1. Check existing [documentation](docs/)
2. Search [existing issues](https://github.com/ISData-consulting/keneyapp/issues)
3. Create a new issue with the `question` label
4. Contact: contact@isdataconsulting.com

## 🎉 Thank You!

Thank you for contributing to KeneyApp! Your efforts help make healthcare data management better for everyone.
