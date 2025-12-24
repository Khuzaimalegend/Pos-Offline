"""
Cash Register Dialog - Open/Close Register with Cash Counting
"""
try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QTextEdit, QGroupBox, QGridLayout, QSpinBox,
        QDoubleSpinBox, QMessageBox, QFormLayout
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QTextEdit, QGroupBox, QGridLayout, QSpinBox,
        QDoubleSpinBox, QMessageBox, QFormLayout
    )
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
from datetime import datetime
from decimal import Decimal

class CashRegisterDialog(QDialog):
    """Dialog for opening/closing cash register"""
    
    def __init__(self, mode='open', session_data=None, parent=None):
        super().__init__(parent)
        self.mode = mode  # 'open' or 'close'
        self.session_data = session_data or {}
        
        self.setWindowTitle("Open Cash Register" if mode == 'open' else "Close Cash Register")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🏦 Open Cash Register" if self.mode == 'open' else "🔒 Close Cash Register")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        layout.addWidget(title)
        
        if self.mode == 'open':
            self.setup_open_mode(layout)
        else:
            self.setup_close_mode(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Open Register" if self.mode == 'open' else "Close Register")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: Qt.white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        self.save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: #64748b;
                color: Qt.white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #475569;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.save_btn)
        
        layout.addLayout(button_layout)
    
    def setup_open_mode(self, layout):
        """Setup UI for opening register"""
        # Opening balance
        form_layout = QFormLayout()
        
        self.opening_balance = QDoubleSpinBox()
        self.opening_balance.setRange(0, 10000000)
        self.opening_balance.setDecimals(2)
        self.opening_balance.setPrefix("Rs ")
        self.opening_balance.setValue(0.0)
        self.opening_balance.setStyleSheet("font-size: 16px; padding: 8px;")
        
        form_layout.addRow("Opening Balance:", self.opening_balance)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        self.notes.setPlaceholderText("Optional notes...")
        form_layout.addRow("Notes:", self.notes)
        
        layout.addLayout(form_layout)
    
    def setup_close_mode(self, layout):
        """Setup UI for closing register with cash counting"""
        # Session info
        info_group = QGroupBox("Session Information")
        info_layout = QFormLayout()
        
        opened_at = self.session_data.get('opened_at', datetime.now())
        opening_balance = self.session_data.get('opening_balance', 0.0)
        
        info_layout.addRow("Opened:", QLabel(opened_at.strftime("%Y-%m-%d %H:%M")))
        info_layout.addRow("Opening Balance:", QLabel(f"Rs {opening_balance:,.2f}"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Expected balance
        expected_group = QGroupBox("Expected Balance")
        expected_layout = QVBoxLayout()
        
        expected_balance = self.session_data.get('expected_balance', 0.0)
        self.expected_label = QLabel(f"Rs {expected_balance:,.2f}")
        self.expected_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        expected_layout.addWidget(self.expected_label)
        
        expected_group.setLayout(expected_layout)
        layout.addWidget(expected_group)
        
        # Cash counting
        counting_group = QGroupBox("💵 Count Cash in Drawer")
        counting_layout = QGridLayout()
        
        # Denomination counters
        self.denominations = {
            5000: QSpinBox(),
            1000: QSpinBox(),
            500: QSpinBox(),
            100: QSpinBox(),
            50: QSpinBox(),
            20: QSpinBox(),
            10: QSpinBox(),
            5: QSpinBox(),
            2: QSpinBox(),
            1: QSpinBox(),
        }
        
        row = 0
        for denom, spinbox in self.denominations.items():
            spinbox.setRange(0, 10000)
            spinbox.setValue(0)
            spinbox.valueChanged.connect(self.calculate_total)
            
            label = QLabel(f"Rs {denom}:")
            label.setStyleSheet("font-weight: bold;")
            counting_layout.addWidget(label, row, 0)
            counting_layout.addWidget(spinbox, row, 1)
            
            # Amount label
            amount_label = QLabel("Rs 0.00")
            amount_label.setObjectName(f"amount_{denom}")
            counting_layout.addWidget(amount_label, row, 2)
            
            row += 1
        
        counting_group.setLayout(counting_layout)
        layout.addWidget(counting_group)
        
        # Total counted
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Total Counted:"))
        self.total_counted_label = QLabel("Rs 0.00")
        self.total_counted_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        total_layout.addWidget(self.total_counted_label)
        total_layout.addStretch()
        layout.addLayout(total_layout)
        
        # Variance
        variance_layout = QHBoxLayout()
        variance_layout.addWidget(QLabel("Variance:"))
        self.variance_label = QLabel("Rs 0.00")
        self.variance_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        variance_layout.addWidget(self.variance_label)
        variance_layout.addStretch()
        layout.addLayout(variance_layout)
        
        # Notes
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Notes about variance or issues...")
        layout.addWidget(QLabel("Notes:"))
        layout.addWidget(self.notes)
    
    def calculate_total(self):
        """Calculate total cash counted"""
        total = 0.0
        for denom, spinbox in self.denominations.items():
            count = spinbox.value()
            amount = denom * count
            total += amount
            
            # Update amount label
            amount_label = self.findChild(QLabel, f"amount_{denom}")
            if amount_label:
                amount_label.setText(f"Rs {amount:,.2f}")
        
        self.total_counted_label.setText(f"Rs {total:,.2f}")
        
        # Calculate variance
        expected = self.session_data.get('expected_balance', 0.0)
        variance = total - expected
        
        self.variance_label.setText(f"Rs {variance:,.2f}")
        
        # Color code variance
        if variance > 0:
            self.variance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")  # Green (over)
        elif variance < 0:
            self.variance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ef4444;")  # Red (short)
        else:
            self.variance_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #64748b;")  # Gray (exact)
    
    def get_data(self):
        """Get dialog data"""
        if self.mode == 'open':
            return {
                'opening_balance': Decimal(str(self.opening_balance.value())),
                'notes': self.notes.toPlainText().strip() or None
            }
        else:
            # Calculate total
            total = sum(denom * spinbox.value() for denom, spinbox in self.denominations.items())
            expected = self.session_data.get('expected_balance', 0.0)
            variance = total - expected
            
            return {
                'closing_balance': Decimal(str(total)),
                'expected_balance': Decimal(str(expected)),
                'variance': Decimal(str(variance)),
                'notes': self.notes.toPlainText().strip() or None,
                'denominations': {denom: spinbox.value() for denom, spinbox in self.denominations.items()}
            }
