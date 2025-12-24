try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
        QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, 
        QDoubleSpinBox, QTabWidget, QTextEdit, QGroupBox, QCheckBox
    )
    from PySide6.QtCore import Qt, Signal, QDate, QDateTime
    from PySide6.QtGui import QIcon
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
        QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, 
        QDoubleSpinBox, QTabWidget, QTextEdit, QGroupBox, QCheckBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QDate, QDateTime
    from PyQt6.QtGui import QIcon
from decimal import Decimal
from datetime import datetime, timedelta

from pos_app.models.database import BankAccount, BankTransaction, Payment
from pos_app.models.database import PaymentMethod as PaymentMethodEnum
from pos_app.database.db_utils import safe_db_operation, get_db_session

class TransactionDialog(QDialog):
    def __init__(self, transaction_id=None, account_id=None, parent=None):
        super().__init__(parent)
        self.transaction_id = transaction_id
        self.account_id = account_id
        self.setWindowTitle("Add Transaction" if not transaction_id else "Edit Transaction")
        self.setMinimumWidth(600)
        
        self.setup_ui()
        self.load_accounts()
        
        if transaction_id:
            self.load_transaction_data()
        elif account_id:
            # Pre-select the account if provided
            index = self.account_combo.findData(account_id)
            if index >= 0:
                self.account_combo.setCurrentIndex(index)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Account selection
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self.update_balance)
        
        # Transaction type
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "DEPOSIT", "WITHDRAWAL", "TRANSFER_IN", 
            "TRANSFER_OUT", "PAYMENT", "RECEIPT", 
            "INTEREST", "FEE", "ADJUSTMENT"
        ])
        self.type_combo.currentTextChanged.connect(self.update_ui_for_type)
        
        # Date and amount
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDateTime(datetime.now())
        
        self.amount_edit = QDoubleSpinBox()
        self.amount_edit.setRange(0.01, 10000000)
        self.amount_edit.setDecimals(2)
        self.amount_edit.setPrefix("$")
        
        # Reference and description
        self.reference_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        
        # For transfers
        self.transfer_group = QGroupBox("Transfer Details")
        self.transfer_group.setVisible(False)
        transfer_layout = QFormLayout()
        
        self.to_account_combo = QComboBox()
        transfer_layout.addRow("To Account:", self.to_account_combo)
        
        self.transfer_group.setLayout(transfer_layout)
        
        # For payments/receipts
        self.payment_group = QGroupBox("Payment Details")
        self.payment_group.setVisible(False)
        payment_layout = QFormLayout()
        
        self.payment_method_combo = QComboBox()
        self.payment_method_combo.addItems([
            "CASH", "CREDIT_CARD", "DEBIT_CARD", 
            "BANK_TRANSFER", "BANK_DEPOSIT", "CREDIT", "OTHER"
        ])
        
        self.customer_edit = QLineEdit()
        self.customer_edit.setPlaceholderText("Search customer...")
        
        self.invoice_edit = QLineEdit()
        self.invoice_edit.setPlaceholderText("Reference invoice...")
        
        payment_layout.addRow("Payment Method:", self.payment_method_combo)
        payment_layout.addRow("Customer:", self.customer_edit)
        payment_layout.addRow("Invoice:", self.invoice_edit)
        
        self.payment_group.setLayout(payment_layout)
        
        # Add fields to form
        form_layout.addRow("Account*:", self.account_combo)
        form_layout.addRow("Type*:", self.type_combo)
        form_layout.addRow("Date*:", self.date_edit)
        form_layout.addRow("Amount*:", self.amount_edit)
        form_layout.addRow("Reference:", self.reference_edit)
        form_layout.addRow("Description:", self.description_edit)
        
        # Add groups
        layout.addLayout(form_layout)
        layout.addWidget(self.transfer_group)
        layout.addWidget(self.payment_group)
        
        # Current balance display
        self.balance_label = QLabel()
        self.balance_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        layout.addWidget(self.balance_label)
        
        # Buttons
        button_box = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(self.save_btn)
        button_box.addWidget(self.cancel_btn)
        
        layout.addLayout(button_box)
    
    def load_accounts(self):
        with get_db_session() as session:
            accounts = session.query(BankAccount).filter_by(is_active=True).all()
            self.account_combo.clear()
            self.to_account_combo.clear()
            
            for account in accounts:
                display_text = f"{account.name} ({account.account_number}) - ${account.current_balance:,.2f}"
                self.account_combo.addItem(display_text, account.id)
                self.to_account_combo.addItem(display_text, account.id)
            
            # Update balance display for the first account
            if accounts:
                self.update_balance()
    
    def update_balance(self):
        account_id = self.account_combo.currentData()
        if account_id:
            with get_db_session() as session:
                account = session.query(BankAccount).get(account_id)
                if account:
                    self.balance_label.setText(f"Current Balance: ${account.current_balance:,.2f}")
    
    def update_ui_for_type(self, transaction_type):
        # Show/hide transfer group
        is_transfer = transaction_type in ["TRANSFER_IN", "TRANSFER_OUT"]
        self.transfer_group.setVisible(is_transfer)
        
        # Show/hide payment group
        is_payment = transaction_type in ["PAYMENT", "RECEIPT"]
        self.payment_group.setVisible(is_payment)
        
        # Update button text
        if transaction_type == "TRANSFER_IN":
            self.save_btn.setText("Record Transfer")
        elif transaction_type == "TRANSFER_OUT":
            self.save_btn.setText("Record Transfer")
        elif transaction_type == "PAYMENT":
            self.save_btn.setText("Record Payment")
        elif transaction_type == "RECEIPT":
            self.save_btn.setText("Record Receipt")
        else:
            self.save_btn.setText("Save Transaction")
    
    def load_transaction_data(self):
        with get_db_session() as session:
            transaction = session.query(BankTransaction).get(self.transaction_id)
            if transaction:
                # Set account
                index = self.account_combo.findData(transaction.bank_account_id)
                if index >= 0:
                    self.account_combo.setCurrentIndex(index)
                
                # Set type
                type_index = self.type_combo.findText(transaction.transaction_type)
                if type_index >= 0:
                    self.type_combo.setCurrentIndex(type_index)
                
                # Set other fields
                self.date_edit.setDateTime(transaction.transaction_date or datetime.now())
                self.amount_edit.setValue(float(transaction.amount))
                self.reference_edit.setText(transaction.reference_number or "")
                self.description_edit.setPlainText(transaction.description or "")
                
                # For transfers
                if transaction.transaction_type in ["TRANSFER_IN", "TRANSFER_OUT"] and transaction.related_transaction:
                    related_account_id = transaction.related_transaction.bank_account_id
                    index = self.to_account_combo.findData(related_account_id)
                    if index >= 0:
                        self.to_account_combo.setCurrentIndex(index)
    
    def get_data(self):
        data = {
            'bank_account_id': self.account_combo.currentData(),
            'transaction_type': self.type_combo.currentText(),
            'transaction_date': self.date_edit.dateTime().toPython(),
            'amount': Decimal(str(self.amount_edit.value())),
            'reference_number': self.reference_edit.text().strip() or None,
            'description': self.description_edit.toPlainText().strip() or None,
            'is_reconciled': False,
            'created_at': datetime.now()
        }
        
        # For transfers
        if self.type_combo.currentText() in ["TRANSFER_IN", "TRANSFER_OUT"]:
            data['related_account_id'] = self.to_account_combo.currentData()
        
        # For payments/receipts
        if self.type_combo.currentText() in ["PAYMENT", "RECEIPT"]:
            data['payment_method'] = self.payment_method_combo.currentText()
            data['customer_reference'] = self.customer_edit.text().strip() or None
            data['invoice_reference'] = self.invoice_edit.text().strip() or None
        
        return data

