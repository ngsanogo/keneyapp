# KeneyApp

[![CI](https://github.com/ISData-consulting/keneyapp/actions/workflows/ci.yml/badge.svg)](https://github.com/ISData-consulting/keneyapp/actions/workflows/ci.yml)
[![Security Scan](https://github.com/ISData-consulting/keneyapp/actions/workflows/security-scan.yml/badge.svg)](https://github.com/ISData-consulting/keneyapp/actions/workflows/security-scan.yml)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18.0+-blue.svg)](https://react.dev/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

KeneyApp is a modern healthcare data management platform built with **Python**, **React (TypeScript)**, and **PostgreSQL**. It provides an end-to-end system for managing patient records, appointments, prescriptions, and hospital workflows.

## 🏥 Features

### Core Functionality
- **Patient Management**: Complete patient record system with medical history, allergies, and emergency contacts
- **Appointment Scheduling**: Comprehensive appointment management with status tracking
- **Prescription Management**: Digital prescription system with medication details and refill tracking
- **Dashboard**: Real-time health metrics and statistics
- **Multi-Role Support**: Role-based access control for Admin, Doctor, Nurse, and Receptionist

### 🆕 Enterprise Features (v2.0)
- ✅ **OAuth2/OIDC Authentication**: SSO with Google, Microsoft, and Okta
- ✅ **Data Encryption at Rest**: AES-256-GCM encryption for sensitive patient data
- ✅ **GraphQL API**: Modern API alongside REST for flexible data queries
- ✅ **FHIR Interoperability**: HL7 FHIR R4 support for healthcare data exchange
- ✅ **Medical Terminologies**: ICD-11, SNOMED CT, LOINC, ATC, CPT/CCAM coding support
- ✅ **Cloud Deployment**: Terraform scripts for AWS, Azure, and GCP

### Security & Compliance
- ✅ **GDPR/HIPAA/HDS compliant architecture**
- ✅ JWT-based authentication + OAuth2/OIDC
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ **Data encryption at rest** (AES-256-GCM)
- ✅ **Comprehensive audit logging** for all critical operations
- ✅ **Rate limiting** to prevent abuse
- ✅ **Security headers** (XSS, CSRF, CSP protection)
- ✅ CORS protection
- ✅ Input validation with Pydantic
- ✅ **International medical coding standards** (ICD-11, SNOMED CT, LOINC, ATC, CPT/CCAM)

### Performance & Scalability
- ⚡ **Redis caching** for frequently accessed data
- ⚡ **Celery background tasks** for asynchronous operations
- ⚡ **Horizontal auto-scaling** with Kubernetes HPA
- ⚡ **Prometheus metrics** for monitoring
- ⚡ Database query optimization

### Enterprise Features
- 🚀 **Kubernetes deployment** ready with Helm charts
- 📊 **Grafana dashboards** for visualization
- 🔍 **Prometheus monitoring** for metrics collection
- 📝 **Comprehensive API documentation**
- 🔄 **Background job processing** with Celery
- 📈 **Health check endpoints** for load balancers

## 🏥 Medical Standards & Interoperability

KeneyApp implements international healthcare standards for maximum interoperability and compliance:

### Supported Medical Terminologies
- **ICD-11** (WHO): International Classification of Diseases for diagnosis coding
- **SNOMED CT**: Comprehensive clinical terminology for detailed medical coding
- **LOINC**: Laboratory and clinical observation coding
- **ATC**: Medication classification (Anatomical Therapeutic Chemical)
- **CPT** (US): Current Procedural Terminology for medical procedures
- **CCAM** (France): Classification Commune des Actes Médicaux for procedures
- **DICOM**: Digital Imaging and Communications in Medicine (reference support)

### FHIR Resources
- **Patient**: Demographics and identifiers
- **Appointment**: Scheduling and visits
- **MedicationRequest**: Prescriptions with ATC codes
- **Condition**: Diagnoses with ICD-11/SNOMED CT codes
- **Observation**: Lab results and vital signs with LOINC codes
- **Procedure**: Medical procedures with CPT/CCAM codes

### Compliance
- ✅ **RGPD** (Europe): Full GDPR compliance with data protection and privacy controls
- ✅ **HIPAA** (US): Security and confidentiality of health information
- ✅ **HDS** (France): Hébergeur de Données de Santé certification-ready architecture

See [Medical Terminologies Guide](docs/MEDICAL_TERMINOLOGIES.md) for complete documentation.

## 🛠 Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL 15
- **Cache & Queue**: Redis 7 + Celery
- **Monitoring**: Prometheus + Grafana
- **Containerization**: Docker & Kubernetes
- **CI/CD**: GitHub Actions
- **Testing**: pytest (backend), Jest (frontend)
- **Code Quality**: Black, Flake8, ESLint

## 📁 Project Structure

```
keneyapp/
├── app/                    # Backend application
│   ├── core/              # Core configuration and security
│   │   ├── config.py      # Application settings
│   │   ├── security.py    # JWT and password hashing
│   │   └── database.py    # Database connection
│   ├── models/            # SQLAlchemy database models
│   │   ├── user.py        # User model with roles
│   │   ├── patient.py     # Patient records
│   │   ├── appointment.py # Appointments
│   │   └── prescription.py # Prescriptions
│   ├── routers/           # FastAPI route handlers
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── patients.py    # Patient CRUD operations
│   │   ├── appointments.py # Appointment management
│   │   ├── prescriptions.py # Prescription handling
│   │   └── dashboard.py   # Dashboard statistics
│   ├── schemas/           # Pydantic schemas for validation
│   └── main.py            # FastAPI application entry point
├── frontend/              # React TypeScript frontend
│   ├── src/
│   │   ├── components/    # Reusable React components
│   │   │   └── Header.tsx # Navigation header
│   │   ├── contexts/      # React context providers
│   │   │   └── AuthContext.tsx # Authentication context
│   │   ├── pages/         # Page components
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   ├── PatientsPage.tsx
│   │   │   ├── AppointmentsPage.tsx
│   │   │   └── PrescriptionsPage.tsx
│   │   └── App.tsx        # Main application component
│   └── package.json
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
│   └── init_db.py        # Database initialization
├── tests/                 # Backend tests
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Backend Docker configuration
├── Dockerfile.frontend   # Frontend Docker configuration
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ISData-consulting/keneyapp.git
   cd keneyapp
   ```

2. **Start all services**
   ```bash
   ./scripts/start_stack.sh
   # add --logs to follow container output, or --down to stop everything
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/v1/docs
   - Prometheus Metrics: http://localhost:8000/metrics
   - Flower (Celery Monitoring): http://localhost:5555
   - Redis: localhost:6379

### Option 2: Manual Setup

#### Backend Setup

1. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   createdb keneyapp
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Update DATABASE_URL in .env if needed
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Initialize database with sample data**
   ```bash
   python scripts/init_db.py
   ```

7. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```

#### Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm start
   ```

## 👥 Demo Accounts

When `ENABLE_BOOTSTRAP_ADMIN=True` (default for local/test), KeneyApp provisions a default tenant and administrators so you can log in immediately. Update or disable these credentials for production deployments.

After running the initialization script, you can log in with these demo accounts:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | doctor | doctor123 |
| Nurse | nurse | nurse123 |
| Receptionist | receptionist | receptionist123 |

## 📚 API Documentation

The API documentation is automatically generated and available at:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

### Main Endpoints

**Authentication:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Retrieve current authenticated user profile
- `GET /api/v1/oauth/authorize/{provider}` - 🆕 Initiate OAuth flow
- `GET /api/v1/oauth/callback/{provider}` - 🆕 OAuth callback handler

**Patient Management:**
- `GET /api/v1/patients/` - List all patients
- `POST /api/v1/patients/` - Create new patient
- `GET /api/v1/fhir/Patient/{id}` - 🆕 Get patient in FHIR format
- `POST /api/v1/fhir/Patient` - 🆕 Create patient from FHIR resource

**Appointments & Prescriptions:**
- `GET /api/v1/appointments/` - List all appointments
- `POST /api/v1/appointments/` - Create new appointment
- `GET /api/v1/prescriptions/` - List all prescriptions
- `POST /api/v1/prescriptions/` - Create new prescription
- `GET /api/v1/fhir/Appointment/{id}` - 🆕 Get appointment in FHIR format
- `GET /api/v1/fhir/MedicationRequest/{id}` - 🆕 Get prescription in FHIR format

**Dashboard & Monitoring:**
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics
- `POST /graphql` - 🆕 GraphQL endpoint
- `GET /api/v1/fhir/metadata` - 🆕 FHIR capability statement

## 🔍 Monitoring & Observability

### Prometheus Metrics

KeneyApp exposes detailed metrics at `/metrics` endpoint:

```bash
curl http://localhost:8000/metrics
```

**Available Metrics:**
- `http_requests_total` - Total HTTP requests by method, endpoint, and status
- `http_request_duration_seconds` - Request duration histogram
- `patient_operations_total` - Total patient operations
- `appointment_bookings_total` - Total appointment bookings
- `prescription_created_total` - Total prescriptions created
- `active_users` - Current active users
- `database_connections` - Active database connections

### Structured Logging & Correlation IDs

All requests are automatically assigned a correlation ID for distributed tracing:

```bash
# Requests include X-Correlation-ID header in responses
curl -v https://api.keneyapp.com/health

# Custom correlation IDs can be passed
curl -H "X-Correlation-ID: my-trace-id" https://api.keneyapp.com/health
```

Logs are structured in JSON format for easy parsing:
```json
{
  "event": "request_complete",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "method": "GET",
  "path": "/api/v1/patients",
  "status_code": 200,
  "duration_ms": 45.23,
  "client_ip": "192.168.1.100"
}
```

### Grafana Dashboards

Pre-configured dashboards are available in `/monitoring/grafana-dashboard.json`:
- API performance metrics
- Database health
- Redis cache statistics
- Healthcare-specific KPIs

### Celery Monitoring with Flower

Monitor background tasks in real-time:

```bash
# Access Flower UI
http://localhost:5555
```

**Background Tasks:**
- `send_appointment_reminder` - Send appointment notifications
- `generate_patient_report` - Create comprehensive patient reports
- `check_prescription_interactions` - Validate drug interactions
- `backup_patient_data` - Automated data backups
- `cleanup_expired_tokens` - Remove expired authentication tokens

## 🔐 Audit Logging

All critical operations are logged for GDPR/HIPAA compliance:

```python
# Audit logs include:
- User authentication events
- Patient record access/modifications
- Prescription creation/updates
- Appointment management
- Administrative actions

# Each log entry contains:
- Timestamp
- User ID and username
- Action performed (CREATE, READ, UPDATE, DELETE)
- Resource type and ID
- IP address and user agent
- Additional context
- Success/failure status
```

Query audit logs via the database:
```sql
SELECT * FROM audit_logs 
WHERE resource_type = 'patient' 
ORDER BY timestamp DESC 
LIMIT 100;
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py -v

# Run smoke tests against docker stack
docker compose up -d
pytest tests/test_smoke.py -v
```

**Test Coverage:** 77% (65 tests)

**Test Types:**
- Unit tests for API endpoints, models, and services
- Integration tests with database
- API contract tests (JSON Schema validation)
- Smoke tests for critical flows
- Middleware and security tests

### Frontend Tests
```bash
cd frontend
npm test
```

### CI/CD Testing Pipeline

Our CI/CD pipeline includes comprehensive automated testing:

1. **Code Quality**
   - Linting with flake8 and ESLint
   - Code formatting with Black and Prettier
   - Type checking with mypy

2. **Unit & Integration Tests**
   - Backend: pytest with 77% coverage
   - Frontend: Jest test suite
   - Contract tests for API compatibility

3. **Security Testing**
   - CodeQL static analysis
   - Dependency vulnerability scanning (pip-audit, npm audit)
   - Container security scanning (Trivy)
   - Secret detection (Gitleaks, detect-secrets)

4. **Smoke Testing**
   - Docker compose stack validation
   - Critical API flow testing
   - Health endpoint monitoring
   - Authentication flows
   - Patient management operations

All tests run automatically on every pull request and push to main/develop branches.

## 🔍 Code Quality

### Backend Linting
```bash
# Check code style
flake8 app

# Format code
black app

# Type checking
mypy app
```

### Frontend Linting
```bash
cd frontend
npm run lint
```

## 🌍 Environment Variables

Create a `.env` file with the following variables:

```env
# Application
APP_NAME=KeneyApp
APP_VERSION=1.0.0
DEBUG=False

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
MFA_ISSUER=KeneyApp
MAX_FAILED_LOGIN_ATTEMPTS=5

# Database
DATABASE_URL=postgresql://keneyapp:keneyapp@localhost:5432/keneyapp

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 🚢 Deployment

### Kubernetes Deployment

KeneyApp is production-ready with comprehensive Kubernetes manifests:

```bash
# Deploy to Kubernetes
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/ingress.yaml

# Check deployment status
kubectl get pods -n keneyapp
```

**Features:**
- Horizontal Pod Autoscaling (3-10 replicas)
- Health checks and readiness probes
- Resource limits and requests
- Persistent storage for PostgreSQL
- TLS/SSL termination at ingress
- Rolling updates with zero downtime

See [k8s/README.md](k8s/README.md) for detailed deployment instructions.

### Docker Production Deployment

1. **Set environment variables**
   ```bash
   export DATABASE_URL=your_production_database_url
   export SECRET_KEY=your_production_secret_key
   export ALLOWED_ORIGINS=https://your-domain.com
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Deploy with Docker**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 🤝 Contributing

We welcome contributions! Please read our contribution guidelines before submitting PRs.

**Quick Links:**
- [Contributing Guide](CONTRIBUTING.md) - Detailed contribution guidelines
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community standards
- [Security Policy](SECURITY.md) - Security reporting and best practices

**Development Setup:**
```bash
# Quick setup with Makefile
make setup          # Install dependencies and hooks
make dev            # Start development servers
make test           # Run tests
make lint           # Check code quality
```

**Contribution Process:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following our [coding standards](CONTRIBUTING.md#coding-standards)
4. Add tests for new functionality
5. Run quality checks (`make lint && make test`)
6. Commit using [conventional commits](CONTRIBUTING.md#commit-message-convention)
7. Push to your fork and open a Pull Request

## 📚 Documentation

Comprehensive documentation available in the `docs/` directory:

### Getting Started
- **[Development Guide](docs/DEVELOPMENT.md)** - Complete development setup and workflow
- **[API Reference](docs/API_REFERENCE.md)** - Full API documentation with examples
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions

### Advanced Features
- **[OAuth Guide](docs/OAUTH_GUIDE.md)** - OAuth2/OIDC authentication setup
- **[Encryption Guide](docs/ENCRYPTION_GUIDE.md)** - Data encryption implementation
- **[FHIR Guide](docs/FHIR_GUIDE.md)** - FHIR interoperability guide
- **[Medical Terminologies](docs/MEDICAL_TERMINOLOGIES.md)** - Healthcare standards implementation (ICD-11, SNOMED CT, LOINC, ATC, CPT/CCAM)
- **[New Features](docs/NEW_FEATURES.md)** - Complete v2.0 feature overview
- **[Integration Plan](docs/INTEGRATION_PLAN.md)** - System integration guide

### Operations & Maintenance
- **[Incident Response Playbook](docs/INCIDENT_RESPONSE.md)** - Step-by-step incident handling procedures
- **[Operations Runbook](docs/OPERATIONS_RUNBOOK.md)** - Standard operating procedures and troubleshooting

## 📄 License

KeneyApp is proprietary software owned by **ISDATA Consulting**.  
Unauthorized copying, modification, or distribution of this software is prohibited.  

For licensing or partnership inquiries, please contact: **contact@isdataconsulting.com**

## 📞 Support

For technical support or questions, please contact:  
📧 **contact@isdataconsulting.com**

---

Made with ❤️ by ISDATA Consulting
