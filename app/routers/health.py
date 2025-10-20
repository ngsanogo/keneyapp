"""
Health check endpoints for monitoring and load balancers
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from datetime import datetime
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "keneyapp-backend",
        "version": os.getenv("APP_VERSION", "1.0.0")
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection failed"
        )
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "keneyapp-backend",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "database": db_status,
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check for Kubernetes"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        
        # Test if we can query users (basic functionality test)
        user_count = db.query(User).count()
        
        return {
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "user_count": user_count
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service not ready: {str(e)}"
        )

@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }
