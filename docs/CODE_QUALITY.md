# Code Quality Standards

This document outlines the code quality standards and tools used in the KeneyApp project.

## Overview

KeneyApp maintains high code quality through:

- Automated linting and formatting
- Type checking with mypy
- Comprehensive test coverage
- Pre-commit hooks
- CI/CD quality gates

## Tools and Configuration

### Python Code Quality

#### Black (Code Formatter)

- **Version:** 24.10.0
- **Line Length:** 88 characters (default)
- **Configuration:** Uses default Black settings
- **Usage:**

  ```bash
  # Format all Python files
  black app tests

  # Check formatting without changing files
  black --check app tests
  ```

#### Flake8 (Linter)

- **Version:** 7.1.1
- **Configuration:** `.flake8`
- **Line Length:** 88 characters (aligned with Black)
- **Ignored Errors:**
  - E203: Whitespace before ':' (Black compatibility)
  - E266: Too many leading '#' for block comment
  - E501: Line too long (handled by Black)
  - W503: Line break before binary operator
- **Max Complexity:** 10 (McCabe)
- **Usage:**

  ```bash
  # Run flake8
  flake8 app

  # Count issues
  flake8 app --count --statistics
  ```

#### mypy (Type Checker)

- **Version:** 1.13.0
- **Configuration:** `mypy.ini`
- **Python Version:** 3.11
- **Strictness:** Gradual adoption
  - Strict checking for `app.core.*` and `app.routers.*`
  - Progressive strictness for other modules
- **Usage:**

  ```bash
  # Run type checking
  mypy app --config-file mypy.ini
  ```

### Frontend Code Quality

#### ESLint (Linter)

- **Configuration:** `frontend/.eslintrc`
- **Extends:** react-app, react-app/jest
- **Usage:**

  ```bash
  cd frontend
  npm run lint
  ```

#### Prettier (Formatter)

- **Configuration:** `frontend/.prettierrc`
- **Usage:**

  ```bash
  cd frontend
  # Format code
  npm run format

  # Check formatting
  npm run format:check
  ```

## Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit.

### Installation

```bash
pip install pre-commit
pre-commit install
```

### Manual Run

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

### Configured Hooks

1. **Black** - Python code formatting
2. **Flake8** - Python linting
3. **isort** - Python import sorting
4. **Prettier** - Frontend code formatting
5. **Standard hooks:**
   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON validation
   - Large file detection
   - Merge conflict detection
   - Private key detection
6. **detect-secrets** - Secret scanning

## CI/CD Quality Gates

### Backend Pipeline

```yaml
# .github/workflows/ci.yml
- Linting (flake8)
- Code formatting check (black --check)
- Type checking (mypy)
- Unit tests with coverage (pytest)
- Security scanning (CodeQL)
- Dependency vulnerability check (pip-audit)
```

### Frontend Pipeline

```yaml
# .github/workflows/ci.yml
- Linting (ESLint)
- Code formatting check (Prettier)
- Unit tests with coverage (Jest)
- Build verification
- Security audit (npm audit)
```

## Code Quality Metrics

### Current Status

- **Test Coverage:** 77% (68 tests passing)
- **Flake8 Issues:** 0 (after configuration)
- **Type Coverage:** Progressive (strict on core modules)
- **Security Vulnerabilities:** Documented in SECURITY_RECOMMENDATIONS.md

### Quality Goals

- [ ] Increase test coverage to 85%
- [ ] Achieve 100% type coverage on core modules
- [ ] Zero critical security vulnerabilities
- [ ] All tests passing on main branch

## Best Practices

### Python

1. **Follow PEP 8** style guide (enforced by Black and Flake8)
2. **Add type hints** to all new functions and methods
3. **Write docstrings** for public functions and classes
4. **Keep functions small** (< 50 lines, complexity < 10)
5. **Use meaningful variable names**
6. **Avoid magic numbers** - use constants

Example:

```python
from typing import Optional
from datetime import datetime, timezone

def calculate_age(birth_date: datetime) -> Optional[int]:
    """
    Calculate age in years from birth date.

    Args:
        birth_date: The person's date of birth

    Returns:
        Age in years, or None if birth_date is in the future
    """
    today = datetime.now(timezone.utc)
    if birth_date > today:
        return None

    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age
```

### TypeScript/React

1. **Use TypeScript** for type safety
2. **Follow React best practices** (hooks, functional components)
3. **Use descriptive component names** (PascalCase)
4. **Keep components small and focused**
5. **Extract reusable logic** into custom hooks
6. **Use proper prop types**

Example:

```typescript
interface PatientCardProps {
  patient: Patient;
  onSelect: (id: number) => void;
}

export const PatientCard: React.FC<PatientCardProps> = ({
  patient,
  onSelect
}) => {
  return (
    <div className="patient-card" onClick={() => onSelect(patient.id)}>
      <h3>{patient.name}</h3>
      <p>{patient.email}</p>
    </div>
  );
};
```

## Testing Standards

### Unit Tests

- Test coverage: Aim for 80%+ on new code
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

### Integration Tests

- Test API endpoints
- Test database interactions
- Test authentication flows

### Test Naming Convention

```python
def test_<function_name>_<scenario>_<expected_result>():
    """Test that <function> returns <result> when <scenario>."""
    # Arrange
    data = create_test_data()

    # Act
    result = function_under_test(data)

    # Assert
    assert result == expected_value
```

## Continuous Improvement

### Regular Reviews

- Weekly code quality metrics review
- Monthly security audit
- Quarterly dependency updates
- Annual tooling review

### Technical Debt

- Track in BACKLOG.md
- Prioritize based on impact and effort
- Address during sprint planning
- Schedule dedicated cleanup sprints

### Metrics to Monitor

1. Test coverage trend
2. Code complexity metrics
3. Build/test execution time
4. Security vulnerability count
5. Code duplication percentage
6. Documentation coverage

## Tools for Local Development

### Recommended IDE Extensions

**VS Code:**

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Flake8 (ms-python.flake8)
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- EditorConfig (editorconfig.editorconfig)

**PyCharm:**

- Enable Black as external tool
- Configure Flake8 as external tool
- Enable mypy plugin
- Configure EditorConfig support

## Troubleshooting

### Common Issues

**Black and Flake8 Conflict:**

- Ensure Flake8 config ignores E203, W503
- Use max-line-length=88 in both tools

**Import Order Issues:**

- Configure isort with `--profile black`
- Run `isort app` to fix import order

**Type Checking Errors:**

- Start with less strict settings
- Gradually increase strictness
- Use `# type: ignore` sparingly

**Pre-commit Hook Failures:**

- Run `pre-commit run --all-files` to fix
- Update hook versions in `.pre-commit-config.yaml`
- Clear cache: `pre-commit clean`

## Resources

- [Black Documentation](https://black.readthedocs.io/)
- [Flake8 Documentation](https://flake8.pycqa.org/)
- [mypy Documentation](https://mypy.readthedocs.io/)
- [pre-commit Documentation](https://pre-commit.com/)
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)

## Contact

For questions or suggestions about code quality standards, please:

- Open an issue on GitHub
- Contact the development team at <contact@isdataconsulting.com>
- Discuss in team meetings
