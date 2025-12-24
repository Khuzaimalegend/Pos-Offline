try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QSpinBox
    )
    from PySide6.QtCore import Qt, QDate, Signal
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QSpinBox
    )
    from PyQt6.QtCore import Qt, QDate, pyqtSignal as Signal
    from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
import logging

app_logger = logging.getLogger(__name__)

class BankManagementWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🏦 Bank Account Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs for different sections
        tabs = QTabWidget()
        
        # Bank Accounts Tab
        accounts_tab = self.create_accounts_tab()
        tabs.addTab(accounts_tab, "🏦 Bank Accounts")
        
        # Transactions Tab
        transactions_tab = self.create_transactions_tab()
        tabs.addTab(transactions_tab, "💳 Transactions")
        
        # Summary Tab
        summary_tab = self.create_summary_tab()
        tabs.addTab(summary_tab, "📊 Summary")
        
        layout.addWidget(tabs)

    def create_accounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Action buttons
        actions_layout = QHBoxLayout()
        
        add_account_btn = QPushButton("➕ Add Bank Account")
        add_account_btn.setProperty('accent', 'Qt.green')
        add_account_btn.setMinimumHeight(40)
        add_account_btn.clicked.connect(self.add_bank_account)
        
        edit_account_btn = QPushButton("✏️ Edit Account")
        edit_account_btn.setProperty('accent', 'Qt.blue')
        edit_account_btn.setMinimumHeight(40)
        edit_account_btn.setEnabled(False)
        
        delete_account_btn = QPushButton("🗑️ Delete Account")
        delete_account_btn.setProperty('accent', 'Qt.red')
        delete_account_btn.setMinimumHeight(40)
        delete_account_btn.setEnabled(False)
        
        actions_layout.addWidget(add_account_btn)
        actions_layout.addWidget(edit_account_btn)
        actions_layout.addWidget(delete_account_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Bank accounts table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(7)
        self.accounts_table.setHorizontalHeaderLabels([
            "Account Name", "Bank Name", "Account Number", "Type", 
            "Current Balance", "Opening Balance", "Status"
        ])
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.accounts_table.itemSelectionChanged.connect(self.on_account_selection_changed)
        
        layout.addWidget(self.accounts_table)
        
        self.load_bank_accounts()
        return widget

    def create_transactions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filters
        filters_frame = QFrame()
        filters_frame.setProperty('role', 'card')
        filters_layout = QHBoxLayout(filters_frame)
        
        filters_layout.addWidget(QLabel("Account:"))
        self.account_filter = QComboBox()
        self.account_filter.addItem("All Accounts", None)
        filters_layout.addWidget(self.account_filter)
        
        filters_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filters_layout.addWidget(self.date_to)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.filter_transactions)
        filters_layout.addWidget(filter_btn)
        
        filters_layout.addStretch()
        
        # Transaction actions
        add_transaction_btn = QPushButton("➕ Add Transaction")
        add_transaction_btn.setProperty('accent', 'Qt.green')
        add_transaction_btn.clicked.connect(self.add_transaction)
        filters_layout.addWidget(add_transaction_btn)
        
        layout.addWidget(filters_frame)

        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Account", "Type", "Amount", "Balance After", 
            "Reference", "Description", "Category"
        ])
        self.transactions_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.transactions_table)
        
        self.load_transactions()
        return widget

    def create_summary_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Summary cards
        summary_frame = QFrame()
        summary_frame.setProperty('role', 'card')
        summary_layout = QVBoxLayout(summary_frame)
        
        # Total balance
        self.total_balance_label = QLabel("💰 Total Balance: Rs 0.00")
        self.total_balance_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #34d399; margin: 10px;")
        summary_layout.addWidget(self.total_balance_label)
        
        # Account balances
        accounts_layout = QHBoxLayout()
        
        # This month summary
        month_frame = QFrame()
        month_frame.setProperty('role', 'card')
        month_layout = QVBoxLayout(month_frame)
        
        month_layout.addWidget(QLabel("📅 This Month"))
        self.month_income_label = QLabel("Income: Rs 0.00")
        self.month_expense_label = QLabel("Expenses: Rs 0.00")
        self.month_net_label = QLabel("Net: Rs 0.00")
        
        month_layout.addWidget(self.month_income_label)
        month_layout.addWidget(self.month_expense_label)
        month_layout.addWidget(self.month_net_label)
        
        accounts_layout.addWidget(month_frame)
        
        # Year summary
        year_frame = QFrame()
        year_frame.setProperty('role', 'card')
        year_layout = QVBoxLayout(year_frame)
        
        year_layout.addWidget(QLabel("📊 This Year"))
        self.year_income_label = QLabel("Income: Rs 0.00")
        self.year_expense_label = QLabel("Expenses: Rs 0.00")
        self.year_net_label = QLabel("Net: Rs 0.00")
        
        year_layout.addWidget(self.year_income_label)
        year_layout.addWidget(self.year_expense_label)
        year_layout.addWidget(self.year_net_label)
        
        accounts_layout.addWidget(year_frame)
        
        summary_layout.addLayout(accounts_layout)
        layout.addWidget(summary_frame)
        
        # Recent transactions
        recent_frame = QFrame()
        recent_frame.setProperty('role', 'card')
        recent_layout = QVBoxLayout(recent_frame)
        
        recent_layout.addWidget(QLabel("🕒 Recent Transactions"))
        
        self.recent_transactions_table = QTableWidget()
        self.recent_transactions_table.setColumnCount(5)
        self.recent_transactions_table.setHorizontalHeaderLabels([
            "Date", "Account", "Type", "Amount", "Description"
        ])
        self.recent_transactions_table.setMaximumHeight(200)
        
        recent_layout.addWidget(self.recent_transactions_table)
        layout.addWidget(recent_frame)
        
        self.update_summary()
        return widget

    def add_bank_account(self):
        dialog = BankAccountDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                from pos_app.models.database import BankAccount
                
                account = BankAccount(
                    account_name=dialog.account_name.text(),
                    bank_name=dialog.bank_name.text(),
                    account_number=dialog.account_number.text(),
                    routing_number=dialog.routing_number.text(),
                    account_type=dialog.account_type.currentText(),
                    current_balance=dialog.current_balance.value(),
                    opening_balance=dialog.opening_balance.value(),
                    opening_date=dialog.opening_date.date().toPython(),
                    notes=dialog.notes.toPlainText()
                )
                
                self.controller.session.add(account)
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", "Bank account added successfully!")
                self.load_bank_accounts()
                self.update_summary()
                
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to add bank account: {str(e)}")

    def add_transaction(self):
        dialog = BankTransactionDialog(self, self.controller)
        if dialog.exec() == QDialog.Accepted:
            try:
                from pos_app.models.database import BankTransaction, BankAccount
                
                # Get selected account
                account_id = dialog.account_combo.currentData()
                account = self.controller.session.get(BankAccount, account_id)
                
                if not account:
                    QMessageBox.warning(self, "Error", "Please select a valid bank account")
                    return
                
                # Calculate new balance
                amount = dialog.amount.value()
                if dialog.transaction_type.currentText() == "WITHDRAWAL":
                    amount = -amount
                
                new_balance = account.current_balance + amount
                
                # Create transaction
                transaction = BankTransaction(
                    bank_account_id=account_id,
                    transaction_date=dialog.transaction_date.dateTime().toPython(),
                    transaction_type=dialog.transaction_type.currentText(),
                    amount=abs(amount),
                    balance_after=new_balance,
                    reference_number=dialog.reference.text(),
                    description=dialog.description.text()
                )
                
                # Update account balance
                account.current_balance = new_balance
                
                self.controller.session.add(transaction)
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", "Transaction added successfully!")
                self.load_transactions()
                self.load_bank_accounts()
                self.update_summary()
                
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to add transaction: {str(e)}")

    def load_bank_accounts(self):
        try:
            from pos_app.models.database import BankAccount
            
            accounts = self.controller.session.query(BankAccount).filter(  # TODO: Add .all() or .first()
                BankAccount.is_active == True
            ).all()
            
            self.accounts_table.setRowCount(len(accounts))
            
            # Update account filter combo
            self.account_filter.clear()
            self.account_filter.addItem("All Accounts", None)
            
            for i, account in enumerate(accounts):
                self.accounts_table.setItem(i, 0, QTableWidgetItem(account.account_name))
                self.accounts_table.setItem(i, 1, QTableWidgetItem(account.bank_name))
                self.accounts_table.setItem(i, 2, QTableWidgetItem(account.account_number))
                self.accounts_table.setItem(i, 3, QTableWidgetItem(account.account_type or ""))
                self.accounts_table.setItem(i, 4, QTableWidgetItem(f"Rs {account.current_balance:,.2f}"))
                self.accounts_table.setItem(i, 5, QTableWidgetItem(f"Rs {account.opening_balance:,.2f}"))
                self.accounts_table.setItem(i, 6, QTableWidgetItem("Active" if account.is_active else "Inactive"))
                
                # Store account ID
                self.accounts_table.item(i, 0).setData(Qt.UserRole, account.id)
                
                # Add to filter combo
                self.account_filter.addItem(f"{account.account_name} - {account.bank_name}", account.id)
                
        except Exception as e:
            app_logger.exception("Failed to load bank accounts")
            QMessageBox.critical(self, "Error", f"Failed to load bank accounts: {str(e)}")

    def load_transactions(self):
        try:
            from pos_app.models.database import BankTransaction, BankAccount
            
            query = self.controller.session.query(BankTransaction).join(BankAccount)
            
            # Apply account filter
            account_id = self.account_filter.currentData()
            if account_id:
                query = query.filter(BankTransaction.bank_account_id == account_id)
            
            transactions = query.order_by(BankTransaction.transaction_date.desc()).limit(100).all()
            
            self.transactions_table.setRowCount(len(transactions))
            
            for i, transaction in enumerate(transactions):
                self.transactions_table.setItem(i, 0, QTableWidgetItem(
                    transaction.transaction_date.strftime('%Y-%m-%d %H:%M') if transaction.transaction_date else ""
                ))
                self.transactions_table.setItem(i, 1, QTableWidgetItem(
                    transaction.bank_account.account_name if transaction.bank_account else ""
                ))
                self.transactions_table.setItem(i, 2, QTableWidgetItem(transaction.transaction_type))
                
                # Color code amounts
                amount_item = QTableWidgetItem(f"Rs {transaction.amount:,.2f}")
                if transaction.transaction_type == "WITHDRAWAL":
                    amount_item.setForeground(Qt.red)
                else:
                    amount_item.setForeground(Qt.green)
                self.transactions_table.setItem(i, 3, amount_item)
                
                self.transactions_table.setItem(i, 4, QTableWidgetItem(f"Rs {transaction.balance_after:,.2f}"))
                self.transactions_table.setItem(i, 5, QTableWidgetItem(transaction.reference or ""))
                self.transactions_table.setItem(i, 6, QTableWidgetItem(transaction.description or ""))
                self.transactions_table.setItem(i, 7, QTableWidgetItem(transaction.category or ""))
                
        except Exception as e:
            app_logger.exception("Failed to load transactions")
            QMessageBox.critical(self, "Error", f"Failed to load transactions: {str(e)}")

    def filter_transactions(self):
        self.load_transactions()

    def update_summary(self):
        try:
            from pos_app.models.database import BankAccount, BankTransaction
            
            # Calculate total balance
            accounts = self.controller.session.query(BankAccount).filter(  # TODO: Add .all() or .first()
                BankAccount.is_active == True
            ).all()
            
            total_balance = sum(account.current_balance for account in accounts)
            self.total_balance_label.setText(f"💰 Total Balance: Rs {total_balance:,.2f}")
            
            # Calculate monthly summary
            now = datetime.now()
            month_start = datetime(now.year, now.month, 1)
            
            month_transactions = self.controller.session.query(BankTransaction).filter(  # TODO: Add .all() or .first()
                BankTransaction.transaction_date >= month_start
            ).all()
            
            month_income = sum(t.amount for t in month_transactions if t.transaction_type == "DEPOSIT")
            month_expense = sum(t.amount for t in month_transactions if t.transaction_type == "WITHDRAWAL")
            month_net = month_income - month_expense
            
            self.month_income_label.setText(f"Income: Rs {month_income:,.2f}")
            self.month_expense_label.setText(f"Expenses: Rs {month_expense:,.2f}")
            self.month_net_label.setText(f"Net: Rs {month_net:,.2f}")
            
            # Calculate yearly summary
            year_start = datetime(now.year, 1, 1)
            
            year_transactions = self.controller.session.query(BankTransaction).filter(  # TODO: Add .all() or .first()
                BankTransaction.transaction_date >= year_start
            ).all()
            
            year_income = sum(t.amount for t in year_transactions if t.transaction_type == "DEPOSIT")
            year_expense = sum(t.amount for t in year_transactions if t.transaction_type == "WITHDRAWAL")
            year_net = year_income - year_expense
            
            self.year_income_label.setText(f"Income: Rs {year_income:,.2f}")
            self.year_expense_label.setText(f"Expenses: Rs {year_expense:,.2f}")
            self.year_net_label.setText(f"Net: Rs {year_net:,.2f}")
            
            # Load recent transactions
            recent_transactions = self.controller.session.query(BankTransaction).join(BankAccount).order_by(
                BankTransaction.transaction_date.desc()
            ).limit(10).all()
            
            self.recent_transactions_table.setRowCount(len(recent_transactions))
            
            for i, transaction in enumerate(recent_transactions):
                self.recent_transactions_table.setItem(i, 0, QTableWidgetItem(
                    transaction.transaction_date.strftime('%Y-%m-%d') if transaction.transaction_date else ""
                ))
                self.recent_transactions_table.setItem(i, 1, QTableWidgetItem(
                    transaction.bank_account.account_name if transaction.bank_account else ""
                ))
                self.recent_transactions_table.setItem(i, 2, QTableWidgetItem(transaction.transaction_type))
                
                amount_item = QTableWidgetItem(f"Rs {transaction.amount:,.2f}")
                if transaction.transaction_type == "WITHDRAWAL":
                    amount_item.setForeground(Qt.red)
                else:
                    amount_item.setForeground(Qt.green)
                self.recent_transactions_table.setItem(i, 3, amount_item)
                
                self.recent_transactions_table.setItem(i, 4, QTableWidgetItem(transaction.description or ""))
                
        except Exception as e:
            app_logger.exception("Failed to update summary")

    def on_account_selection_changed(self):
        # Enable/disable edit and delete buttons based on selection
        has_selection = len(self.accounts_table.selectedItems()) > 0
        # Note: You would need to get references to edit and delete buttons to enable/disable them


class BankAccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Bank Account")
        self.setMinimumSize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.account_name = QLineEdit()
        self.account_name.setPlaceholderText("e.g., Main Business Account")
        layout.addRow("Account Name:", self.account_name)

        self.bank_name = QLineEdit()
        self.bank_name.setPlaceholderText("e.g., State Bank of Pakistan")
        layout.addRow("Bank Name:", self.bank_name)

        self.account_number = QLineEdit()
        self.account_number.setPlaceholderText("Account Number")
        layout.addRow("Account Number:", self.account_number)

        self.routing_number = QLineEdit()
        self.routing_number.setPlaceholderText("Routing/IBAN Number")
        layout.addRow("Routing Number:", self.routing_number)

        self.account_type = QComboBox()
        self.account_type.addItems(["CHECKING", "SAVINGS", "BUSINESS", "CURRENT"])
        layout.addRow("Account Type:", self.account_type)

        self.opening_balance = QDoubleSpinBox()
        self.opening_balance.setRange(0, 10000000)
        self.opening_balance.setSuffix(" Rs")
        layout.addRow("Opening Balance:", self.opening_balance)

        self.current_balance = QDoubleSpinBox()
        self.current_balance.setRange(0, 10000000)
        self.current_balance.setSuffix(" Rs")
        layout.addRow("Current Balance:", self.current_balance)

        self.opening_date = QDateEdit()
        self.opening_date.setDate(QDate.currentDate())
        self.opening_date.setCalendarPopup(True)
        layout.addRow("Opening Date:", self.opening_date)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addRow(buttons_layout)


