# KeneyApp
KeneyApp is a modern healthcare data management platform built with **Python**, **React (TypeScript)**, and **PostgreSQL**.

It provides an end-to-end system for managing patient records, appointments, prescriptions, and hospital workflows — suitable for:
- Liberal physicians (solo practice)
- Small and medium-sized clinics
- Large hospitals with multiple departments

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript
- **Database**: PostgreSQL
- **Containerization**: Docker
- **CI/CD**: GitHub Actions

## Features
- 🔐 **Secure Authentication**: JWT-based authentication system
- 👥 **Patient Management**: Complete patient records with medical history
- 📅 **Appointment Scheduling**: Manage appointments with status tracking
- 💊 **Prescription Management**: Digital prescription system
- 📊 **Dashboard**: Real-time healthcare metrics
- 🏥 **Multi-role Support**: Admin, Doctor, Nurse, Receptionist roles
- 🔒 **Data Security**: GDPR/HIPAA compliance ready

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker (optional)

### Option 1: Docker Compose (Recommended)
```bash
# Clone the repository
git clone https://github.com/ISData-consulting/keneyapp.git
cd keneyapp

# Start all services
docker-compose up -d

# The application will be available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/api/docs
```

### Option 2: Manual Setup

#### Backend Setup
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb keneyapp
# Update DATABASE_URL in .env if needed

# Run database migrations
alembic upgrade head

# Initialize database with sample data
python scripts/init_db.py

# Start backend server
uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm start
```

## Default Login Credentials
- **Admin**: username: `admin`, password: `admin123`
- **Doctor**: username: `doctor`, password: `doctor123`

## API Documentation
Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Project Structure
```
keneyapp/
├── app/                    # Backend application
│   ├── core/              # Core configuration and security
│   ├── models/            # SQLAlchemy database models
│   ├── routers/           # FastAPI route handlers
│   ├── schemas/           # Pydantic schemas for validation
│   └── main.py            # FastAPI application entry point
├── frontend/              # React TypeScript frontend
│   ├── src/
│   │   ├── components/    # Reusable React components
│   │   ├── contexts/      # React context providers
│   │   ├── pages/         # Page components
│   │   └── App.tsx        # Main application component
│   └── package.json
├── alembic/               # Database migrations
├── scripts/               # Utility scripts
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile            # Backend Docker configuration
├── Dockerfile.frontend   # Frontend Docker configuration
└── requirements.txt      # Python dependencies
```

## Database Models
- **Users**: Healthcare staff (doctors, nurses, admins)
- **Patients**: Patient records with medical history
- **Appointments**: Scheduled appointments with status tracking
- **Prescriptions**: Digital prescriptions with medication details

## Security Features
- JWT-based authentication
- Password hashing with bcrypt
- Role-based access control
- CORS protection
- Input validation with Pydantic

## Development

### Running Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Code Quality
```bash
# Backend linting
flake8 app/
black app/

# Frontend linting
cd frontend
npm run lint
```

## Deployment

### Production Environment
1. Set up PostgreSQL database
2. Configure environment variables
3. Run database migrations
4. Deploy with Docker or directly

### Environment Variables
```bash
DATABASE_URL=postgresql://user:password@host:port/database
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=["https://yourdomain.com"]
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License
KeneyApp is proprietary software owned by **ISDATA Consulting**.  
Unauthorized copying, modification, or distribution of this software is prohibited.  
For licensing or partnership inquiries, please contact: contact@isdataconsulting.com.

## Support
For technical support or questions:
- Email: contact@isdataconsulting.com
- Documentation: [API Docs](http://localhost:8000/api/docs)

---

**KeneyApp** - Modern Healthcare Data Management Platform