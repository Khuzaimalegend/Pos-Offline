import sys
import os

# Import qt_compat FIRST to patch Qt enums for PyQt6 compatibility
try:
    # Try absolute import first
    import qt_compat
except ImportError:
    try:
        # Try from pos_app package
        from pos_app import qt_compat
    except ImportError:
        print("[ERROR] Could not import qt_compat - ensure qt_compat.py exists in pos_app directory")
        raise

import threading
import time
from datetime import datetime
try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import qInstallMessageHandler, QtMsgType
except ImportError:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
import logging
# Ensure console can print Unicode on Windows cmd
try:
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
    sys.stderr.reconfigure(encoding='utf-8', errors='ignore')
except Exception:
    pass
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to Python path so we can import pos_app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from pos_app.views.main_window import MainWindow
from pos_app.controllers.business_logic import BusinessController
from pos_app.utils.logger import app_logger
from pos_app.utils.network_manager import bootstrap_database_config, set_server_mode, set_client_mode
from pos_app.utils.license_manager import LicenseManager
from pos_app.utils.startup_validator import StartupValidator

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


def _install_dialog_auto_fit(app: QApplication):
    try:
        try:
            from PySide6.QtCore import QObject, QEvent
            from PySide6.QtWidgets import QDialog
        except ImportError:
            from PyQt6.QtCore import QObject, QEvent
            from PyQt6.QtWidgets import QDialog

        class _DialogAutoFitFilter(QObject):
            def eventFilter(self, obj, event):
                try:
                    if not isinstance(obj, QDialog):
                        return False

                    try:
                        t = event.type()
                    except Exception:
                        return False

                    try:
                        show_t = QEvent.Type.Show
                    except Exception:
                        show_t = getattr(QEvent, 'Show', None)

                    if show_t is None or t != show_t:
                        return False

                    # Only apply once per dialog instance
                    try:
                        if bool(obj.property('_auto_fit_done')):
                            return False
                    except Exception:
                        pass

                    try:
                        obj.setProperty('_auto_fit_done', True)
                    except Exception:
                        pass

                    try:
                        scr = obj.screen() if hasattr(obj, 'screen') else None
                        if scr is None and hasattr(app, 'primaryScreen'):
                            scr = app.primaryScreen()
                        if scr is None:
                            return False

                        geo = scr.availableGeometry()

                        # Ensure dialog is not forced fullscreen/maximized
                        try:
                            obj.showNormal()
                        except Exception:
                            pass

                        # Let layouts compute a natural size first
                        try:
                            obj.adjustSize()
                        except Exception:
                            pass

                        # Cap size to 80% of available screen
                        try:
                            max_w = int(geo.width() * 0.8)
                            max_h = int(geo.height() * 0.8)
                        except Exception:
                            max_w = geo.width()
                            max_h = geo.height()

                        try:
                            w = obj.width()
                            h = obj.height()
                            # Keep natural size; only clamp down if too large
                            if w > max_w or h > max_h:
                                obj.resize(min(w, max_w), min(h, max_h))
                        except Exception:
                            pass

                        # Center dialog on screen
                        try:
                            x = geo.x() + (geo.width() - obj.width()) // 2
                            y = geo.y() + (geo.height() - obj.height()) // 2
                            obj.move(x, y)
                        except Exception:
                            pass

                        # Re-run layout after resize
                        try:
                            obj.updateGeometry()
                        except Exception:
                            pass
                    except Exception:
                        return False

                except Exception:
                    return False

                return False

        f = _DialogAutoFitFilter(app)
        app.installEventFilter(f)
        try:
            app._dialog_auto_fit_filter = f
        except Exception:
            pass
    except Exception:
        return


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

