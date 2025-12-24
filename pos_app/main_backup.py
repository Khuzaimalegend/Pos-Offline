import sys
import os
import threading
import time
from datetime import datetime
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler, QtMsgType
import logging
import traceback

# BULLETPROOF INITIALIZATION - Initialize error handling first
try:
    from pos_app.utils.error_handler import BulletproofErrorHandler, safe_execute
    _error_handler = BulletproofErrorHandler()
    print("[BULLETPROOF] Error handler initialized")
except Exception as e:
    print(f"[BULLETPROOF] Could not initialize error handler: {e}")
    # Create fallback safe_execute
    def safe_execute(func, *args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[FALLBACK] Error in {func.__name__}: {e}")
            return None

# AUTO-SETUP - Run auto-setup for new systems
try:
    from pos_app.utils.auto_setup import run_auto_setup
    print("[BULLETPROOF] Running auto-setup for new system...")
    safe_execute(run_auto_setup)
    print("[BULLETPROOF] Auto-setup completed")
except Exception as e:
    print(f"[BULLETPROOF] Auto-setup error: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to Python path so we can import pos_app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from pos_app.views.main_window import MainWindow
from pos_app.views.login import LoginDialog
from pos_app.database.connection import Database
from pos_app.controllers.business_logic import BusinessController
from pos_app.utils.logger import app_logger

# Import error logger
try:
    from pos_app.utils.error_logger import error_logger, log_error, log_info
    ERROR_LOGGING_ENABLED = True
    log_info("Error logging system initialized", "STARTUP")
except Exception as e:
    ERROR_LOGGING_ENABLED = False
    print(f"Warning: Error logging not available: {e}")

# Global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    """Handle uncaught exceptions"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    print(f"\n{'='*80}")
    print("[ERROR] UNCAUGHT EXCEPTION")
    print(f"{'='*80}")
    print(error_msg)
    print(f"{'='*80}\n")
    
    if ERROR_LOGGING_ENABLED:
        log_error(exc_value, "UNCAUGHT_EXCEPTION", "MAIN")

# Set the exception handler
sys.excepthook = handle_exception


# Check if we're in network mode
NETWORK_MODE = os.environ.get('POS_NETWORK_MODE', '0') == '1'

def is_network_mode():
    """Return True if POS is configured for network mode (PostgreSQL)."""
    return os.environ.get('POS_NETWORK_MODE', '0') == '1'


def start_network_server():
    """Start the FastAPI network server in a separate thread"""
    try:
        # Skip if not in network mode
        if not is_network_mode():
            return True

        # Try to import and start the network server (optional feature)
        try:
            from pos_server import app
            import uvicorn

            print("Starting Network POS Server...")
            print("Server will be available at: http://localhost:8000")
            print("Access from other devices: http://[YOUR_IP]:8000")
            print("Database: PostgreSQL")
            print("Multi-terminal support enabled")

            # Start server in a separate thread
            def run_server():
                try:
                    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
                except Exception as e:
                    print(f"ERROR: Server error: {e}")

            server_thread = threading.Thread(target=run_server, daemon=True)
            server_thread.start()

            # Wait a moment for server to start
            time.sleep(2)
            print("Network server started successfully")
            return True
        except ImportError:
            # Network server module not available - single terminal mode
            return False

    except Exception as e:
        # Network server not started - single terminal mode
        return False

def setup_network_database():
    """Set up PostgreSQL database"""
    try:
        print("Setting up database...")
        print("[INFO] Using PostgreSQL database")
        print("")

        # PostgreSQL connection
        try:
            import psycopg2
            # Try to connect to PostgreSQL
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="admin",
                password="admin",
                database="postgres"
            )
            conn.close()
            
            # PostgreSQL is available, try to set up the database
            from setup_network_db import create_network_database
            if create_network_database():
                print("[OK] PostgreSQL network database connected successfully!")
                print("[OK] All terminals will share the same data")
                print("[OK] Database: pos_network")
                print("[OK] Connection: PostgreSQL @ localhost:5432")
                return True
            else:
                raise Exception("PostgreSQL database setup failed")
                
        except Exception as e:
            print(f"[ERROR] PostgreSQL connection failed: {e}")
            print("[ERROR] Please ensure:")
            print("  1. PostgreSQL is running")
            print("  2. Database 'pos_network' exists")
            print("  3. User 'admin' with password 'admin' has access")
            print("  4. psycopg2-binary is installed")
            return False

    except Exception as e:
        print(f"ERROR: Database setup error: {e}")
        return False

def setup_controllers(db):
    # Instantiate controllers for their respective views
    business = BusinessController(db.session)
    return {
        'inventory': business,
        'customers': business,
        'suppliers': business,
        'sales': business,
        'reports': business
    }

def setup_folders():
    """Create necessary folders for the application"""
    folders = ['logs', 'documents', 'backups', 'exports']
    for folder in folders:
        path = os.path.join(os.path.dirname(__file__), folder)
        if not os.path.exists(path):
            os.makedirs(path)

def create_necessary_folders():
    """Create necessary folders for the application"""
    folders = ['logs', 'documents', 'backups', 'exports']
    for folder in folders:
        path = os.path.join(os.path.dirname(__file__), folder)
        if not os.path.exists(path):
            os.makedirs(path)

def main():
    """Main application entry point with bulletproof error handling"""
    print("[BULLETPROOF] Starting POS application...")
    db = None
    
    try:
        # Create necessary folders
        create_necessary_folders()

        # Set up PostgreSQL database
        if not setup_network_database():
            print("ERROR: Cannot continue without database")
            return
        
        # Network server is optional for multi-terminal support
        try:
            start_network_server()
            print(" Multi-terminal support enabled")
        except Exception:
            # Single-terminal mode is perfectly fine for most users
            pass

        # Initialize database connection for the GUI
        try:
            from pos_app.database.connection import Database
            db = Database()  # PostgreSQL connection
        except Exception as e:
            print(f"ERROR: Failed to initialize database: {e}")
            return

        # Ensure an admin user exists
        from pos_app.models.database import User
        from pos_app.utils.auth import hash_password
        admin_user = db.session.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            admin = User(username='admin', password_hash=hash_password('admin'), full_name='Administrator', is_admin=True)
            db.session.add(admin)
            db.session.commit()
            
    except Exception as e:
        print(f"ERROR during initialization: {e}")
        if db:
            db.session.rollback()
        return

    try:
        # Check if demo data exists
        from pos_app.models.database import Product, Customer, Supplier
        product_count = db.session.query(Product).count()
        customer_count = db.session.query(Customer).count()
        supplier_count = db.session.query(Supplier).count()
        
        if product_count > 0 or customer_count > 0 or supplier_count > 0:
            print(f" Demo data loaded: {product_count} products, {customer_count} customers, {supplier_count} suppliers")
        else:
            print(" Starting with empty database - ready for production use")
    except Exception:
        print(" Database ready for use")

    try:
        # Setup controllers with error handling
        print("[BULLETPROOF] Setting up controllers...")
        controllers = safe_execute(setup_controllers, db)
        if not controllers:
            print("[BULLETPROOF] Controller setup failed")
            return

        # Initialize Qt Application with error handling
        print("[BULLETPROOF] Initializing Qt application...")
        app = safe_execute(QApplication, sys.argv)
        if not app:
            print("[BULLETPROOF] Qt application initialization failed")
            return
            
        # Install Qt message handler to suppress CSS warnings
        def qt_message_handler(mode, context, message):
            # Suppress CSS property warnings
            if any(warning in message.lower() for warning in [
                'unknown property', 'text-shadow', 'box-shadow', 'transform',
                'border-image', 'background-clip', 'filter'
            ]):
                return  # Ignore these warnings
            
            # Allow other important messages through
            if mode == QtMsgType.QtCriticalMsg or mode == QtMsgType.QtFatalMsg:
                print(f"Qt {mode.name}: {message}")
        
        safe_execute(qInstallMessageHandler, qt_message_handler)
        
        # Apply clean stylesheet to avoid Qt CSS warnings
        try:
            from pos_app.utils.clean_styles import CLEAN_GLOBAL_STYLESHEET
            safe_execute(app.setStyleSheet, CLEAN_GLOBAL_STYLESHEET)
            print(" Clean stylesheet loaded with CSS warning suppression")
        except Exception as e:
            print(f"WARNING: Could not load clean stylesheet: {e}")
            print("Using minimal styling to avoid CSS warnings")

        # Create main window with error handling
        print("[BULLETPROOF] Creating main window...")
        window = safe_execute(MainWindow, controllers)
        if not window:
            print("[BULLETPROOF] Main window creation failed")
            return
            
        # Apply UI auditor if available
        try:
            from pos_app.utils.ui_auditor import UIAuditor
            safe_execute(UIAuditor.apply_to, window)
        except Exception as e:
            print(f"WARNING: Could not apply UI auditor: {e}")

        # Start in fullscreen mode with error handling
        print("[BULLETPROOF] Starting application...")
        safe_execute(window.showFullScreen)
        
        # Run application event loop
        exit_code = safe_execute(app.exec)
        print(f"[BULLETPROOF] Application exited with code: {exit_code}")
        sys.exit(exit_code or 0)
        
    except Exception as e:
        print(f"[BULLETPROOF] Critical error in main: {e}")
        print(f"[BULLETPROOF] Traceback: {traceback.format_exc()}")
        
        # Try to show error dialog if possible
        try:
            from PySide6.QtWidgets import QMessageBox, QApplication
            if not QApplication.instance():
                app = QApplication(sys.argv)
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("POS System Error")
            msg.setText("A critical error occurred during startup.")
            msg.setDetailedText(str(e))
            msg.exec()
        except:
            print("[BULLETPROOF] Could not show error dialog")
        
        sys.exit(1)

def create_main_window():
    """Create and return the main window for external startup scripts"""
    try:
        # Setup database connection
        from pos_app.database.connection import Database
        db = Database()
        
        # Setup controllers
        controllers = setup_controllers(db)
        
        # Create main window
        window = MainWindow(controllers)
        
        # Apply UI auditor if available
        try:
            from pos_app.utils.ui_auditor import UIAuditor
            UIAuditor.apply_to(window)
        except Exception as e:
            print(f"WARNING: Could not apply UI auditor: {e}")
        
        return window
        
    except Exception as e:
        print(f"Error creating main window: {e}")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
