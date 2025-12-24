try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
        QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, 
        QDoubleSpinBox, QTabWidget, QTextEdit, QGroupBox
    )
    from PySide6.QtCore import Qt, Signal, QDate
    from PySide6.QtGui import QIcon
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
        QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, 
        QDialog, QFormLayout, QLineEdit, QComboBox, QDateEdit, 
        QDoubleSpinBox, QTabWidget, QTextEdit, QGroupBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QDate
    from PyQt6.QtGui import QIcon
from decimal import Decimal
from datetime import datetime

from pos_app.models.database import BankAccount, BankTransaction
from pos_app.database.db_utils import safe_db_operation, get_db_session

class BankAccountDialog(QDialog):
    def __init__(self, account_id=None, parent=None):
        super().__init__(parent)
        self.account_id = account_id
        self.setWindowTitle("Add Bank Account" if not account_id else "Edit Bank Account")
        self.setMinimumWidth(500)
        
        self.setup_ui()
        
        if account_id:
            self.load_account_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Account Information
        self.name_edit = QLineEdit()
        self.account_number_edit = QLineEdit()
        self.bank_name_edit = QLineEdit()
        self.branch_name_edit = QLineEdit()
        
        # Account Type
        self.account_type_combo = QComboBox()
        self.account_type_combo.addItems(["CHECKING", "SAVINGS", "BUSINESS"])
        
        # Opening Balance
        self.opening_balance_edit = QDoubleSpinBox()
        self.opening_balance_edit.setRange(0, 10000000)
        self.opening_balance_edit.setDecimals(2)
        self.opening_balance_edit.setPrefix("$")
        
        # Notes
        self.notes_edit = QTextEdit()
        
        # Add fields to form
        form_layout.addRow("Account Name*:", self.name_edit)
        form_layout.addRow("Account Number*:", self.account_number_edit)
        form_layout.addRow("Bank Name*:", self.bank_name_edit)
        form_layout.addRow("Branch Name:", self.branch_name_edit)
        form_layout.addRow("Account Type*:", self.account_type_combo)
        form_layout.addRow("Opening Balance*:", self.opening_balance_edit)
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Buttons
        button_box = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        
        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_box.addWidget(self.save_btn)
        button_box.addWidget(self.cancel_btn)
        
        layout.addLayout(form_layout)
        layout.addLayout(button_box)
    
    def load_account_data(self):
        with get_db_session() as session:
            account = session.query(BankAccount).get(self.account_id)
            if account:
                self.name_edit.setText(account.name)
                self.account_number_edit.setText(account.account_number)
                self.bank_name_edit.setText(account.bank_name)
                self.branch_name_edit.setText(account.branch_name or "")
                
                index = self.account_type_combo.findText(account.account_type or "CHECKING")
                if index >= 0:
                    self.account_type_combo.setCurrentIndex(index)
                
                self.opening_balance_edit.setValue(float(account.opening_balance or 0))
                self.notes_edit.setPlainText(account.notes or "")
    
    def get_data(self):
        return {
            'name': self.name_edit.text().strip(),
            'account_number': self.account_number_edit.text().strip(),
            'bank_name': self.bank_name_edit.text().strip(),
            'branch_name': self.branch_name_edit.text().strip() or None,
            'account_type': self.account_type_combo.currentText(),
            'opening_balance': Decimal(str(self.opening_balance_edit.value())),
            'current_balance': Decimal(str(self.opening_balance_edit.value())),
            'notes': self.notes_edit.toPlainText().strip() or None
        }

class BankAccountsWidget(QWidget):
    # Signals
    account_updated = Signal()
    
    def __init__(self, controllers, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.setup_ui()
        self.load_accounts()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QHBoxLayout()
        title = QLabel("Bank Accounts")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.add_btn = QPushButton("Add Account")
        self.add_btn.clicked.connect(self.add_account)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.add_btn)
        
        # Accounts Table
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(6)
        self.accounts_table.setHorizontalHeaderLabels([
            "Account Name", "Account Number", "Bank Name", 
            "Type", "Balance", "Actions"
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.verticalHeader().setVisible(False)
        
        layout.addLayout(header)
        layout.addWidget(self.accounts_table)
    
    def load_accounts(self):
        self.accounts_table.setRowCount(0)
        
        with get_db_session() as session:
            accounts = session.query(BankAccount).all()
            
            for row, account in enumerate(accounts):
                self.accounts_table.insertRow(row)
                
                # Account details
                self.accounts_table.setItem(row, 0, QTableWidgetItem(account.name))
                self.accounts_table.setItem(row, 1, QTableWidgetItem(account.account_number))
                self.accounts_table.setItem(row, 2, QTableWidgetItem(account.bank_name))
                self.accounts_table.setItem(row, 3, QTableWidgetItem(account.account_type or "-"))
                
                # Balance with currency formatting
                balance_item = QTableWidgetItem(f"${account.current_balance:,.2f}")
                balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.accounts_table.setItem(row, 4, balance_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                
                view_btn = QPushButton("View")
                view_btn.clicked.connect(lambda _, a=account.id: self.view_account(a))
                
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda _, a=account.id: self.edit_account(a))
                
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda _, a=account.id: self.delete_account(a))
                
                actions_layout.addWidget(view_btn)
                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                actions_layout.setSpacing(2)
                
                self.accounts_table.setCellWidget(row, 5, actions_widget)
            
            # Resize columns to contents
            self.accounts_table.resizeColumnsToContents()
    
    def add_account(self):
        dialog = BankAccountDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                account = BankAccount(**data)
                
                with get_db_session() as session:
                    session.add(account)
                    session.commit()
                
                self.load_accounts()
                QMessageBox.information(self, "Success", "Bank account added successfully!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to add bank account: {str(e)}")
    
    def edit_account(self, account_id):
        dialog = BankAccountDialog(account_id, self)
        if dialog.exec() == QDialog.Accepted:
            try:
                data = dialog.get_data()
                
                with get_db_session() as session:
                    account = session.query(BankAccount).get(account_id)
                    if account:
                        for key, value in data.items():
                            setattr(account, key, value)
                        session.commit()
                        self.load_accounts()
                        QMessageBox.information(self, "Success", "Bank account updated successfully!")
                    else:
                        QMessageBox.warning(self, "Not Found", "Bank account not found!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update bank account: {str(e)}")
    
    def view_account(self, account_id):
        # TODO: Implement detailed view with transactions
        pass
    
    def delete_account(self, account_id):
        reply = QMessageBox.question(
            self, 
            "Confirm Delete", 
            "Are you sure you want to delete this bank account? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                with get_db_session() as session:
                    account = session.query(BankAccount).get(account_id)
                    if account:
                        # Check for associated transactions
                        transaction_count = session.query(BankTransaction)\
                            .filter_by(bank_account_id=account_id)\
                            .count()
                        
                        if transaction_count > 0:
                            QMessageBox.warning(
                                self,
                                "Cannot Delete",
                                f"Cannot delete account with {transaction_count} transactions. "
                                "Please delete or reassign the transactions first."
                            )
                            return
                        
                        session.delete(account)
                        session.commit()
                        self.load_accounts()
                        QMessageBox.information(self, "Success", "Bank account deleted successfully!")
                    else:
                        QMessageBox.warning(self, "Not Found", "Bank account not found!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete bank account: {str(e)}")
