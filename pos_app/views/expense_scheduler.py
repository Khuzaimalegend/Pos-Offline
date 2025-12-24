try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QCheckBox, QSpinBox
    )
    from PySide6.QtCore import Qt, QDate, QTimer
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QCheckBox, QSpinBox
    )
    from PyQt6.QtCore import Qt, QDate, QTimer
from datetime import datetime, timedelta
import logging

class ExpenseSchedulerWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("📅 Expense Scheduler")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        
        # Recurring Expenses
        recurring_tab = self.create_recurring_tab()
        tabs.addTab(recurring_tab, "🔄 Recurring Expenses")
        
        # Scheduled Payments
        scheduled_tab = self.create_scheduled_tab()
        tabs.addTab(scheduled_tab, "📋 Scheduled Payments")
        
        # Expense Categories
        categories_tab = self.create_categories_tab()
        tabs.addTab(categories_tab, "📂 Categories")
        
        layout.addWidget(tabs)

    def create_recurring_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Actions
        actions_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Add Recurring Expense")
        add_btn.setProperty('accent', 'Qt.green')
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.add_recurring_expense)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setProperty('accent', 'Qt.blue')
        edit_btn.setMinimumHeight(40)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setProperty('accent', 'Qt.red')
        delete_btn.setMinimumHeight(40)
        
        actions_layout.addWidget(add_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Recurring expenses table
        self.recurring_table = QTableWidget()
        self.recurring_table.setColumnCount(7)
        self.recurring_table.setHorizontalHeaderLabels([
            "Title", "Amount", "Frequency", "Next Due", "Category", "Status", "Actions"
        ])
        
        layout.addWidget(self.recurring_table)
        self.load_recurring_expenses()
        return widget

    def create_scheduled_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter controls
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Paid", "Overdue"])
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addWidget(QLabel("Period:"))
        self.period_filter = QComboBox()
        self.period_filter.addItems(["This Week", "This Month", "Next 30 Days", "All"])
        filter_layout.addWidget(self.period_filter)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.filter_scheduled)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        
        pay_btn = QPushButton("💰 Mark as Paid")
        pay_btn.setProperty('accent', 'Qt.green')
        pay_btn.clicked.connect(self.mark_as_paid)
        filter_layout.addWidget(pay_btn)
        
        layout.addWidget(filter_frame)

        # Scheduled payments table
        self.scheduled_table = QTableWidget()
        self.scheduled_table.setColumnCount(7)
        self.scheduled_table.setHorizontalHeaderLabels([
            "Due Date", "Title", "Amount", "Category", "Status", "Days Overdue", "Actions"
        ])
        
        layout.addWidget(self.scheduled_table)
        self.load_scheduled_payments()
        return widget

    def create_categories_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Category management
        actions_layout = QHBoxLayout()
        
        add_cat_btn = QPushButton("➕ Add Category")
        add_cat_btn.setProperty('accent', 'Qt.green')
        add_cat_btn.clicked.connect(self.add_category)
        
        edit_cat_btn = QPushButton("✏️ Edit Category")
        edit_cat_btn.setProperty('accent', 'Qt.blue')
        
        actions_layout.addWidget(add_cat_btn)
        actions_layout.addWidget(edit_cat_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Categories list
        self.categories_table = QTableWidget()
        self.categories_table.setColumnCount(4)
        self.categories_table.setHorizontalHeaderLabels([
            "Category", "Subcategory", "Total Expenses", "Monthly Average"
        ])
        
        layout.addWidget(self.categories_table)
        self.load_categories()
        return widget

    def add_recurring_expense(self):
        dialog = RecurringExpenseDialog(self, self.controller)
        if dialog.exec() == QDialog.Accepted:
            try:
                from pos_app.models.database import Expense, ExpenseSchedule
                
                # Create recurring expense
                expense = Expense(
                    title=dialog.title.text(),
                    amount=dialog.amount.value(),
                    category=dialog.category.text(),
                    subcategory=dialog.subcategory.text(),
                    frequency=dialog.frequency.currentText().upper().replace(" ", "_"),
                    is_recurring=True,
                    next_due_date=dialog.next_due.date().toPython(),
                    payment_method=dialog.payment_method.currentText().upper().replace(" ", "_"),
                    notes=dialog.notes.toPlainText(),
                    created_by="Admin"
                )
                
                self.controller.session.add(expense)
                self.controller.session.commit()
                
                # Generate scheduled payments
                self.generate_scheduled_payments(expense)
                
                QMessageBox.information(self, "Success", "Recurring expense added successfully!")
                self.load_recurring_expenses()
                self.load_scheduled_payments()
                
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to add recurring expense: {str(e)}")

    def generate_scheduled_payments(self, expense):
        try:
            from pos_app.models.database import ExpenseSchedule
            
            # Generate next 12 scheduled payments
            current_date = expense.next_due_date
            
            for i in range(12):
                schedule = ExpenseSchedule(
                    expense_id=expense.id,
                    scheduled_date=current_date,
                    amount=expense.amount,
                    status="PENDING"
                )
                
                self.controller.session.add(schedule)
                
                # Calculate next date based on frequency
                if expense.frequency == "MONTHLY":
                    if current_date.month == 12:
                        current_date = current_date.replace(year=current_date.year + 1, month=1)
                    else:
                        current_date = current_date.replace(month=current_date.month + 1)
                elif expense.frequency == "WEEKLY":
                    current_date = current_date + timedelta(weeks=1)
                elif expense.frequency == "DAILY":
                    current_date = current_date + timedelta(days=1)
                elif expense.frequency == "YEARLY":
                    current_date = current_date.replace(year=current_date.year + 1)
                elif expense.frequency == "QUARTERLY":
                    if current_date.month <= 9:
                        current_date = current_date.replace(month=current_date.month + 3)
                    else:
                        current_date = current_date.replace(year=current_date.year + 1, month=current_date.month - 9)
            
            self.controller.session.commit()
            
        except Exception as e:
            self.controller.session.rollback()
            raise e

    def load_recurring_expenses(self):
        try:
            from pos_app.models.database import Expense
            
            expenses = self.controller.session.query(Expense).filter(  # TODO: Add .all() or .first()
                Expense.is_recurring == True
            ).all()
            
            self.recurring_table.setRowCount(len(expenses))
            
            for i, expense in enumerate(expenses):
                self.recurring_table.setItem(i, 0, QTableWidgetItem(expense.title))
                self.recurring_table.setItem(i, 1, QTableWidgetItem(f"Rs {expense.amount:,.2f}"))
                self.recurring_table.setItem(i, 2, QTableWidgetItem(expense.frequency.replace("_", " ").title()))
                
                next_due = expense.next_due_date.strftime('%Y-%m-%d') if expense.next_due_date else "Not Set"
                self.recurring_table.setItem(i, 3, QTableWidgetItem(next_due))
                
                self.recurring_table.setItem(i, 4, QTableWidgetItem(expense.category or ""))
                self.recurring_table.setItem(i, 5, QTableWidgetItem("Active"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load recurring expenses: {str(e)}")

    def load_scheduled_payments(self):
        try:
            from pos_app.models.database import ExpenseSchedule, Expense
            
            schedules = self.controller.session.query(ExpenseSchedule).join(Expense).filter(  # TODO: Add .all() or .first()
                ExpenseSchedule.status.in_(["PENDING", "OVERDUE"])
            ).order_by(ExpenseSchedule.scheduled_date).all()
            
            self.scheduled_table.setRowCount(len(schedules))
            
            today = datetime.now().date()
            
            for i, schedule in enumerate(schedules):
                due_date = schedule.scheduled_date.date() if schedule.scheduled_date else today
                days_overdue = (today - due_date).days if due_date < today else 0
                
                # Color code overdue items
                due_item = QTableWidgetItem(due_date.strftime('%Y-%m-%d'))
                if days_overdue > 0:
                    due_item.setForeground(Qt.red)
                    schedule.status = "OVERDUE"
                
                self.scheduled_table.setItem(i, 0, due_item)
                self.scheduled_table.setItem(i, 1, QTableWidgetItem(schedule.expense.title))
                self.scheduled_table.setItem(i, 2, QTableWidgetItem(f"Rs {schedule.amount:,.2f}"))
                self.scheduled_table.setItem(i, 3, QTableWidgetItem(schedule.expense.category or ""))
                
                status_item = QTableWidgetItem(schedule.status)
                if schedule.status == "OVERDUE":
                    status_item.setForeground(Qt.red)
                self.scheduled_table.setItem(i, 4, status_item)
                
                overdue_item = QTableWidgetItem(str(days_overdue) if days_overdue > 0 else "")
                if days_overdue > 0:
                    overdue_item.setForeground(Qt.red)
                self.scheduled_table.setItem(i, 5, overdue_item)
                
                # Store schedule ID
                self.scheduled_table.item(i, 0).setData(Qt.UserRole, schedule.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load scheduled payments: {str(e)}")

    def load_categories(self):
        try:
            from pos_app.models.database import Expense
            from sqlalchemy import func
            
            # Get category statistics
            categories = self.controller.session.query(
                Expense.category,
                Expense.subcategory,
                func.sum(Expense.amount).label('total'),
                func.avg(Expense.amount).label('average')
            ).group_by(Expense.category, Expense.subcategory).all()
            
            self.categories_table.setRowCount(len(categories))
            
            for i, (category, subcategory, total, average) in enumerate(categories):
                self.categories_table.setItem(i, 0, QTableWidgetItem(category or ""))
                self.categories_table.setItem(i, 1, QTableWidgetItem(subcategory or ""))
                self.categories_table.setItem(i, 2, QTableWidgetItem(f"Rs {total:,.2f}" if total else "Rs 0.00"))
                self.categories_table.setItem(i, 3, QTableWidgetItem(f"Rs {average:,.2f}" if average else "Rs 0.00"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load categories: {str(e)}")

    def mark_as_paid(self):
        selected_rows = self.scheduled_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a scheduled payment to mark as paid")
            return
        
        try:
            from pos_app.models.database import ExpenseSchedule
            
            for row in selected_rows:
                schedule_id = self.scheduled_table.item(row.row(), 0).data(Qt.UserRole)
                schedule = self.controller.session.get(ExpenseSchedule, schedule_id)
                
                if schedule:
                    schedule.status = "PAID"
                    schedule.paid_date = datetime.now()
            
            self.controller.session.commit()
            QMessageBox.information(self, "Success", "Scheduled payment(s) marked as paid!")
            self.load_scheduled_payments()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to mark as paid: {str(e)}")

    def filter_scheduled(self):
        self.load_scheduled_payments()

    def add_category(self):
        # Simple input dialog for adding categories
        from PySide6.QtWidgets import QInputDialog
        
        category, ok = QInputDialog.getText(self, "Add Category", "Category Name:")
        if ok and category:
            subcategory, ok = QInputDialog.getText(self, "Add Subcategory", "Subcategory Name (optional):")
            if ok:
                # Categories are created automatically when expenses are added
                QMessageBox.information(self, "Info", "Categories are created automatically when you add expenses with new category names.")


class RecurringExpenseDialog(QDialog):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Add Recurring Expense")
        self.setMinimumSize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.title = QLineEdit()
        self.title.setPlaceholderText("e.g., Office Rent, Electricity Bill")
        layout.addRow("Title:", self.title)

        self.amount = QDoubleSpinBox()
        self.amount.setRange(0, 1000000)
        self.amount.setSuffix(" Rs")
        layout.addRow("Amount:", self.amount)

        self.frequency = QComboBox()
        self.frequency.addItems(["Daily", "Weekly", "Monthly", "Quarterly", "Yearly"])
        self.frequency.setCurrentText("Monthly")
        layout.addRow("Frequency:", self.frequency)

        self.next_due = QDateEdit()
        self.next_due.setDate(QDate.currentDate().addDays(30))
        self.next_due.setCalendarPopup(True)
        layout.addRow("Next Due Date:", self.next_due)

        self.category = QLineEdit()
        self.category.setPlaceholderText("e.g., Utilities, Rent, Insurance")
        layout.addRow("Category:", self.category)

        self.subcategory = QLineEdit()
        self.subcategory.setPlaceholderText("e.g., Electricity, Water, Internet")
        layout.addRow("Subcategory:", self.subcategory)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Bank Transfer", "Credit Card", "Cheque"])
        layout.addRow("Payment Method:", self.payment_method)

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
