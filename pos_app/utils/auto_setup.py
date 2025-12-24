
import os
import sys
import json
import subprocess
from pos_app.utils.error_handler import safe_execute
from pos_app.utils.ip_scanner import IPScanner

class AutoSetup:
    def __init__(self):
        self.config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        self.ensure_config_dir()
    
    def ensure_config_dir(self):
        """Ensure config directory exists"""
        os.makedirs(self.config_dir, exist_ok=True)
    
    def setup_for_new_system(self):
        """Complete setup for brand new system"""
        print("[AutoSetup] Setting up POS for new system...")
        
        # Step 1: Check dependencies
        self.check_dependencies()
        
        # Step 2: Scan for PostgreSQL servers
        server_config = self.find_postgresql_server()
        
        # Step 3: Create database configuration
        self.create_database_config(server_config)
        
        # Step 4: Test database connection
        self.test_database_connection()
        
        # Step 5: Initialize database if needed
        self.initialize_database()
        
        print("[AutoSetup] Setup complete!")
    
    def check_dependencies(self):
        """Check and handle missing dependencies"""
        print("[AutoSetup] Checking dependencies...")
        
        # Check psycopg2
        try:
            import psycopg2
            print("[AutoSetup] ✅ psycopg2 available")
        except ImportError:
            print("[AutoSetup] ❌ psycopg2 missing - POS will work with limited functionality")
        
        # Check PySide6
        try:
            import PySide6
            print("[AutoSetup] ✅ PySide6 available")
        except ImportError:
            print("[AutoSetup] ❌ PySide6 missing - This should not happen in exe")
    
    def find_postgresql_server(self):
        """Find PostgreSQL server on network"""
        print("[AutoSetup] Searching for PostgreSQL servers...")
        
        scanner = IPScanner()
        
        # First try quick scan
        quick_result = scanner.quick_scan_common_ips()
        if quick_result:
            return quick_result
        
        # If no quick result, do full scan
        print("[AutoSetup] No servers found in quick scan, doing full scan 1-150...")
        found_servers = scanner.scan_network_range(1, 150)
        
        if found_servers:
            best_server = scanner.get_best_server()
            print(f"[AutoSetup] ✅ Using PostgreSQL server: {best_server['ip']}")
            return best_server
        
        # No network server found, use localhost
        print("[AutoSetup] No network PostgreSQL found, using localhost")
        return {
            'ip': 'localhost',
            'status': 'localhost_fallback',
            'username': 'admin',
            'password': 'admin'
        }
    
    def create_database_config(self, server_config):
        """Create database configuration"""
        config = {
            "username": server_config['username'],
            "password": server_config['password'],
            "host": server_config['ip'],
            "port": "5432",
            "database": "pos_network",
            "connection_settings": {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "connect_timeout": 10
            },
            "auto_setup": {
                "server_found": server_config['status'],
                "scan_date": datetime.now().isoformat(),
                "fallback_mode": server_config['status'] == 'localhost_fallback'
            },
            "description": f"Auto-configured for {server_config['ip']} - {server_config['status']}"
        }
        
        config_path = os.path.join(self.config_dir, 'database.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        print(f"[AutoSetup] ✅ Database config created: {server_config['ip']}:5432")
    
    def test_database_connection(self):
        """Test database connection"""
        try:
            from pos_app.models.database import get_database_url
            from sqlalchemy import create_engine, text
            
            db_url = get_database_url()
            engine = create_engine(db_url)
            
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            print("[AutoSetup] ✅ Database connection test successful")
            return True
            
        except Exception as e:
            print(f"[AutoSetup] ❌ Database connection failed: {e}")
            return False
    
    def initialize_database(self):
        """Initialize database tables if needed"""
        try:
            from pos_app.models.database import Base, engine
            
            # Create all tables
            Base.metadata.create_all(engine)
            print("[AutoSetup] ✅ Database tables initialized")
            
        except Exception as e:
            print(f"[AutoSetup] Database initialization error: {e}")

# Auto-setup on import
def run_auto_setup():
    """Run auto-setup if needed"""
    try:
        setup = AutoSetup()
        setup.setup_for_new_system()
    except Exception as e:
        print(f"[AutoSetup] Setup failed: {e}")
        # Continue anyway - don't crash
