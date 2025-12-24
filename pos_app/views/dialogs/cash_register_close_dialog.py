"""
Cash Register Close Dialog - Simplified version with cash out tracking
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

class CashRegisterCloseDialog(QDialog):
    """Simplified dialog for closing cash register"""
    
    def __init__(self, session_data=None, parent=None):
        super().__init__(parent)
        self.session_data = session_data or {}
        
        self.setWindowTitle("Close Cash Register")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("🔒 Close Cash Register")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Session info
        info_group = QGroupBox("Session Information")
        info_layout = QFormLayout()
        
        opened_at = self.session_data.get('opened_at', datetime.now())
        opening_balance = self.session_data.get('opening_balance', 0.0)
        expected_balance = self.session_data.get('expected_balance', 0.0)
        
        info_layout.addRow("Opened:", QLabel(opened_at.strftime("%Y-%m-%d %H:%M")))
        info_layout.addRow("Opening Balance:", QLabel(f"Rs {opening_balance:,.2f}"))
        
        self.expected_label = QLabel(f"Rs {expected_balance:,.2f}")
        self.expected_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        info_layout.addRow("Expected Balance:", self.expected_label)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
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
        
        # Cash taken out
        cashout_layout = QFormLayout()
        self.cash_out = QDoubleSpinBox()
        self.cash_out.setRange(0, 10000000)
        self.cash_out.setDecimals(2)
        self.cash_out.setPrefix("Rs ")
        self.cash_out.setValue(0.0)
        self.cash_out.setStyleSheet("font-size: 16px; padding: 8px;")
        self.cash_out.valueChanged.connect(self.calculate_final)
        cashout_layout.addRow("Cash Taken Out (for expenses/personal):", self.cash_out)
        layout.addLayout(cashout_layout)
        
        # Final balance after cash out
        final_layout = QHBoxLayout()
        final_layout.addWidget(QLabel("Final Balance (after cash out):"))
        self.final_balance_label = QLabel("Rs 0.00")
        self.final_balance_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #8b5cf6;")
        final_layout.addWidget(self.final_balance_label)
        final_layout.addStretch()
        layout.addLayout(final_layout)
        
        # Variance
        variance_layout = QHBoxLayout()
        variance_layout.addWidget(QLabel("Variance:"))
        self.variance_label = QLabel("Rs 0.00")
        self.variance_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        variance_layout.addWidget(self.variance_label)
        variance_layout.addStretch()
        layout.addLayout(variance_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_btn = QPushButton("Close Register")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: Qt.white;
                border: none;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #dc2626;
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
        self.calculate_final()
    
    def calculate_final(self):
        """Calculate final balance and variance"""
        # Get total counted
        total = sum(denom * spinbox.value() for denom, spinbox in self.denominations.items())
        
        # Subtract cash taken out
        cash_out = self.cash_out.value()
        final_balance = total - cash_out
        
        self.final_balance_label.setText(f"Rs {final_balance:,.2f}")
        
        # Calculate variance (final balance vs expected)
        expected = self.session_data.get('expected_balance', 0.0)
        variance = final_balance - expected
        
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
        # Calculate totals
        total_counted = sum(denom * spinbox.value() for denom, spinbox in self.denominations.items())
        cash_out = self.cash_out.value()
        final_balance = total_counted - cash_out
        expected = self.session_data.get('expected_balance', 0.0)
        variance = final_balance - expected
        
        return {
            'closing_balance': Decimal(str(final_balance)),
            'expected_balance': Decimal(str(expected)),
            'variance': Decimal(str(variance)),
            'cash_out': Decimal(str(cash_out)),
            'total_counted': Decimal(str(total_counted)),
            'denominations': {denom: spinbox.value() for denom, spinbox in self.denominations.items()}
        }
