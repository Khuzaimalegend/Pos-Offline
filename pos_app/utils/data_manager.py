import os
import psycopg2
from datetime import datetime
import json
import shutil
from pos_app.utils.logger import app_logger

class DataManager:
    def __init__(self, db_config=None):
        """Initialize with PostgreSQL database configuration"""
        if db_config is None:
            self.db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'port': os.environ.get('DB_PORT', '5432'),
                'database': os.environ.get('DB_NAME', 'pos_network'),
                'user': os.environ.get('DB_USER', 'admin'),
                'password': os.environ.get('DB_PASSWORD', 'admin')
            }
        else:
            self.db_config = db_config
    
    def create_backup(self, backup_path=None):
        """Create PostgreSQL database backup"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"backup_pos_{timestamp}.sql"
            
            # Use pg_dump to create backup
            import subprocess
            cmd = [
                'pg_dump',
                f"--host={self.db_config['host']}",
                f"--port={self.db_config['port']}",
                f"--username={self.db_config['user']}",
                f"--dbname={self.db_config['database']}",
                '--format=custom',
                '--no-password',
                f"--file={backup_path}"
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                app_logger.info(f"Backup created successfully: {backup_path}")
                return backup_path
            else:
                app_logger.error(f"Backup failed: {result.stderr}")
                return None
                
        except Exception as e:
            app_logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Restore PostgreSQL database from backup"""
        try:
            if not os.path.exists(backup_path):
                app_logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Use pg_restore to restore backup
            import subprocess
            cmd = [
                'pg_restore',
                f"--host={self.db_config['host']}",
                f"--port={self.db_config['port']}",
                f"--username={self.db_config['user']}",
                f"--dbname={self.db_config['database']}",
                '--clean',
                '--if-exists',
                '--no-password',
                backup_path
            ]
            
            # Set password environment variable
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                app_logger.info("Database restored successfully")
                return True
            else:
                app_logger.error(f"Restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            app_logger.error(f"Error restoring backup: {e}")
            return False
    
    def export_data(self, table_name, output_path):
        """Export table data to JSON file"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get all data from the table
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            # Get column names
            cursor.execute(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """)
            columns = [row[0] for row in cursor.fetchall()]
            
            # Convert to list of dictionaries
            data = []
            for row in rows:
                record = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Handle datetime objects
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    record[column] = value
                data.append(record)
            
            # Write to JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            cursor.close()
            conn.close()
            
            app_logger.info(f"Data exported successfully: {output_path}")
            return True
            
        except Exception as e:
            app_logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, table_name, input_path):
        """Import data from JSON file to table"""
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                return False
            
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get column names from first record
            columns = list(data[0].keys())
            
            # Clear existing data (optional - be careful!)
            # cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
            
            # Insert data
            for record in data:
                placeholders = ', '.join(['%s'] * len(columns))
                column_names = ', '.join(columns)
                values = [record[col] for col in columns]
                
                cursor.execute(
                    f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
                    values
                )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            app_logger.info(f"Data imported successfully: {input_path}")
            return True
            
        except Exception as e:
            app_logger.error(f"Error importing data: {e}")
            return False
    
    def validate_data(self, table_name, data):
        """Validate data before import"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Get table schema
            cursor.execute(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """)
            schema = {row[0]: {'type': row[1], 'nullable': row[2] == 'YES'} for row in cursor.fetchall()}
            
            # Validate each record
            for i, record in enumerate(data):
                for field, value in record.items():
                    if field not in schema:
                        raise ValueError(f"Invalid field: {field}")
                    
                    # Basic type checking
                    if value is None and not schema[field]['nullable']:
                        raise ValueError(f"Field {field} cannot be null")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            app_logger.error(f"Data validation failed: {e}")
            return False
    
    def get_table_list(self):
        """Get list of all tables in the database"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            cursor.close()
            conn.close()
            return tables
            
        except Exception as e:
            app_logger.error(f"Error getting table list: {e}")
            return []
    
    def verify_backup(self, backup_path):
        """Verify if a backup file is valid"""
        try:
            if not os.path.exists(backup_path):
                return False
            
            # For PostgreSQL custom format backups, we can use pg_restore --list
            import subprocess
            cmd = ['pg_restore', '--list', backup_path]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Check if essential tables are in the backup
                essential_tables = ['products', 'customers', 'sales', 'suppliers']
                backup_content = result.stdout.lower()
                
                for table in essential_tables:
                    if table not in backup_content:
                        app_logger.warning(f"Missing essential table in backup: {table}")
                        return False
                
                return True
            else:
                return False
                
        except Exception as e:
            app_logger.error(f"Error verifying backup: {e}")
            return False
