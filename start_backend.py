#!/usr/bin/env python3
"""
Simple backend startup script that creates tables directly
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import engine, Base
from app.models import *
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from datetime import datetime

def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def create_admin_user():
    """Create initial admin user"""
    from sqlalchemy.orm import Session
    from app.database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("✅ Admin user already exists")
            return

        # Create admin user
        admin_user = User(
            email="admin@keneyapp.com",
            username="admin",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created successfully")
        print("   Username: admin")
        print("   Password: admin123")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Main startup function"""
    print("🚀 Starting KeneyApp backend...")
    
    # Create tables
    if not create_tables():
        sys.exit(1)
    
    # Create admin user
    create_admin_user()
    
    # Start the server
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
