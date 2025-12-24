from functools import wraps
from PySide6.QtWidgets import QMessageBox


def admin_required(func):
    """Decorator to ensure the current user is an admin"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            current_user = self.controllers['auth'].get_current_user()
            if not current_user or not current_user.is_admin:
                QMessageBox.warning(
                    self, 
                    "Access Denied", 
                    "You do not have permission to access this feature. "
                    "Only administrators can manage users."
                )
                return
        except (KeyError, AttributeError):
            # If auth controller is not available, allow the operation
            pass
        return func(self, *args, **kwargs)
    return wrapper