class TransactionsWidget(QWidget):
    # Signals
    transaction_updated = Signal()
    
    def __init__(self, controllers, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.setup_ui()
        self.load_transactions()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Bank Transactions")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.add_btn = QPushButton("Add Transaction")
        self.add_btn.clicked.connect(self.add_transaction)
        
        # Filters
        self.filter_account_combo = QComboBox()
        self.filter_account_combo.addItem("All Accounts", None)
        
        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItem("All Types", "")
        
        # Add transaction types with data values
        transaction_types = [
            "DEPOSIT", "WITHDRAWAL", "TRANSFER_IN", 
            "TRANSFER_OUT", "PAYMENT", "RECEIPT", 
            "INTEREST", "FEE", "ADJUSTMENT"
        ]
        for tx_type in transaction_types:
            self.filter_type_combo.addItem(tx_type, tx_type)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        self.reconciled_check = QCheckBox("Reconciled Only")
        
        filter_btn = QPushButton("Filter")
        filter_btn.clicked.connect(self.load_transactions)
        
        # Add widgets to header
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("Account:"))
        header.addWidget(self.filter_account_combo)
        header.addWidget(QLabel("Type:"))
        header.addWidget(self.filter_type_combo)
        header.addWidget(QLabel("From:"))
        header.addWidget(self.date_from)
        header.addWidget(QLabel("To:"))
        header.addWidget(self.date_to)
        header.addWidget(self.reconciled_check)
        header.addWidget(filter_btn)
        header.addWidget(self.add_btn)
        
        # Transactions Table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(8)
        self.transactions_table.setHorizontalHeaderLabels([
            "Date", "Account", "Type", "Reference", "Description", 
            "Debit", "Credit", "Balance", "Actions"
        ])
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.transactions_table.verticalHeader().setVisible(False)
        
        # Set column widths
        self.transactions_table.setColumnWidth(0, 120)  # Date
        self.transactions_table.setColumnWidth(1, 180)  # Account
        self.transactions_table.setColumnWidth(2, 100)  # Type
        self.transactions_table.setColumnWidth(3, 120)  # Reference
        self.transactions_table.setColumnWidth(4, 200)  # Description
        self.transactions_table.setColumnWidth(5, 100)  # Debit
        self.transactions_table.setColumnWidth(6, 100)  # Credit
        self.transactions_table.setColumnWidth(7, 100)  # Balance
        self.transactions_table.setColumnWidth(8, 120)  # Actions
        
        layout.addLayout(header)
        layout.addWidget(self.transactions_table)
        
        # Load accounts for filter
        self.load_accounts()
    
    def load_accounts(self):
        with get_db_session() as session:
            accounts = session.query(BankAccount).filter_by(is_active=True).all()
            self.filter_account_combo.clear()
            self.filter_account_combo.addItem("All Accounts", None)
            
            for account in accounts:
                display_text = f"{account.name} ({account.account_number})"
                self.filter_account_combo.addItem(display_text, account.id)
    
    def load_transactions(self):
        self.transactions_table.setRowCount(0)
        
        account_id = self.filter_account_combo.currentData()
        transaction_type = self.filter_type_combo.currentData()
        if transaction_type == "" or transaction_type is None:  # "All Types" has empty string as data
            transaction_type = None
        # PyQt6 uses toPyDate(), PySide6 uses toPython()
        try:
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().addDays(1).toPython()
        except AttributeError:
            date_from = self.date_from.date().toPyDate()
            date_to = self.date_to.date().addDays(1).toPyDate()
        reconciled_only = self.reconciled_check.isChecked()
        
        with get_db_session() as session:
            query = session.query(BankTransaction)
            
            if account_id:
                query = query.filter_by(bank_account_id=account_id)
            
            if transaction_type:
                query = query.filter_by(transaction_type=transaction_type)
            
            if date_from and date_to:
                query = query.filter(
                    BankTransaction.transaction_date >= date_from,
                    BankTransaction.transaction_date < date_to
                )
            
            if reconciled_only:
                query = query.filter_by(is_reconciled=True)
            
            # Order by date (newest first)
            transactions = query.order_by(BankTransaction.transaction_date.desc()).all()
            
            for row, transaction in enumerate(transactions):
                self.transactions_table.insertRow(row)
                
                # Date
                date_item = QTableWidgetItem(transaction.transaction_date.strftime("%Y-%m-%d %H:%M"))
                date_item.setData(Qt.UserRole, transaction.id)
                
                # Account
                account_name = f"{transaction.bank_account.name} ({transaction.bank_account.account_number[-4:]})"
                
                # Type with color coding
                type_item = QTableWidgetItem(transaction.transaction_type)
                if transaction.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                    type_item.setForeground(Qt.darkGreen)
                else:
                    type_item.setForeground(Qt.darkRed)
                
                # Reference and description
                reference_item = QTableWidgetItem(transaction.reference_number or "")
                description_item = QTableWidgetItem(transaction.description or "")
                
                # Amounts
                is_credit = transaction.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]
                debit = "" if is_credit else f"${transaction.amount:,.2f}"
                credit = f"${transaction.amount:,.2f}" if is_credit else ""
                
                debit_item = QTableWidgetItem(debit)
                credit_item = QTableWidgetItem(credit)
                balance_item = QTableWidgetItem(f"${transaction.balance_after:,.2f}")
                
                # Set text alignment
                for item in [debit_item, credit_item, balance_item]:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Set items in table
                self.transactions_table.setItem(row, 0, date_item)
                self.transactions_table.setItem(row, 1, QTableWidgetItem(account_name))
                self.transactions_table.setItem(row, 2, type_item)
                self.transactions_table.setItem(row, 3, reference_item)
                self.transactions_table.setItem(row, 4, description_item)
                self.transactions_table.setItem(row, 5, debit_item)
                self.transactions_table.setItem(row, 6, credit_item)
                self.transactions_table.setItem(row, 7, balance_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                view_btn = QPushButton("View")
                view_btn.clicked.connect(lambda _, t=transaction.id: self.view_transaction(t))
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda _, t=transaction.id: self.edit_transaction(t))
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda _, t=transaction.id: self.delete_transaction(t))
                
                actions_layout.addWidget(view_btn)
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.setSpacing(2)
                
                self.transactions_table.setCellWidget(row, 8, actions_widget)
            
            # Resize columns to contents
            self.transactions_table.resizeColumnsToContents()
    
    def add_transaction(self, account_id=None):
        dialog = TransactionDialog(account_id=account_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                print(f"[DEBUG] Transaction data: {data}")
                print(f"[DEBUG] Transaction type: {data.get('transaction_type')} (type: {type(data.get('transaction_type'))})")
                
                # Ensure transaction_type is a string
                if 'transaction_type' in data:
                    data['transaction_type'] = str(data['transaction_type'])
                
                transaction = BankTransaction(**data)
                
                # Handle transfers (create two transactions)
                if data['transaction_type'] in ["TRANSFER_IN", "TRANSFER_OUT"]:
                    # First transaction (outgoing)
                    out_account_id = data['bank_account_id']
                    in_account_id = data.pop('related_account_id')
                    
                    # Create outgoing transaction
                    out_transaction = BankTransaction(**data)
                    
                    # Create incoming transaction
                    in_data = data.copy()
                    in_data['bank_account_id'] = in_account_id
                    in_data['transaction_type'] = "TRANSFER_IN" if data['transaction_type'] == "TRANSFER_OUT" else "TRANSFER_OUT"
                    print(f"[DEBUG] Incoming transaction data: {in_data}")
                    print(f"[DEBUG] Incoming transaction type: {in_data.get('transaction_type')} (type: {type(in_data.get('transaction_type'))})")
                    
                    # Ensure transaction_type is a string
                    in_data['transaction_type'] = str(in_data['transaction_type'])
                    in_transaction = BankTransaction(**in_data)
                    
                    # Link transactions
                    out_transaction.related_transaction = in_transaction
                    
                    with get_db_session() as session:
                        # Update account balances
                        out_account = session.query(BankAccount).get(out_account_id)
                        in_account = session.query(BankAccount).get(in_account_id)
                        
                        if out_account and in_account:
                            # Outgoing transaction
                            out_transaction.balance_after = out_account.current_balance - out_transaction.amount
                            out_account.current_balance = out_transaction.balance_after
                            
                            # Incoming transaction
                            in_transaction.balance_after = in_account.current_balance + in_transaction.amount
                            in_account.current_balance = in_transaction.balance_after
                            
                            session.add(out_transaction)
                            session.add(in_transaction)
                            session.commit()
                            
                            QMessageBox.information(self, "Success", "Transfer recorded successfully!")
                        else:
                            QMessageBox.warning(self, "Error", "One or more accounts not found!")
                            return
                else:
                    # Regular transaction
                    with get_db_session() as session:
                        account = session.query(BankAccount).get(data['bank_account_id'])
                        if account:
                            # Update account balance
                            if data['transaction_type'] in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                                transaction.balance_after = account.current_balance + transaction.amount
                                account.current_balance = transaction.balance_after
                            else:
                                transaction.balance_after = account.current_balance - transaction.amount
                                account.current_balance = transaction.balance_after
                            
                            session.add(transaction)
                            session.commit()
                            
                            QMessageBox.information(self, "Success", "Transaction recorded successfully!")
                        else:
                            QMessageBox.warning(self, "Error", "Account not found!")
                            return
                
                self.load_transactions()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to record transaction: {str(e)}")
    
    def edit_transaction(self, transaction_id):
        dialog = TransactionDialog(transaction_id, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                
                with get_db_session() as session:
                    transaction = session.query(BankTransaction).get(transaction_id)
                    if transaction:
                        # Store old values for balance recalculation
                        old_amount = transaction.amount
                        old_type = transaction.transaction_type
                        old_account_id = transaction.bank_account_id
                        
                        # Update transaction
                        for key, value in data.items():
                            if key != 'related_account_id':  # Handle this separately
                                setattr(transaction, key, value)
                        
                        # Recalculate balance
                        account = session.query(BankAccount).get(transaction.bank_account_id)
                        if account:
                            # First, reverse the old transaction
                            if old_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                                account.current_balance -= old_amount
                            else:
                                account.current_balance += old_amount
                            
                            # Then apply the new transaction
                            if transaction.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                                transaction.balance_after = account.current_balance + transaction.amount
                                account.current_balance = transaction.balance_after
                            else:
                                transaction.balance_after = account.current_balance - transaction.amount
                                account.current_balance = transaction.balance_after
                            
                            session.commit()
                            QMessageBox.information(self, "Success", "Transaction updated successfully!")
                            self.load_transactions()
                        else:
                            QMessageBox.warning(self, "Error", "Account not found!")
                    else:
                        QMessageBox.warning(self, "Error", "Transaction not found!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update transaction: {str(e)}")
    
    def view_transaction(self, transaction_id):
        # TODO: Implement detailed view
        pass
    
    def delete_transaction(self, transaction_id):
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this transaction? This will also reverse the account balance.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with get_db_session() as session:
                    transaction = session.query(BankTransaction).get(transaction_id)
                    if transaction:
                        # Get the account
                        account = session.query(BankAccount).get(transaction.bank_account_id)
                        if account:
                            # Reverse the transaction amount
                            if transaction.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                                account.current_balance -= transaction.amount
                            else:
                                account.current_balance += transaction.amount
                            
                            # If this is part of a transfer, also delete the related transaction
                            if transaction.related_transaction_id:
                                related = session.query(BankTransaction).get(transaction.related_transaction_id)
                                if related:
                                    related_account = session.query(BankAccount).get(related.bank_account_id)
                                    if related_account:
                                        if related.transaction_type in ["DEPOSIT", "TRANSFER_IN", "RECEIPT"]:
                                            related_account.current_balance -= related.amount
                                        else:
                                            related_account.current_balance += related.amount
                                    session.delete(related)
                            
                            session.delete(transaction)
                            session.commit()
                            
                            QMessageBox.information(self, "Success", "Transaction deleted successfully!")
                            self.load_transactions()
                        else:
                            QMessageBox.warning(self, "Error", "Account not found!")
                    else:
                        QMessageBox.warning(self, "Error", "Transaction not found!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete transaction: {str(e)}")
