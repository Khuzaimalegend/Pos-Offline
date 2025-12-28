import subprocess
import sys
import os

try:
    from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QTextEdit
    from PySide6.QtCore import Qt, QThread, Signal
except ImportError:
    from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox, QTextEdit
    from PyQt6.QtCore import Qt, QThread, Signal

def is_postgresql_installed():
    """Check if PostgreSQL is installed and accessible"""
    try:
        # Try to run pg_isready or psql to check if PostgreSQL is running
        result = subprocess.run(['pg_isready'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    try:
        # Try alternative check with psql
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    return False

def is_database_available():
    """Check if the pos_network database and admin user exist"""
    try:
        from pos_app.database.connection import Database
        db = Database()
        if not db._is_offline:
            # Test if we can connect and if admin user exists
            from pos_app.models.database import User
            admin_user = db.session.query(User).filter(User.username == 'admin').first()
            return admin_user is not None
    except Exception:
        pass
    return False

class PostgreSQLInstaller(QThread):
    """Thread to handle PostgreSQL installation"""
    progress = Signal(str)
    finished = Signal(bool, str)

    def run(self):
        try:
            self.progress.emit("Starting PostgreSQL installation...")

            # Check if running on Windows
            if os.name != 'nt':
                self.finished.emit(False, "PostgreSQL auto-installation is only supported on Windows")
                return

            # Download and install PostgreSQL
            self.progress.emit("Downloading PostgreSQL installer...")

            # For Windows, we'll use a simple approach - try to install via winget or chocolatey
            install_commands = [
                ['winget', 'install', '--id', 'PostgreSQL.PostgreSQL', '--version', '15.4', '--accept-source-agreements', '--accept-package-agreements'],
                ['choco', 'install', 'postgresql', '--version=15.4', '-y'],
                # Fallback - try to download and run installer manually
            ]

            success = False
            for cmd in install_commands:
                try:
                    self.progress.emit(f"Trying installation method: {' '.join(cmd[:2])}")
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        success = True
                        break
                    else:
                        self.progress.emit(f"Method failed: {result.stderr}")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            if not success:
                self.finished.emit(False, "Could not install PostgreSQL automatically. Please install it manually.")
                return

            self.progress.emit("PostgreSQL installed successfully. Starting service...")

            # Start PostgreSQL service
            try:
                subprocess.run(['net', 'start', 'postgresql-x64-15'], capture_output=True, timeout=30)
            except:
                pass  # Service might already be running

            # Wait for PostgreSQL to start
            import time
            time.sleep(5)

            self.progress.emit("Creating database and user...")

            # Create database and user
            try:
                # Use psql to create database and user
                sql_commands = [
                    "CREATE DATABASE pos_network;",
                    "CREATE USER admin WITH PASSWORD 'admin';",
                    "GRANT ALL PRIVILEGES ON DATABASE pos_network TO admin;",
                    "ALTER USER admin CREATEDB;"
                ]

                for sql in sql_commands:
                    cmd = ['psql', '-U', 'postgres', '-c', sql]
                    result = subprocess.run(cmd, capture_output=True, text=True, input='postgres\n')
                    if result.returncode != 0:
                        self.progress.emit(f"Warning: {sql} failed: {result.stderr}")

                self.progress.emit("Database setup completed successfully!")
                self.finished.emit(True, "PostgreSQL installed and configured successfully!")

            except Exception as e:
                self.finished.emit(False, f"Database setup failed: {str(e)}")

        except Exception as e:
            self.finished.emit(False, f"Installation failed: {str(e)}")

class PostgreSQLSetupDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PostgreSQL Setup Required")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("🚫 PostgreSQL Not Found")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #dc2626; margin-bottom: 10px;")
        layout.addWidget(title)

        # Message
        message = QLabel(
            "PostgreSQL database server is required to run this application, but it is not installed on this system.\n\n"
            "Would you like to install PostgreSQL automatically? This will:\n"
            "• Download and install PostgreSQL 15.4\n"
            "• Create the 'pos_network' database\n"
            "• Create an 'admin' user with password 'admin'\n\n"
            "⚠️ Note: This process may take several minutes and requires administrator privileges."
        )
        message.setWordWrap(True)
        message.setStyleSheet("font-size: 12px; color: #374151; margin-bottom: 20px;")
        layout.addWidget(message)

        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Progress text
        self.progress_text = QLabel("")
        self.progress_text.setStyleSheet("font-size: 11px; color: #6b7280;")
        self.progress_text.setVisible(False)
        layout.addWidget(self.progress_text)

        # Log output
        self.log_text = QTextEdit()
        self.log_text.setVisible(False)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("font-family: monospace; font-size: 10px;")
        layout.addWidget(self.log_text)

        # Buttons
        button_layout = QVBoxLayout()

        install_btn = QPushButton("✅ Install PostgreSQL")
        install_btn.setMinimumHeight(40)
        install_btn.clicked.connect(self.start_installation)
        button_layout.addWidget(install_btn)

        manual_btn = QPushButton("📖 Install Manually")
        manual_btn.setMinimumHeight(40)
        manual_btn.clicked.connect(self.show_manual_instructions)
        button_layout.addWidget(manual_btn)

        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

        self.installer = None

    def start_installation(self):
        """Start the PostgreSQL installation process"""
        self.progress_bar.setVisible(True)
        self.progress_text.setVisible(True)
        self.log_text.setVisible(True)

        self.installer = PostgreSQLInstaller()
        self.installer.progress.connect(self.update_progress)
        self.installer.finished.connect(self.installation_finished)
        self.installer.start()

    def update_progress(self, message):
        """Update progress display"""
        self.progress_text.setText(message)
        self.log_text.append(message)

    def installation_finished(self, success, message):
        """Handle installation completion"""
        self.progress_bar.setVisible(False)
        self.progress_text.setText(message)

        if success:
            QMessageBox.information(self, "Success", message)
            self.accept()
        else:
            QMessageBox.warning(self, "Installation Failed", message)

    def show_manual_instructions(self):
        """Show manual installation instructions"""
        instructions = """
PostgreSQL Manual Installation Instructions:

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Install PostgreSQL with default settings
3. During installation, set password for 'postgres' user
4. After installation, create database and user:

   Open pgAdmin or command prompt and run:
   CREATE DATABASE pos_network;
   CREATE USER admin WITH PASSWORD 'admin';
   GRANT ALL PRIVILEGES ON DATABASE pos_network TO admin;

5. Restart the application

For detailed instructions, visit: https://www.postgresql.org/docs/current/tutorial-install.html
        """

        QMessageBox.information(self, "Manual Installation", instructions)
