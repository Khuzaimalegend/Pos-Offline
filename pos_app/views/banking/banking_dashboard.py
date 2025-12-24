try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QFrame, QGridLayout, QPushButton, QComboBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractItemView
    )
    from PySide6.QtCore import Qt, QDate, Signal
    from PySide6.QtGui import QColor, QBrush, QLinearGradient, QPalette, QPainter
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QFrame, QGridLayout, QPushButton, QComboBox,
        QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractItemView
    )
    from PyQt6.QtCore import Qt, QDate, pyqtSignal as Signal
    from PyQt6.QtGui import QColor, QBrush, QLinearGradient, QPalette, QPainter
from datetime import datetime, timedelta
from decimal import Decimal

from pos_app.models.database import BankAccount, BankTransaction, Payment, Sale
from pos_app.models.database import PaymentMethod as PaymentMethodEnum
from pos_app.database.db_utils import safe_db_operation, get_db_session

class BalanceCard(QFrame):
    def __init__(self, title, amount, color, parent=None):
        super().__init__(parent)
        self.title = title
        self.amount = amount
        self.color = color
        self.setup_ui()
    
    def setup_ui(self):
        try:
            self.setFrameShape(QFrame.StyledPanel)
        except AttributeError:
            self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #e0e0e0;
            }
            QLabel#title {
                color: #666666;
                font-size: 14px;
                font-weight: 500;
            }
            QLabel#amount {
                color: #333333;
                font-size: 24px;
                font-weight: 600;
                margin-top: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel(self.title)
        title_label.setObjectName("title")
        
        amount_str = f"${self.amount:,.2f}" if isinstance(self.amount, (int, float, Decimal)) else self.amount
        amount_label = QLabel(amount_str)
        amount_label.setObjectName("amount")
        
        # Set text color based on amount
        if isinstance(self.amount, (int, float, Decimal)):
            if self.amount < 0:
                amount_label.setStyleSheet("color: #d32f2f;")  # Red for negative
            elif self.amount > 0:
                amount_label.setStyleSheet(f"color: {self.color};")  # Custom color for positive
        
        layout.addWidget(title_label)
        layout.addWidget(amount_label)
        layout.addStretch()
        
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)

