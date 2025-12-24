#!/usr/bin/env python3
"""
Migration script to add is_refund and refund_of_sale_id columns to sales table
"""

import psycopg2
from psycopg2 import sql
import sys

def migrate_database():
    """Add refund columns to sales table"""
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="pos_network",
            user="admin",
            password="admin"
        )
        cursor = conn.cursor()
        
        print("[MIGRATION] Starting database migration...")
        
        # Check if columns already exist
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='sales' AND column_name='is_refund'
        """)
        
        if cursor.fetchone():
            print("[MIGRATION] Column 'is_refund' already exists, skipping...")
        else:
            print("[MIGRATION] Adding 'is_refund' column...")
            cursor.execute("""
                ALTER TABLE sales 
                ADD COLUMN is_refund BOOLEAN DEFAULT FALSE
            """)
            print("[MIGRATION] ✅ Added 'is_refund' column")
        
        # Check if refund_of_sale_id column exists
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='sales' AND column_name='refund_of_sale_id'
        """)
        
        if cursor.fetchone():
            print("[MIGRATION] Column 'refund_of_sale_id' already exists, skipping...")
        else:
            print("[MIGRATION] Adding 'refund_of_sale_id' column...")
            cursor.execute("""
                ALTER TABLE sales 
                ADD COLUMN refund_of_sale_id INTEGER REFERENCES sales(id)
            """)
            print("[MIGRATION] ✅ Added 'refund_of_sale_id' column")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("[MIGRATION] ✅ Database migration completed successfully!")
        return True
        
    except psycopg2.Error as e:
        print(f"[MIGRATION] ❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"[MIGRATION] ❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)
