#!/usr/bin/env python3
"""
Script to reset admin user with proper bcrypt hashing
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def reset_admin():
    """Reset admin user with proper bcrypt hashing"""
    db = SessionLocal()
    try:
        # Delete existing admin user
        admin_user = db.query(User).filter(User.username == "admin").first()
        if admin_user:
            db.delete(admin_user)
            db.commit()
            print("✅ Deleted existing admin user")
        
        # Create new admin user with proper bcrypt hashing
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
        print("✅ Admin user created successfully with bcrypt hashing")
        print("   Username: admin")
        print("   Password: admin123")
        
    except Exception as e:
        print(f"❌ Error resetting admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
