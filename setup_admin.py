#!/usr/bin/env python3
"""
Setup admin user for POS application
Run this on a new PC to create the default admin user
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

def setup_admin():
    """Setup default admin user"""
    try:
        from pos_app.models.database import db_session, User, engine, Base
        from pos_app.utils.auth import hash_password
        from pos_app.utils.network_manager import read_db_config
        
        print("\n" + "=" * 80)
        print("  POS SYSTEM - ADMIN USER SETUP")
        print("=" * 80 + "\n")
        
        # Read database config
        db_config = read_db_config()
        print(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        print(f"Username: {db_config['username']}\n")
        
        # Create tables if they don't exist
        print("Creating database tables...")
        try:
            Base.metadata.create_all(engine)
            print("[OK] Database tables created/verified\n")
        except Exception as e:
            print(f"[WARN] Could not create tables: {e}\n")
        
        # Check if admin user already exists
        print("Checking for existing admin user...")
        existing_admin = db_session.query(User).filter(User.username == 'admin').first()
        
        if existing_admin:
            print("[OK] Admin user already exists!")
            print(f"    Username: {existing_admin.username}")
            print(f"    Full Name: {existing_admin.full_name}")
            print(f"    Status: {'Active' if existing_admin.is_active else 'Inactive'}\n")
            return True
        
        # Create admin user
        print("Creating default admin user...\n")
        
        admin_password = 'admin'
        admin_user = User(
            username='admin',
            password_hash=hash_password(admin_password),
            full_name='Administrator',
            is_admin=True,
            is_active=True
        )
        
        db_session.add(admin_user)
        db_session.commit()
        
        print("[OK] Admin user created successfully!\n")
        print("Login Credentials:")
        print(f"  Username: admin")
        print(f"  Password: {admin_password}")
        print(f"  Role: Administrator\n")
        
        print("=" * 80)
        print("  SETUP COMPLETE")
        print("=" * 80 + "\n")
        
        print("You can now login to the POS application with these credentials.\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to setup admin user: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = setup_admin()
    sys.exit(0 if success else 1)
