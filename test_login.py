#!/usr/bin/env python3
"""Test login functionality"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pos_app.models.database import db_session, User
from pos_app.utils.auth import check_password, hash_password

def test_admin_login():
    """Test admin login"""
    try:
        # Check if admin user exists
        admin = db_session.query(User).filter(User.username == 'admin').first()
        
        if not admin:
            print("❌ Admin user not found in database")
            return False
        
        print(f"✅ Admin user found: {admin.username}")
        print(f"   Full Name: {admin.full_name}")
        print(f"   Is Admin: {admin.is_admin}")
        print(f"   Is Active: {admin.is_active}")
        
        # Test password verification
        test_password = 'admin123'
        if check_password(test_password, admin.password_hash):
            print(f"✅ Password verification successful for 'admin123'")
            return True
        else:
            print(f"❌ Password verification failed for 'admin123'")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == '__main__':
    print("Testing Admin Login Credentials...")
    print("=" * 50)
    
    if test_admin_login():
        print("\n✅ Login test PASSED - You can login with:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n❌ Login test FAILED")
        sys.exit(1)
