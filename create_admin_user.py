#!/usr/bin/env python3
"""Create an admin user for the POS application"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pos_app.models.database import db_session, User
from pos_app.utils.auth import hash_password

def create_admin_user():
    """Create a default admin user"""
    try:
        # Check if admin user already exists
        existing_admin = db_session.query(User).filter(User.username == 'admin').first()
        if existing_admin:
            print("✅ Admin user already exists!")
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            password_hash=hash_password('admin123'),
            full_name='Administrator',
            is_admin=True,
            is_active=True
        )
        
        db_session.add(admin_user)
        db_session.commit()
        
        print("✅ Admin user created successfully!")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Role: Administrator")
        
    except Exception as e:
        db_session.rollback()
        print(f"❌ Error creating admin user: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin_user()
