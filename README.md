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
- ✅ CORS protection
- ✅ Input validation with Pydantic

## 🛠 Tech Stack

- **Backend**: FastAPI (Python 3.11)
- **Frontend**: React 18 + TypeScript
- **Database**: PostgreSQL 15
- **Containerization**: Docker & Docker Compose
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
```

## 🚢 Deployment

### Production Deployment

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
