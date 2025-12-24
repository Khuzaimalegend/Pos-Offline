try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
        QDialog, QFormLayout, QLineEdit, QMessageBox, QHBoxLayout, QComboBox,
        QCheckBox, QSpinBox, QGroupBox, QTabWidget, QDateEdit
    )
    from PySide6.QtCore import QDate, QTimer
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
        QDialog, QFormLayout, QLineEdit, QMessageBox, QHBoxLayout, QComboBox,
        QCheckBox, QSpinBox, QGroupBox, QTabWidget, QDateEdit
    )
    from PyQt6.QtCore import QDate, QTimer
from datetime import datetime, timedelta
from pos_app.models.database import Expense
from pos_app.utils.document_generator import DocumentGenerator


class CreateRecurringExpenseDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Setup Recurring Expense")
        layout = QFormLayout(self)

        self.title_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.category_input = QLineEdit()

        # Recurring options
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"])

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate().addYears(1))

        self.auto_create = QCheckBox("Automatically create expenses")
        self.auto_create.setChecked(True)

        layout.addRow("Title:", self.title_input)
        layout.addRow("Amount:", self.amount_input)
        layout.addRow("Category:", self.category_input)
        layout.addRow("Frequency:", self.frequency_combo)
        layout.addRow("Start Date:", self.start_date)
        layout.addRow("End Date:", self.end_date)
        layout.addRow(self.auto_create)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Recurring")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.save_recurring)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def save_recurring(self):
        try:
            title = self.title_input.text()
            try:
                amount = float(self.amount_input.text())
            except (ValueError, TypeError):
                amount = 0.0
            category = self.category_input.text() or None
            frequency = self.frequency_combo.currentText()
            # PySide6 uses toPython(), PyQt6 uses toPyDate()
            try:
                start_date = self.start_date.date().toPython()
                end_date = self.end_date.date().toPython()
            except AttributeError:
                start_date = self.start_date.date().toPyDate()
                end_date = self.end_date.date().toPyDate()
            auto_create = self.auto_create.isChecked()

            recurring = self.controller.create_recurring_expense(
                title, amount, category, frequency, start_date, end_date, auto_create
            )
            QMessageBox.information(self, "Saved", f"Recurring expense setup: {recurring.title}")
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))


class EditRecurringExpenseDialog(QDialog):
    def __init__(self, controller, recurring_expense, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.recurring_expense = recurring_expense
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Edit Recurring Expense")
        layout = QFormLayout(self)

        self.title_input = QLineEdit(self.recurring_expense.title)
        self.amount_input = QLineEdit(str(self.recurring_expense.amount))
        self.category_input = QLineEdit(self.recurring_expense.category or "")

        # Recurring options
        self.frequency_combo = QComboBox()
        self.frequency_combo.addItems(["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"])
        self.frequency_combo.setCurrentText(self.recurring_expense.frequency)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        if self.recurring_expense.start_date:
            self.start_date.setDate(self.recurring_expense.start_date)
        else:
            self.start_date.setDate(QDate.currentDate())

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        if self.recurring_expense.end_date:
            self.end_date.setDate(self.recurring_expense.end_date)
        else:
            self.end_date.setDate(QDate.currentDate().addYears(1))

        self.auto_create = QCheckBox("Automatically create expenses")
        self.auto_create.setChecked(self.recurring_expense.auto_create)

        layout.addRow("Title:", self.title_input)
        layout.addRow("Amount:", self.amount_input)
        layout.addRow("Category:", self.category_input)
        layout.addRow("Frequency:", self.frequency_combo)
        layout.addRow("Start Date:", self.start_date)
        layout.addRow("End Date:", self.end_date)
        layout.addRow(self.auto_create)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Update Recurring")
        cancel_btn = QPushButton("Cancel")

        save_btn.clicked.connect(self.update_recurring)
        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

    def update_recurring(self):
        try:
            title = self.title_input.text()
            try:
                amount = float(self.amount_input.text())
            except (ValueError, TypeError):
                amount = 0.0
            category = self.category_input.text() or None
            frequency = self.frequency_combo.currentText()
            start_date = self.start_date.date().toPython()
            end_date = self.end_date.date().toPython()
            auto_create = self.auto_create.isChecked()

            updated = self.controller.update_recurring_expense(
                self.recurring_expense.title, title, amount, category,
                frequency, start_date, end_date, auto_create
            )
            QMessageBox.information(self, "Updated", f"Recurring expense updated: {updated.title}")
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))


class CreateExpenseDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Record Expense")
        layout = QFormLayout(self)
        self.title_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.category_input = QLineEdit()
        layout.addRow("Title:", self.title_input)
        layout.addRow("Amount:", self.amount_input)
        layout.addRow("Category:", self.category_input)
        btn = QPushButton("Save")
        btn.clicked.connect(self.save_expense)
        layout.addRow(btn)

    def save_expense(self):
        try:
            title = self.title_input.text()
            try:
                amount = float(self.amount_input.text())
            except (ValueError, TypeError):
                amount = 0.0
            category = self.category_input.text() or None
            e = self.controller.record_expense(title, amount, category)
            QMessageBox.information(self, "Saved", f"Expense recorded: Rs {e.amount:,.2f}")
            self.accept()
        except Exception as exc:
            QMessageBox.warning(self, "Error", str(exc))


class ExpensesWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        # Ensure clean transaction state before loading data
        try:
            self.controller.session.rollback()
        except Exception as e:
            pass
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("📉 Expenses")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Toolbar with tabs
        toolbar = QHBoxLayout()

        # Create tabs
        self.tabs = QTabWidget()

        # Regular Expenses Tab
        self.expenses_tab = QWidget()
        self.setup_expenses_tab()
        self.tabs.addTab(self.expenses_tab, "Regular Expenses")

        # Recurring Expenses Tab
        self.recurring_tab = QWidget()
        self.setup_recurring_tab()
        self.tabs.addTab(self.recurring_tab, "Recurring Expenses")

        layout.addWidget(self.tabs)

    def setup_expenses_tab(self):
        layout = QVBoxLayout(self.expenses_tab)

        # Toolbar for regular expenses
        toolbar = QHBoxLayout()
        add_btn = QPushButton("✨ New Expense")
        add_btn.clicked.connect(self.open_create_expense)
        toolbar.addWidget(add_btn)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        toolbar.addWidget(QLabel("From:"))
        toolbar.addWidget(self.start_date)
        toolbar.addWidget(QLabel("To:"))
        toolbar.addWidget(self.end_date)

        export_btn = QPushButton("📄 Export CSV")
        export_btn.clicked.connect(self.export_csv)
        toolbar.addWidget(export_btn)

        layout.addLayout(toolbar)

        # Regular expenses table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Title", "Amount", "Category", "Date"])
        layout.addWidget(self.table)
        self.load_expenses()

    def setup_recurring_tab(self):
        layout = QVBoxLayout(self.recurring_tab)

        # Toolbar for recurring expenses
        toolbar = QHBoxLayout()
        add_btn = QPushButton("➕ New Recurring")
        add_btn.clicked.connect(self.open_create_recurring)
        toolbar.addWidget(add_btn)

        process_btn = QPushButton("⚡ Process Due")
        process_btn.clicked.connect(self.process_recurring_expenses)
        toolbar.addWidget(process_btn)

        layout.addLayout(toolbar)

        # Recurring expenses table
        self.recurring_table = QTableWidget(0, 6)
        self.recurring_table.setHorizontalHeaderLabels(["Title", "Amount", "Frequency", "Next Due", "Auto Create", "Actions"])
        layout.addWidget(self.recurring_table)
        self.load_recurring_expenses()

    def load_expenses(self):
        try:
            try:
                start = self.start_date.date().toPython()
                end = self.end_date.date().toPython()
            except AttributeError:
                start = self.start_date.date().toPyDate()
                end = self.end_date.date().toPyDate()
            rows = self.controller.list_expenses(start, end)
            self.table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                self.table.setItem(i, 0, QTableWidgetItem(r.title))
                self.table.setItem(i, 1, QTableWidgetItem(f"Rs {r.amount:,.2f}"))
                self.table.setItem(i, 2, QTableWidgetItem(r.category or ""))
                self.table.setItem(i, 3, QTableWidgetItem(str(r.expense_date)))
        except Exception as e:
            print(f"Error loading expenses: {e}")
            # Rollback the transaction on error
            try:
                self.controller.session.rollback()
            except Exception as e:
                pass
            self.table.setRowCount(0)

    def load_recurring_expenses(self):
        try:
            # Get recurring expenses from controller
            recurring_expenses = self.controller.list_recurring_expenses()
            self.recurring_table.setRowCount(len(recurring_expenses))

            for i, rec in enumerate(recurring_expenses):
                self.recurring_table.setItem(i, 0, QTableWidgetItem(rec.title))
                self.recurring_table.setItem(i, 1, QTableWidgetItem(f"Rs {rec.amount:,.2f}"))
                self.recurring_table.setItem(i, 2, QTableWidgetItem(rec.frequency))
                self.recurring_table.setItem(i, 3, QTableWidgetItem(str(rec.next_due_date) if rec.next_due_date else "N/A"))
                self.recurring_table.setItem(i, 4, QTableWidgetItem("Yes" if rec.auto_create else "No"))

                # Add action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(2, 2, 2, 2)

                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda checked, idx=i: self.edit_recurring_expense(idx))
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda checked, idx=i: self.delete_recurring_expense(idx))

                actions_layout.addWidget(edit_btn)
                actions_layout.addWidget(delete_btn)
                self.recurring_table.setCellWidget(i, 5, actions_widget)
        except Exception as e:
            print(f"Error loading recurring expenses: {e}")
            try:
                self.controller.session.rollback()
            except Exception as e:
                pass
            self.recurring_table.setRowCount(0)

    def open_create_expense(self):
        dlg = CreateExpenseDialog(self.controller, self)
        if dlg.exec() == QDialog.Accepted:
            self.load_expenses()

    def open_create_recurring(self):
        dlg = CreateRecurringExpenseDialog(self.controller, self)
        if dlg.exec() == QDialog.Accepted:
            self.load_recurring_expenses()

    def process_recurring_expenses(self):
        try:
            count = self.controller.process_recurring_expenses()
            QMessageBox.information(self, "Processed", f"Created {count} recurring expenses")
            self.load_expenses()  # Refresh regular expenses to show new ones
            self.load_recurring_expenses()  # Refresh recurring list
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to process recurring expenses: {str(e)}")

    def edit_recurring_expense(self, index):
        # Get the recurring expense from the table
        title_item = self.recurring_table.item(index, 0)
        if title_item:
            title = title_item.text()
            try:
                # Find the recurring expense by title
                recurring_expenses = self.controller.list_recurring_expenses()
                recurring = next((r for r in recurring_expenses if r.title == title), None)

                if recurring:
                    dlg = EditRecurringExpenseDialog(self.controller, recurring, self)
                    if dlg.exec() == QDialog.Accepted:
                        self.load_recurring_expenses()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to edit recurring expense: {str(e)}")

    def delete_recurring_expense(self, index):
        title_item = self.recurring_table.item(index, 0)
        if title_item:
            title = title_item.text()
            reply = QMessageBox.question(self, "Delete Recurring Expense",
                                        f"Delete recurring expense '{title}'?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    self.controller.delete_recurring_expense(title)
                    QMessageBox.information(self, "Deleted", "Recurring expense deleted")
                    self.load_recurring_expenses()
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to delete: {str(e)}")

    def export_csv(self):
        try:
            start = self.start_date.date().toPython()
            end = self.end_date.date().toPython()
        except AttributeError:
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
        path = self.controller.export_expenses_csv(start, end)
        QMessageBox.information(self, "Exported", f"Expenses exported to: {path}")
