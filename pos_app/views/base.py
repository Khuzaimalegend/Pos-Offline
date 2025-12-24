try:
    from PySide6.QtWidgets import QWidget
except ImportError:
    from PyQt6.QtWidgets import QWidget

class BaseView(QWidget):
    """Base view class that all other views should inherit from.

    Accepts either a QWidget parent or a controller object as the first arg for
    backwards compatibility with views that pass the controller positionally.
    """

    def __init__(self, controller_or_parent=None, parent=None):
        # If the first arg is not a QWidget, assume it's a controller
        if parent is None and controller_or_parent is not None and not isinstance(controller_or_parent, QWidget):
            try:
                self.controller = controller_or_parent
            except Exception:
                pass
            parent = None
        super().__init__(parent)
        # Subclasses are responsible for calling setup_ui() after their own init
    
    def setup_ui(self):
        """Setup the UI components. Should be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement setup_ui()")
