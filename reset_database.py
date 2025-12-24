"""
Database reset script - drops and recreates the database
"""

import os
import sys
from sqlalchemy import create_engine, text
from pos_app.models.database import Base, get_database_url

def reset_database():
    print("⚠️  WARNING: This will DROP the existing database and recreate it!")
    print("All data will be lost!")
    
    response = input("\nAre you sure you want to continue? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Operation cancelled.")
        return False
    
    try:
        # Get database URL
        db_url = get_database_url()
        print(f"\n📡 Connecting to PostgreSQL server...")
        
        # Connect to PostgreSQL default database to drop the pos_network database
        server_url = db_url.rsplit('/', 1)[0] + '/postgres'
        engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
        
        with engine.connect() as conn:
            # Terminate existing connections
            conn.execute(text("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'pos_network'
                AND pid <> pg_backend_pid();
            """))
            
            # Drop the database
            print("🗑️  Dropping existing database...")
            conn.execute(text("DROP DATABASE IF EXISTS pos_network;"))
            
            # Create new database
            print("🛠️  Creating new database...")
            conn.execute(text("CREATE DATABASE pos_network;"))
        
        print("✅ Database dropped and recreated successfully!")
        
        # Now create all tables
        print("\n🛠️  Creating database tables...")
        engine = create_engine(db_url)
        Base.metadata.create_all(engine)
        
        print("✅ All tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = reset_database()
    if success:
        print("\n✨ Database is ready! You can now start the POS application.")
    else:
        print("\n❌ Failed to reset database.")
    
    input("\nPress Enter to exit...")
