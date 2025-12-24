"""
Migration script to update database schema for new POS application
Handles schema changes, column additions, and data transformations
"""

import os
import sys
import json
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from pos_app.utils.network_manager import read_db_config, detect_local_ip
from pos_app.utils.ip_scanner import IPScanner


class DatabaseMigration:
    def __init__(self):
        self.config = None
        self.conn = None
        self.cursor = None
        self.migration_log = []
        
    def log(self, message):
        """Log migration messages"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {message}"
        print(log_msg)
        self.migration_log.append(log_msg)
    
    def connect_to_database(self):
        """Connect to the database"""
        try:
            self.config = read_db_config()
            self.log(f"Connecting to database at {self.config['host']}:{self.config['port']}")
            
            self.conn = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
            self.cursor = self.conn.cursor()
            self.log("✅ Successfully connected to database")
            return True
        except Exception as e:
            self.log(f"❌ Failed to connect to database: {e}")
            return False
    
    def check_table_exists(self, table_name):
        """Check if a table exists"""
        try:
            self.cursor.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name=%s)",
                (table_name,)
            )
            return self.cursor.fetchone()[0]
        except Exception as e:
            self.log(f"Error checking table {table_name}: {e}")
            return False
    
    def add_column_if_not_exists(self, table_name, column_name, column_type):
        """Add a column to a table if it doesn't exist"""
        try:
            self.cursor.execute(
                f"SELECT EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name=%s AND column_name=%s)",
                (table_name, column_name)
            )
            if not self.cursor.fetchone()[0]:
                self.cursor.execute(
                    sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        sql.Identifier(table_name),
                        sql.Identifier(column_name),
                        sql.SQL(column_type)
                    )
                )
                self.conn.commit()
                self.log(f"✅ Added column {column_name} to {table_name}")
                return True
            else:
                self.log(f"⚠️  Column {column_name} already exists in {table_name}")
                return False
        except Exception as e:
            self.log(f"❌ Error adding column {column_name} to {table_name}: {e}")
            self.conn.rollback()
            return False
    
    def migrate_users_table(self):
        """Migrate users table"""
        self.log("\n--- Migrating Users Table ---")
        if not self.check_table_exists('users'):
            self.log("⚠️  Users table does not exist, skipping migration")
            return
        
        # Add new columns if they don't exist
        self.add_column_if_not_exists('users', 'is_admin', 'BOOLEAN DEFAULT FALSE')
        self.add_column_if_not_exists('users', 'is_active', 'BOOLEAN DEFAULT TRUE')
        self.add_column_if_not_exists('users', 'last_login', 'TIMESTAMP')
        self.add_column_if_not_exists('users', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('users', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_products_table(self):
        """Migrate products table"""
        self.log("\n--- Migrating Products Table ---")
        if not self.check_table_exists('products'):
            self.log("⚠️  Products table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('products', 'sku', 'VARCHAR(50) UNIQUE')
        self.add_column_if_not_exists('products', 'barcode', 'VARCHAR(100) UNIQUE')
        self.add_column_if_not_exists('products', 'description', 'TEXT')
        self.add_column_if_not_exists('products', 'cost_price', 'DECIMAL(10,2)')
        self.add_column_if_not_exists('products', 'selling_price', 'DECIMAL(10,2)')
        self.add_column_if_not_exists('products', 'quantity_in_stock', 'INTEGER DEFAULT 0')
        self.add_column_if_not_exists('products', 'reorder_level', 'INTEGER DEFAULT 10')
        self.add_column_if_not_exists('products', 'is_active', 'BOOLEAN DEFAULT TRUE')
        self.add_column_if_not_exists('products', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('products', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_customers_table(self):
        """Migrate customers table"""
        self.log("\n--- Migrating Customers Table ---")
        if not self.check_table_exists('customers'):
            self.log("⚠️  Customers table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('customers', 'code', 'VARCHAR(20) UNIQUE')
        self.add_column_if_not_exists('customers', 'type', 'VARCHAR(20)')
        self.add_column_if_not_exists('customers', 'contact', 'VARCHAR(50)')
        self.add_column_if_not_exists('customers', 'email', 'VARCHAR(100)')
        self.add_column_if_not_exists('customers', 'address', 'VARCHAR(200)')
        self.add_column_if_not_exists('customers', 'city', 'VARCHAR(50)')
        self.add_column_if_not_exists('customers', 'state', 'VARCHAR(50)')
        self.add_column_if_not_exists('customers', 'postal_code', 'VARCHAR(20)')
        self.add_column_if_not_exists('customers', 'credit_limit', 'DECIMAL(10,2) DEFAULT 0')
        self.add_column_if_not_exists('customers', 'is_active', 'BOOLEAN DEFAULT TRUE')
        self.add_column_if_not_exists('customers', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('customers', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_sales_table(self):
        """Migrate sales table"""
        self.log("\n--- Migrating Sales Table ---")
        if not self.check_table_exists('sales'):
            self.log("⚠️  Sales table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('sales', 'sale_number', 'VARCHAR(50) UNIQUE')
        self.add_column_if_not_exists('sales', 'customer_id', 'INTEGER')
        self.add_column_if_not_exists('sales', 'sale_date', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('sales', 'total_amount', 'DECIMAL(10,2) DEFAULT 0')
        self.add_column_if_not_exists('sales', 'discount_amount', 'DECIMAL(10,2) DEFAULT 0')
        self.add_column_if_not_exists('sales', 'tax_amount', 'DECIMAL(10,2) DEFAULT 0')
        self.add_column_if_not_exists('sales', 'net_amount', 'DECIMAL(10,2) DEFAULT 0')
        self.add_column_if_not_exists('sales', 'payment_method', 'VARCHAR(50)')
        self.add_column_if_not_exists('sales', 'status', 'VARCHAR(20) DEFAULT \'COMPLETED\'')
        self.add_column_if_not_exists('sales', 'notes', 'TEXT')
        self.add_column_if_not_exists('sales', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('sales', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_sale_items_table(self):
        """Migrate sale items table"""
        self.log("\n--- Migrating Sale Items Table ---")
        if not self.check_table_exists('sale_items'):
            self.log("⚠️  Sale Items table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('sale_items', 'sale_id', 'INTEGER')
        self.add_column_if_not_exists('sale_items', 'product_id', 'INTEGER')
        self.add_column_if_not_exists('sale_items', 'quantity', 'INTEGER DEFAULT 1')
        self.add_column_if_not_exists('sale_items', 'unit_price', 'DECIMAL(10,2)')
        self.add_column_if_not_exists('sale_items', 'discount_percent', 'DECIMAL(5,2) DEFAULT 0')
        self.add_column_if_not_exists('sale_items', 'line_total', 'DECIMAL(10,2)')
        self.add_column_if_not_exists('sale_items', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_inventory_table(self):
        """Migrate inventory table"""
        self.log("\n--- Migrating Inventory Table ---")
        if not self.check_table_exists('inventory'):
            self.log("⚠️  Inventory table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('inventory', 'product_id', 'INTEGER')
        self.add_column_if_not_exists('inventory', 'quantity_on_hand', 'INTEGER DEFAULT 0')
        self.add_column_if_not_exists('inventory', 'quantity_reserved', 'INTEGER DEFAULT 0')
        self.add_column_if_not_exists('inventory', 'location', 'VARCHAR(100)')
        self.add_column_if_not_exists('inventory', 'last_counted', 'TIMESTAMP')
        self.add_column_if_not_exists('inventory', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('inventory', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_expenses_table(self):
        """Migrate expenses table"""
        self.log("\n--- Migrating Expenses Table ---")
        if not self.check_table_exists('expenses'):
            self.log("⚠️  Expenses table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('expenses', 'category', 'VARCHAR(100)')
        self.add_column_if_not_exists('expenses', 'amount', 'DECIMAL(10,2)')
        self.add_column_if_not_exists('expenses', 'expense_date', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('expenses', 'description', 'TEXT')
        self.add_column_if_not_exists('expenses', 'payment_method', 'VARCHAR(50)')
        self.add_column_if_not_exists('expenses', 'is_recurring', 'BOOLEAN DEFAULT FALSE')
        self.add_column_if_not_exists('expenses', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('expenses', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def migrate_suppliers_table(self):
        """Migrate suppliers table"""
        self.log("\n--- Migrating Suppliers Table ---")
        if not self.check_table_exists('suppliers'):
            self.log("⚠️  Suppliers table does not exist, skipping migration")
            return
        
        self.add_column_if_not_exists('suppliers', 'code', 'VARCHAR(20) UNIQUE')
        self.add_column_if_not_exists('suppliers', 'contact_person', 'VARCHAR(100)')
        self.add_column_if_not_exists('suppliers', 'email', 'VARCHAR(100)')
        self.add_column_if_not_exists('suppliers', 'phone', 'VARCHAR(20)')
        self.add_column_if_not_exists('suppliers', 'address', 'VARCHAR(200)')
        self.add_column_if_not_exists('suppliers', 'city', 'VARCHAR(50)')
        self.add_column_if_not_exists('suppliers', 'state', 'VARCHAR(50)')
        self.add_column_if_not_exists('suppliers', 'postal_code', 'VARCHAR(20)')
        self.add_column_if_not_exists('suppliers', 'payment_terms', 'VARCHAR(100)')
        self.add_column_if_not_exists('suppliers', 'is_active', 'BOOLEAN DEFAULT TRUE')
        self.add_column_if_not_exists('suppliers', 'created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        self.add_column_if_not_exists('suppliers', 'updated_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
    
    def run_all_migrations(self):
        """Run all database migrations"""
        self.log("=" * 80)
        self.log("POS DATABASE MIGRATION STARTED")
        self.log("=" * 80)
        
        if not self.connect_to_database():
            self.log("❌ Migration failed: Could not connect to database")
            return False
        
        try:
            self.migrate_users_table()
            self.migrate_products_table()
            self.migrate_customers_table()
            self.migrate_sales_table()
            self.migrate_sale_items_table()
            self.migrate_inventory_table()
            self.migrate_expenses_table()
            self.migrate_suppliers_table()
            
            self.log("\n" + "=" * 80)
            self.log("✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY")
            self.log("=" * 80)
            return True
            
        except Exception as e:
            self.log(f"\n❌ Migration failed with error: {e}")
            self.conn.rollback()
            return False
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn:
                self.conn.close()
    
    def save_migration_log(self):
        """Save migration log to file"""
        try:
            log_dir = os.path.join(os.path.dirname(__file__), 'migration_logs')
            os.makedirs(log_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"migration_{timestamp}.log")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.migration_log))
            
            self.log(f"\n📝 Migration log saved to: {log_file}")
        except Exception as e:
            self.log(f"Warning: Could not save migration log: {e}")


def main():
    """Main migration function"""
    print("\n" + "=" * 80)
    print("POS SYSTEM DATABASE MIGRATION TOOL")
    print("=" * 80)
    print("\nThis script will update your database schema to match the new application.")
    print("It will ADD new columns but will NOT delete any existing data.\n")
    
    response = input("Do you want to proceed with the migration? (yes/no): ").strip().lower()
    
    if response not in ['yes', 'y']:
        print("Migration cancelled.")
        return
    
    migration = DatabaseMigration()
    success = migration.run_all_migrations()
    migration.save_migration_log()
    
    if success:
        print("\n✅ Migration completed successfully!")
        print("Your database is now ready for the new POS application.")
    else:
        print("\n❌ Migration failed. Please check the logs for details.")
        sys.exit(1)


if __name__ == '__main__':
    main()
