#!/usr/bin/env python3
"""
Script to create admin user manually
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_admin():
    """Create admin user"""
    db = SessionLocal()
    try:
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            print("✅ Admin user already exists")
            return

        # Create admin user with shorter password
        password = "admin123"
        hashed_password = get_password_hash(password)
        
        admin_user = User(
            email="admin@keneyapp.com",
            username="admin",
            hashed_password=hashed_password,
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

if __name__ == "__main__":
    create_admin()
