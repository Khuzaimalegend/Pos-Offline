try:
    from PySide6.QtWidgets import QLabel
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import QLabel
    from PyQt6.QtCore import Qt

class StatusBar(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QLabel {
                background-color: #0b1220; /* match dark cards */
                border-top: 1px solid #1f2937;
                padding: 5px 10px;
                color: #cbd5e1; /* slate-300 for readability on dark */
            }
        """)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setText("Ready")