def main():
    db = None
    try:
        app_mode = 'server'
        # Create necessary folders
        setup_folders()

        # Bootstrap with app_config.json
        try:
            import json
            from pos_app.models.database import update_db_config
            
            # Determine config path - try multiple locations
            # 1. Same directory as executable (for packaged EXE)
            # 2. pos_app/config directory (for development)
            exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            config_path_exe = os.path.join(exe_dir, 'app_config.json')
            config_path_dev = os.path.join(os.path.dirname(__file__), 'config', 'app_config.json')
            
            # Use exe directory if running as packaged app
            if getattr(sys, 'frozen', False):
                config_path = config_path_exe
            else:
                config_path = config_path_dev
            
            app_config = {
                'use_static_ip': False,
                'static_ip': 'localhost',
                'mode': 'server'
            }
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        app_config = json.load(f)
                    print(f"[BOOTSTRAP] Loaded app_config.json: mode={app_config.get('mode')}, use_static_ip={app_config.get('use_static_ip')}")
                except Exception as e:
                    print(f"[BOOTSTRAP] Error reading app_config.json: {e}, using defaults")
            else:
                print(f"[BOOTSTRAP] app_config.json not found at {config_path}, creating with defaults")
                # Create config file with defaults
                try:
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    with open(config_path, 'w', encoding='utf-8') as f:
                        json.dump(app_config, f, indent=2)
                    print(f"[BOOTSTRAP] Created app_config.json at {config_path}")
                except Exception as e:
                    print(f"[BOOTSTRAP] Error creating app_config.json: {e}")
            
            # Determine host based on config
            mode = app_config.get('mode', 'server').lower()
            app_mode = mode
            use_static_ip = app_config.get('use_static_ip', False)
            static_ip = app_config.get('static_ip', 'localhost')
            
            if use_static_ip and static_ip:
                host = static_ip
                print(f"[BOOTSTRAP] Using static IP: {host}")
            else:
                host = 'localhost'
                print(f"[BOOTSTRAP] Using localhost (static_ip disabled)")
            
            # Configure based on mode
            if mode == 'server':
                print(f"[BOOTSTRAP] Configuring as SERVER mode")
                update_db_config(
                    host=host,
                    port='5432',
                    database='pos_network',
                    username='admin',
                    password='admin'
                )
            elif mode == 'client':
                print(f"[BOOTSTRAP] Configuring as CLIENT mode")
                update_db_config(
                    host=host,
                    port='5432',
                    database='pos_network',
                    username='admin',
                    password='admin'
                )
                # Product cache will be done after DB session is created (below), using that live session.
            else:
                print(f"[BOOTSTRAP] Unknown mode '{mode}', defaulting to server")
                update_db_config(
                    host=host,
                    port='5432',
                    database='pos_network',
                    username='admin',
                    password='admin'
                )
        except Exception as e:
            print(f"[BOOTSTRAP] Error during bootstrap: {e}")
            # Fallback to localhost
            try:
                from pos_app.models.database import update_db_config
                update_db_config(
                    host="localhost",
                    port="5432",
                    database="pos_network",
                    username="admin",
                    password="admin"
                )
            except Exception as e2:
                print(f"[BOOTSTRAP] Error setting fallback config: {e2}")

        # Initialize database connection for the GUI
        from pos_app.database.connection import Database
        db = Database()  # PostgreSQL connection
        
        if db._is_offline:
            print("[WARN] Application will run in OFFLINE MODE")
        else:
            print("[SUCCESS] Database connection established")

            # Client machines: after connecting, download products and cache locally for offline use.
            try:
                if str(app_mode or '').lower() == 'client':
                    from pos_app.data.products import cache_products_from_session
                    cache_products_from_session(db.session)
                    print("[BOOTSTRAP] Cached products to client machine for offline use")
            except Exception as e:
                print(f"[BOOTSTRAP] Warning: could not cache products on client: {e}")

        # Run startup validation and auto-recovery BEFORE login dialog
        if not db._is_offline:
            try:
                print("[STARTUP] Running pre-login database validation...")
                if not StartupValidator.run_full_startup_check(db.session):
                    print("[WARN] Startup validation had issues but continuing...")
            except Exception as e:
                print(f"[WARN] Startup validation error: {e}")
        
        # Ensure an admin user exists (skip if offline)
        if not db._is_offline:
            try:
                from pos_app.models.database import User, Base
                from pos_app.utils.auth import hash_password
                
                # Create tables if they don't exist
                try:
                    Base.metadata.create_all(db.engine)
                except Exception as e:
                    print(f"[WARN] Could not create tables: {e}")
                
                admin_user = db.session.query(User).filter(User.username == 'admin').first()
                if not admin_user:
                    admin = User(
                        username='admin',
                        password_hash=hash_password('admin'),
                        full_name='Administrator',
                        is_admin=True,
                        is_active=True
                    )
                    db.session.add(admin)
                    db.session.commit()
                    print("[SUCCESS] Created default admin user (username: admin, password: admin)")
            except Exception as e:
                print(f"[WARN] Could not ensure admin user exists: {e}")
    except Exception as e:
        print(f"ERROR during initialization: {e}")
        if db:
            db.session.rollback()
        return

    # Skip demo data seeding on startup for speed - load only when needed
    if not db._is_offline:
        print("[STARTUP] Database ready - demo data will load on-demand")
    else:
        print("[OFFLINE] Database is offline")

    # Setup controllers
    controllers = setup_controllers(db)

    # Initialize Qt Application (or get existing instance)
    app = QApplication.instance() or QApplication(sys.argv)
    try:
        _install_dialog_auto_fit(app)
    except Exception:
        pass
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
    
    qInstallMessageHandler(qt_message_handler)
    
    # Apply clean stylesheet to avoid Qt CSS warnings
    try:
        from pos_app.utils.clean_styles import CLEAN_GLOBAL_STYLESHEET
        app.setStyleSheet(CLEAN_GLOBAL_STYLESHEET)
        print("✅ Clean stylesheet loaded with CSS warning suppression")
    except Exception as e:
        print(f"WARNING: Could not load clean stylesheet: {e}")
        # Don't use fallback stylesheet as it contains problematic CSS
        print("Using minimal styling to avoid CSS warnings")

    login_dialog = LoginDialog()
    if login_dialog.exec() == LoginDialog.Accepted:
        # User logged in successfully
        
        # Check PostgreSQL installation and setup
        try:
            from pos_app.views.postgres_setup import is_postgresql_installed, is_database_available, PostgreSQLSetupDialog
            
            # Only check if database is not already available (to avoid data loss)
            if not is_database_available():
                if not is_postgresql_installed():
                    print("[POSTGRESQL] PostgreSQL not found, showing setup dialog...")
                    setup_dialog = PostgreSQLSetupDialog()
                    if setup_dialog.exec() == PostgreSQLSetupDialog.Accepted:
                        print("[POSTGRESQL] Setup completed, reinitializing database connection...")
                        # Reinitialize database connection after setup
                        from pos_app.database.connection import Database
                        db = Database()
                        if not db._is_offline:
                            print("[SUCCESS] Database connection re-established after PostgreSQL setup")
                        else:
                            QMessageBox.warning(None, "Database Issue", 
                                              "PostgreSQL setup completed but database connection failed. Please restart the application.")
                            sys.exit(1)
                    else:
                        print("[POSTGRESQL] Setup cancelled by user")
                        QMessageBox.information(None, "Setup Cancelled", 
                                              "PostgreSQL setup was cancelled. The application will exit.")
                        sys.exit(0)
                else:
                    print("[POSTGRESQL] PostgreSQL found but database not set up, will use existing setup")
            else:
                print("[POSTGRESQL] Database already available, skipping setup")
                
        except Exception as e:
            print(f"[POSTGRESQL] Setup check failed: {e}")
            # Continue anyway - maybe database is already working
        
        # Store logged-in user in controllers if auth controller exists
        try:
            if 'auth' in controllers and hasattr(login_dialog.user, 'username'):
                controllers['auth'].current_user = login_dialog.user
        except Exception as e:
            print(f"WARNING: Could not store user in controllers: {e}")

        # Check if user is admin, if not switch to client mode
        try:
            current_user = login_dialog.user
            if hasattr(current_user, 'is_admin') and not current_user.is_admin:
                # Get server IP from config or use localhost as fallback
                network_config = read_network_config()
                server_ip = network_config.get('server_ip', 'localhost')
                port = network_config.get('port', '5432')
                # Set client mode with current server details
                set_client_mode(server_ip, port)
                print(f"Switched to client mode for non-admin user: {current_user.username}")

                # After switching config to client mode, cache products for offline use.
                try:
                    from pos_app.data.products import cache_products_from_session
                    # Use the existing controller session if available
                    sess = None
                    try:
                        if isinstance(controllers, dict):
                            for _n, c in controllers.items():
                                if hasattr(c, 'session') and getattr(c, 'session', None) is not None:
                                    sess = c.session
                                    break
                    except Exception:
                        sess = None
                    if sess is not None:
                        cache_products_from_session(sess)
                except Exception:
                    pass
        except Exception as e:
            print(f"WARNING: Could not switch to client mode: {e}")
        
        # Create window with the logged-in user
        window = MainWindow(controllers, login_dialog.user)
        
        try:
            from pos_app.utils.ui_auditor import UIAuditor
            UIAuditor.apply_to(window)
        except Exception as e:
            print(f"WARNING: Could not apply UI auditor: {e}")

        window.show()
        sys.exit(app.exec())
    else:
        # User cancelled login
        print("Login cancelled. Exiting application.")
        sys.exit(0)

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

def check_license(app):
    """Check and validate the application license"""
    license_mgr = LicenseManager()
    
    if not license_mgr.is_license_valid():
        if not license_mgr.show_license_dialog():
            QMessageBox.critical(None, "License Required", 
                               "A valid license is required to run this application.")
            return False
    return True

if __name__ == "__main__":
    # Create application instance
    app = QApplication(sys.argv)
    try:
        _install_dialog_auto_fit(app)
    except Exception:
        pass
    
    # Check license
    if not check_license(app):
        sys.exit(1)
        
    # If license is valid, proceed with main application
    main()
                