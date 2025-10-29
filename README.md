# KeneyApp

KeneyApp is a modern healthcare data management platform built with **Python**, **React (TypeScript)**, and **PostgreSQL**. It provides an end-to-end system for managing patient records, appointments, prescriptions, and hospital workflows.

## 🏥 Features

### Core Functionality
- **Patient Management**: Complete patient record system with medical history, allergies, and emergency contacts
- **Appointment Scheduling**: Comprehensive appointment management with status tracking
- **Prescription Management**: Digital prescription system with medication details and refill tracking
- **Dashboard**: Real-time health metrics and statistics
- **Multi-Role Support**: Role-based access control for Admin, Doctor, Nurse, and Receptionist

### Security & Compliance
- ✅ GDPR/HIPAA compliant architecture
- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ Role-based access control (RBAC)
- ✅ **Comprehensive audit logging** for all critical operations
- ✅ **Rate limiting** to prevent abuse
- ✅ **Security headers** (XSS, CSRF, CSP protection)
- ✅ CORS protection
- ✅ Input validation with Pydantic

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

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**
   ```bash
   docker-compose up -d
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

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/patients/` - List all patients
- `POST /api/v1/patients/` - Create new patient
- `GET /api/v1/appointments/` - List all appointments
- `POST /api/v1/appointments/` - Create new appointment
- `GET /api/v1/prescriptions/` - List all prescriptions
- `POST /api/v1/prescriptions/` - Create new prescription
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /health` - Health check endpoint
- `GET /metrics` - Prometheus metrics

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
```

### Frontend Tests
```bash
cd frontend
npm test
```

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

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run linting and tests
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

KeneyApp is proprietary software owned by **ISDATA Consulting**.  
Unauthorized copying, modification, or distribution of this software is prohibited.  

For licensing or partnership inquiries, please contact: **contact@isdataconsulting.com**

## 📞 Support

For technical support or questions, please contact:  
📧 **contact@isdataconsulting.com**

---

Made with ❤️ by ISDATA Consulting
