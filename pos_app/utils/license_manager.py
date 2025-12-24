import hashlib
import os
import platform
import uuid
from pathlib import Path
from PySide6.QtWidgets import QInputDialog, QMessageBox, QLineEdit

class LicenseManager:
    def __init__(self, app_name="POS_System"):
        self.app_name = app_name
        self.license_key = "yallahmaA1!23"  # Hardcoded license key
        self.license_file = self._get_license_file_path()
        self.current_pc_id = self._get_pc_id()

    def _get_license_file_path(self):
        """Get path to the license file in user's app data directory"""
        if platform.system() == "Windows":
            app_data = os.getenv('APPDATA')
            license_dir = os.path.join(app_data, self.app_name)
        else:  # Linux/Mac
            home = os.path.expanduser('~')
            license_dir = os.path.join(home, f".{self.app_name.lower()}")
        
        os.makedirs(license_dir, exist_ok=True)
        return os.path.join(license_dir, "license.dat")

    def _get_pc_id(self):
        """Generate a unique ID for the current PC"""
        # Get machine-specific identifiers
        try:
            # Get system UUID (works on most platforms)
            node = uuid.getnode()
            # Get machine name
            machine = platform.node()
            # Combine and hash
            unique_id = f"{node}-{machine}"
            return hashlib.sha256(unique_id.encode()).hexdigest()
        except Exception:
            # Fallback to a random UUID if we can't get system info
            return str(uuid.uuid4())

    def is_license_valid(self):
        """Check if the license is valid for this PC"""
        if not os.path.exists(self.license_file):
            return False
            
        try:
            with open(self.license_file, 'r') as f:
                saved_key, saved_pc_id = f.read().split('|')
                
            # Verify both the key and PC ID match
            return (saved_key == self.license_key and 
                    saved_pc_id == self.current_pc_id)
        except Exception:
            return False

    def activate_license(self, key):
        """Activate the license with the provided key"""
        if key == self.license_key:
            try:
                with open(self.license_file, 'w') as f:
                    f.write(f"{key}|{self.current_pc_id}")
                return True
            except Exception as e:
                QMessageBox.critical(None, "Error", f"Failed to save license: {str(e)}")
                return False
        return False

    def show_license_dialog(self, parent=None):
        """Show license activation dialog"""
        if self.is_license_valid():
            return True
            
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("License Activation")
        msg.setText("Please enter your license key to activate the software.")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        
        # Create and configure input dialog
        input_widget = QInputDialog(parent)
        input_widget.setWindowTitle("License Key")
        input_widget.setLabelText("Enter License Key:")
        input_widget.setTextEchoMode(QLineEdit.Password)
        
        while True:
            ok = input_widget.exec()
            if not ok:
                return False
                
            key = input_widget.textValue().strip()
            if self.activate_license(key):
                QMessageBox.information(parent, "Success", "License activated successfully!")
                return True
            else:
                retry = QMessageBox.critical(
                    parent,
                    "Invalid Key",
                    "The license key is invalid. Would you like to try again?",
                    QMessageBox.Retry | QMessageBox.Cancel
                )
                if retry != QMessageBox.Retry:
                    return False