class BankingDashboardWidget(QWidget):
    # Signals
    data_updated = Signal()
    refresh_requested = Signal()
    
    def __init__(self, controllers, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Banking Overview")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        
        # Time period selector
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Today", "This Week", "This Month", "This Year", "All Time"])
        self.period_combo.setCurrentText("This Month")
        self.period_combo.currentTextChanged.connect(self.load_data)
        
        header.addWidget(title)
        header.addStretch()
        period_lbl = QLabel("Period:")
        period_lbl.setStyleSheet("color: #e2e8f0; font-weight: 600;")
        header.addWidget(period_lbl)
        header.addWidget(self.period_combo)
        
        # Balance Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(15)
        
        self.cash_balance_card = BalanceCard("Cash Balance", 0, "#2ecc71")
        self.bank_balance_card = BalanceCard("Bank Balance", 0, "#3498db")
        self.credit_balance_card = BalanceCard("Credit Balance", 0, "#e74c3c")
        self.net_balance_card = BalanceCard("Net Balance", 0, "#9b59b6")
        
        cards_layout.addWidget(self.cash_balance_card)
        cards_layout.addWidget(self.bank_balance_card)
        cards_layout.addWidget(self.credit_balance_card)
        cards_layout.addWidget(self.net_balance_card)
        
        # Charts and Tables
        charts_tables_layout = QHBoxLayout()
        
        # Left side - Payment Methods
        payment_methods_group = QFrame()
        payment_methods_group.setFrameShape(QFrame.StyledPanel)
        payment_methods_group.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-radius: 8px;
                border: 1px solid #334155;
                padding: 15px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: 600;
                color: #e2e8f0;
                margin-bottom: 15px;
            }
        """)
        
        payment_methods_layout = QVBoxLayout(payment_methods_group)
        
        title = QLabel("Payment Methods")
        title.setObjectName("title")
        
        self.payment_methods_table = QTableWidget()
        self.payment_methods_table.setColumnCount(2)
        self.payment_methods_table.setHorizontalHeaderLabels(["Method", "Amount"])
        self.payment_methods_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.payment_methods_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.payment_methods_table.verticalHeader().setVisible(False)
        self.payment_methods_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.payment_methods_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.payment_methods_table.setAlternatingRowColors(True)
        
        payment_methods_layout.addWidget(title)
        payment_methods_layout.addWidget(self.payment_methods_table)
        
        # Right side - Recent Transactions
        recent_transactions_group = QFrame()
        recent_transactions_group.setFrameShape(QFrame.StyledPanel)
        recent_transactions_group.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-radius: 8px;
                border: 1px solid #334155;
                padding: 15px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: 600;
                color: #e2e8f0;
                margin-bottom: 15px;
            }
        """)
        
        recent_transactions_layout = QVBoxLayout(recent_transactions_group)
        
        title = QLabel("Recent Transactions")
        title.setObjectName("title")
        
        self.recent_transactions_table = QTableWidget()
        self.recent_transactions_table.setColumnCount(5)
        self.recent_transactions_table.setHorizontalHeaderLabels(["Date", "Account", "Type", "Description", "Amount"])
        self.recent_transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.recent_transactions_table.verticalHeader().setVisible(False)
        self.recent_transactions_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.recent_transactions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.recent_transactions_table.setAlternatingRowColors(True)
        
        # Set column widths
        self.recent_transactions_table.setColumnWidth(0, 100)  # Date
        self.recent_transactions_table.setColumnWidth(1, 120)  # Account
        self.recent_transactions_table.setColumnWidth(2, 100)  # Type
        self.recent_transactions_table.setColumnWidth(3, 200)  # Description
        self.recent_transactions_table.setColumnWidth(4, 100)  # Amount
        
        recent_transactions_layout.addWidget(title)
        recent_transactions_layout.addWidget(self.recent_transactions_table)
        
        # Add to main layout
        charts_tables_layout.addWidget(payment_methods_group, 1)
        charts_tables_layout.addWidget(recent_transactions_group, 2)
        
        # Add all to main layout
        layout.addLayout(header)
        layout.addLayout(cards_layout)
        layout.addLayout(charts_tables_layout, 1)
    
    def get_date_range(self, period):
        today = datetime.now().date()
        
        if period == "Today":
            start_date = today
            end_date = today + timedelta(days=1)
        elif period == "This Week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(weeks=1)
        elif period == "This Month":
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1)
        elif period == "This Year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(year=today.year + 1, month=1, day=1)
        else:  # All Time
            start_date = None
            end_date = None
        
        return start_date, end_date
    
    def load_data(self):
        period = self.period_combo.currentText()
        start_date, end_date = self.get_date_range(period)
        
        with get_db_session() as session:
            # Load account balances
            cash_balance = 0
            bank_balance = 0
            credit_balance = 0
            
            # Get all bank accounts
            bank_accounts = session.query(BankAccount).all()
            for account in bank_accounts:
                if "cash" in account.name.lower():
                    cash_balance += float(account.current_balance or 0)
                else:
                    bank_balance += float(account.current_balance or 0)
            
            # Update balance cards
            self.cash_balance_card.amount = cash_balance
            self.bank_balance_card.amount = bank_balance
            self.credit_balance_card.amount = credit_balance
            self.net_balance_card.amount = cash_balance + bank_balance + credit_balance
            
            # Update card displays
            self.update_balance_card(self.cash_balance_card)
            self.update_balance_card(self.bank_balance_card)
            self.update_balance_card(self.credit_balance_card)
            self.update_balance_card(self.net_balance_card)
            
            # Load payment methods data
            self.load_payment_methods(session, start_date, end_date)
            
            # Load recent transactions
            self.load_recent_transactions(session, start_date, end_date)
    
    def update_balance_card(self, card):
        # Find the amount label and update it
        amount_label = card.findChild(QLabel, "amount")
        if amount_label:
            amount_str = f"${card.amount:,.2f}" if isinstance(card.amount, (int, float, Decimal)) else str(card.amount)
            amount_label.setText(amount_str)
            
            # Update color based on amount
            if isinstance(card.amount, (int, float, Decimal)):
                if card.amount < 0:
                    amount_label.setStyleSheet("color: #d32f2f; font-size: 24px; font-weight: 600; margin-top: 5px;")
                else:
                    amount_label.setStyleSheet(f"color: {card.color}; font-size: 24px; font-weight: 600; margin-top: 5px;")
    
    def load_payment_methods(self, session, start_date, end_date):
        # Query payments for the selected period
        query = session.query(Payment.payment_method, Payment.amount)
        
        if start_date and end_date:
            query = query.filter(Payment.payment_date >= start_date, Payment.payment_date < end_date)
        
        payments = query.all()
        
        # Group by payment method
        method_totals = {}
        for method, amount in payments:
            method_name = str(method) if method else "Unknown"
            if method_name not in method_totals:
                method_totals[method_name] = 0
            method_totals[method_name] += float(amount or 0)
        
        # Sort by amount (descending)
        sorted_methods = sorted(method_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Update table
        self.payment_methods_table.setRowCount(len(sorted_methods))
        for row, (method, total) in enumerate(sorted_methods):
            method_item = QTableWidgetItem(method.replace("_", " ").title())
            total_item = QTableWidgetItem(f"${total:,.2f}")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            self.payment_methods_table.setItem(row, 0, method_item)
            self.payment_methods_table.setItem(row, 1, total_item)
    
    def load_recent_transactions(self, session, start_date, end_date):
        # Query recent bank transactions
        query = session.query(
            BankTransaction,
            BankAccount.name.label('account_name')
        ).join(
            BankAccount,
            BankTransaction.bank_account_id == BankAccount.id
        )
        
        if start_date and end_date:
            query = query.filter(
                BankTransaction.transaction_date >= start_date,
                BankTransaction.transaction_date < end_date
            )
        
        transactions = query.order_by(BankTransaction.transaction_date.desc()).limit(10).all()
        
        # Update table
        self.recent_transactions_table.setRowCount(len(transactions))
        
        for row, (transaction, account_name) in enumerate(transactions):
            # Date
            date_item = QTableWidgetItem(transaction.transaction_date.strftime("%Y-%m-%d"))
            
            # Account (show last 4 digits)
            account_display = f"{account_name} ({transaction.bank_account.account_number[-4:]})"
            account_item = QTableWidgetItem(account_display)
            
            # Type with color coding
            type_item = QTableWidgetItem(transaction.transaction_type)
            if transaction.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                type_item.setForeground(QColor("#2e7d32"))  # Dark Qt.green
            else:
                type_item.setForeground(QColor("#c62828"))  # Dark Qt.red
            
            # Description
            desc = transaction.description or ""
            if transaction.reference_number:
                desc = f"{transaction.reference_number}: {desc}"
            desc_item = QTableWidgetItem(desc[:50] + (desc[50:] and '...'))
            
            # Amount with color coding
            is_credit = transaction.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]
            amount_str = f"${transaction.amount:,.2f}"
            amount_item = QTableWidgetItem(amount_str)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            if is_credit:
                amount_item.setForeground(QColor("#2e7d32"))  # Dark Qt.green
            else:
                amount_item.setForeground(QColor("#c62828"))  # Dark Qt.red
            
            # Set items in table
            self.recent_transactions_table.setItem(row, 0, date_item)
            self.recent_transactions_table.setItem(row, 1, account_item)
            self.recent_transactions_table.setItem(row, 2, type_item)
            self.recent_transactions_table.setItem(row, 3, desc_item)
            self.recent_transactions_table.setItem(row, 4, amount_item)
        
        # Resize columns to contents
        self.recent_transactions_table.resizeColumnsToContents()
