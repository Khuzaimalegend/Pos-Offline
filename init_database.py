"""
Database initialization script for POS System
This script creates all database tables based on SQLAlchemy models.
"""

import os
import sys
from sqlalchemy import create_engine
from pos_app.models.database import Base, get_database_url

def init_database():
    print("🔧 Initializing database...")
    
    # Get database URL
    db_url = get_database_url()
    print(f"📡 Connecting to database: {db_url}")
    
    try:
        # Create engine
        engine = create_engine(db_url)
        
        # Create all tables
        print("🛠️  Creating database tables...")
        Base.metadata.create_all(engine)
        
        print("✅ Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    success = init_database()
    if success:
        print("\nYou can now start the POS application.")
    else:
        print("\nFailed to initialize database. Please check the error message above.")
    
    input("\nPress Enter to exit...")
