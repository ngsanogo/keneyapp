from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers import auth, patients, appointments, prescriptions, users
from app.core.config import settings

app = FastAPI(
    title="KeneyApp API",
    description="Healthcare Data Management Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(patients.router, prefix="/api/patients", tags=["patients"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["appointments"])
app.include_router(prescriptions.router, prefix="/api/prescriptions", tags=["prescriptions"])

@app.get("/")
async def root():
    return {"message": "Welcome to KeneyApp API", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "KeneyApp API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
