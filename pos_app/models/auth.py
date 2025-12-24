import hashlib
import secrets

class User:
    def __init__(self, username, password_hash, role):
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def hash_password(password):
        """Hash password using built-in hashlib (no external dependencies)"""
        # Generate a random salt
        salt = secrets.token_hex(16)
        # Hash password with salt
        pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return f"{salt}:{pwd_hash}".encode('utf-8')

    def check_password(self, password):
        """Check password against hash using built-in hashlib"""
        try:
            if isinstance(self.password_hash, bytes):
                hash_str = self.password_hash.decode('utf-8')
            else:
                hash_str = self.password_hash
                
            if ':' not in hash_str:
                return False
            salt, stored_hash = hash_str.split(':', 1)
            pwd_hash = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
            return pwd_hash == stored_hash
        except Exception:
            return False

class Role:
    ADMIN = "admin"
    MANAGER = "manager"
    CASHIER = "cashier"
    
    @staticmethod
    def get_permissions(role):
        permissions = {
            Role.ADMIN: [
                "manage_users",
                "manage_inventory",
                "manage_customers",
                "manage_suppliers",
                "manage_sales",
                "view_reports",
                "manage_settings"
            ],
            Role.MANAGER: [
                "manage_inventory",
                "manage_customers",
                "manage_suppliers",
                "manage_sales",
                "view_reports"
            ],
            Role.CASHIER: [
                "make_sale",
                "view_inventory",
                "view_customers"
            ]
        }
        return permissions.get(role, [])