class BankTransactionDialog(QDialog):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Add Bank Transaction")
        self.setMinimumSize(400, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Load bank accounts
        self.account_combo = QComboBox()
        self.load_accounts()
        layout.addRow("Bank Account:", self.account_combo)

        self.transaction_date = QDateEdit()
        self.transaction_date.setDateTime(datetime.now())
        self.transaction_date.setCalendarPopup(True)
        layout.addRow("Transaction Date:", self.transaction_date)

        self.transaction_type = QComboBox()
        self.transaction_type.addItems(["DEPOSIT", "WITHDRAWAL", "TRANSFER"])
        layout.addRow("Transaction Type:", self.transaction_type)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 10000000)
        self.amount.setSuffix(" Rs")
        layout.addRow("Amount:", self.amount)

        self.reference = QLineEdit()
        self.reference.setPlaceholderText("Check number, transaction ID, etc.")
        layout.addRow("Reference:", self.reference)

        self.description = QLineEdit()
        self.description.setPlaceholderText("Transaction description")
        layout.addRow("Description:", self.description)

        self.category = QLineEdit()
        self.category.setPlaceholderText("e.g., Sales, Expenses, Loan")
        layout.addRow("Category:", self.category)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addRow(buttons_layout)

    def load_accounts(self):
        try:
            from pos_app.models.database import BankAccount
            
            accounts = self.controller.session.query(BankAccount).filter(  # TODO: Add .all() or .first()
                BankAccount.is_active == True
            ).all()
            
            for account in accounts:
                self.account_combo.addItem(
                    f"{account.account_name} - {account.bank_name}",
                    account.id
                )
                
        except Exception as e:
            app_logger.exception("Failed to load accounts for transaction dialog")
