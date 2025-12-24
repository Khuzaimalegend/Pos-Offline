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

class OutstandingPurchasesWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("⚠️ Outstanding Purchases")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Summary cards
        summary_frame = self.create_summary_section()
        layout.addWidget(summary_frame)

        # Tabs
        tabs = QTabWidget()
        
        # Overdue tab
        overdue_tab = self.create_overdue_tab()
        tabs.addTab(overdue_tab, "🚨 Overdue")
        
        # Due Soon tab
        due_soon_tab = self.create_due_soon_tab()
        tabs.addTab(due_soon_tab, "⏰ Due Soon")
        
        # All Outstanding tab
        all_tab = self.create_all_outstanding_tab()
        tabs.addTab(all_tab, "📋 All Outstanding")
        
        # Follow-up tab
        followup_tab = self.create_followup_tab()
        tabs.addTab(followup_tab, "📞 Follow-up")
        
        layout.addWidget(tabs)

    def create_summary_section(self):
        frame = QFrame()
        frame.setProperty('role', 'card')
        layout = QHBoxLayout(frame)

        # Total Outstanding
        total_frame = QFrame()
        total_frame.setProperty('role', 'card')
        total_layout = QVBoxLayout(total_frame)
        
        self.total_outstanding_label = QLabel("Rs 0.00")
        self.total_outstanding_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #ef4444;")
        total_layout.addWidget(QLabel("💰 Total Outstanding"))
        total_layout.addWidget(self.total_outstanding_label)
        
        # Overdue Count
        overdue_frame = QFrame()
        overdue_frame.setProperty('role', 'card')
        overdue_layout = QVBoxLayout(overdue_frame)
        
        self.overdue_count_label = QLabel("0")
        self.overdue_count_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #dc2626;")
        overdue_layout.addWidget(QLabel("🚨 Overdue"))
        overdue_layout.addWidget(self.overdue_count_label)
        
        # Due This Week
        week_frame = QFrame()
        week_frame.setProperty('role', 'card')
        week_layout = QVBoxLayout(week_frame)
        
        self.week_count_label = QLabel("0")
        self.week_count_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #f59e0b;")
        week_layout.addWidget(QLabel("📅 Due This Week"))
        week_layout.addWidget(self.week_count_label)
        
        # Suppliers Count
        suppliers_frame = QFrame()
        suppliers_frame.setProperty('role', 'card')
        suppliers_layout = QVBoxLayout(suppliers_frame)
        
        self.suppliers_count_label = QLabel("0")
        self.suppliers_count_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #3b82f6;")
        suppliers_layout.addWidget(QLabel("🏢 Suppliers"))
        suppliers_layout.addWidget(self.suppliers_count_label)
        
        layout.addWidget(total_frame)
        layout.addWidget(overdue_frame)
        layout.addWidget(week_frame)
        layout.addWidget(suppliers_frame)
        
        self.update_summary()
        return frame

    def create_overdue_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Actions for overdue
        actions_layout = QHBoxLayout()
        
        pay_btn = QPushButton("💰 Record Payment")
        pay_btn.setProperty('accent', 'Qt.green')
        pay_btn.setMinimumHeight(40)
        pay_btn.clicked.connect(self.record_payment)
        
        followup_btn = QPushButton("📞 Schedule Follow-up")
        followup_btn.setProperty('accent', 'Qt.blue')
        followup_btn.setMinimumHeight(40)
        followup_btn.clicked.connect(self.schedule_followup)
        
        extend_btn = QPushButton("📅 Extend Due Date")
        extend_btn.setProperty('accent', 'orange')
        extend_btn.setMinimumHeight(40)
        followup_btn.clicked.connect(self.extend_due_date)
        
        actions_layout.addWidget(pay_btn)
        actions_layout.addWidget(followup_btn)
        actions_layout.addWidget(extend_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Overdue table
        self.overdue_table = QTableWidget()
        self.overdue_table.setColumnCount(8)
        self.overdue_table.setHorizontalHeaderLabels([
            "Purchase #", "Supplier", "Due Date", "Days Overdue", 
            "Amount Due", "Priority", "Last Contact", "Actions"
        ])
        self.overdue_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.overdue_table)
        self.load_overdue_purchases()
        return widget

    def create_due_soon_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter for due soon
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Show purchases due in:"))
        
        self.due_period = QComboBox()
        self.due_period.addItems(["Next 7 days", "Next 15 days", "Next 30 days"])
        self.due_period.currentTextChanged.connect(self.load_due_soon_purchases)
        filter_layout.addWidget(self.due_period)
        
        filter_layout.addStretch()
        
        remind_btn = QPushButton("🔔 Set Reminder")
        remind_btn.setProperty('accent', 'Qt.blue')
        remind_btn.clicked.connect(self.set_reminder)
        filter_layout.addWidget(remind_btn)
        
        layout.addWidget(filter_frame)

        # Due soon table
        self.due_soon_table = QTableWidget()
        self.due_soon_table.setColumnCount(7)
        self.due_soon_table.setHorizontalHeaderLabels([
            "Purchase #", "Supplier", "Due Date", "Days Until Due", 
            "Amount Due", "Priority", "Actions"
        ])
        self.due_soon_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.due_soon_table)
        self.load_due_soon_purchases()
        return widget

    def create_all_outstanding_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filters
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Supplier:"))
        self.supplier_filter = QComboBox()
        self.supplier_filter.addItem("All Suppliers", None)
        self.load_suppliers_filter()
        filter_layout.addWidget(self.supplier_filter)
        
        filter_layout.addWidget(QLabel("Priority:"))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["All", "LOW", "NORMAL", "HIGH", "URGENT"])
        filter_layout.addWidget(self.priority_filter)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.filter_outstanding)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        
        export_btn = QPushButton("📊 Export Report")
        export_btn.setProperty('accent', 'Qt.blue')
        export_btn.clicked.connect(self.export_report)
        filter_layout.addWidget(export_btn)
        
        layout.addWidget(filter_frame)

        # All outstanding table
        self.all_outstanding_table = QTableWidget()
        self.all_outstanding_table.setColumnCount(9)
        self.all_outstanding_table.setHorizontalHeaderLabels([
            "Purchase #", "Supplier", "Purchase Date", "Due Date", 
            "Total Amount", "Paid Amount", "Outstanding", "Priority", "Status"
        ])
        self.all_outstanding_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.all_outstanding_table)
        self.load_all_outstanding()
        return widget

    def create_followup_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Follow-up actions
        actions_layout = QHBoxLayout()
        
        add_followup_btn = QPushButton("➕ Add Follow-up Note")
        add_followup_btn.setProperty('accent', 'Qt.green')
        add_followup_btn.setMinimumHeight(40)
        add_followup_btn.clicked.connect(self.add_followup_note)
        
        mark_contacted_btn = QPushButton("✅ Mark as Contacted")
        mark_contacted_btn.setProperty('accent', 'Qt.blue')
        mark_contacted_btn.setMinimumHeight(40)
        mark_contacted_btn.clicked.connect(self.mark_contacted)
        
        actions_layout.addWidget(add_followup_btn)
        actions_layout.addWidget(mark_contacted_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Follow-up table
        self.followup_table = QTableWidget()
        self.followup_table.setColumnCount(7)
        self.followup_table.setHorizontalHeaderLabels([
            "Purchase #", "Supplier", "Follow-up Date", "Amount Due", 
            "Contact Method", "Notes", "Status"
        ])
        self.followup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.followup_table)
        self.load_followups()
        return widget

    def update_summary(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            
            # Get all outstanding purchases
            outstanding_purchases = self.controller.session.query(Purchase).filter(  # TODO: Add .all() or .first()
                (Purchase.total_amount - Purchase.paid_amount) > 0
            ).all()
            
            total_outstanding = sum((p.total_amount - p.paid_amount) for p in outstanding_purchases)
            self.total_outstanding_label.setText(f"Rs {total_outstanding:,.2f}")
            
            # Count overdue
            today = datetime.now().date()
            overdue_count = 0
            week_count = 0
            suppliers_with_outstanding = set()
            
            for purchase in outstanding_purchases:
                suppliers_with_outstanding.add(purchase.supplier_id)
                
                if hasattr(purchase, 'delivery_date') and purchase.delivery_date:
                    due_date = purchase.delivery_date.date()
                    if due_date < today:
                        overdue_count += 1
                    elif due_date <= today + timedelta(days=7):
                        week_count += 1
            
            self.overdue_count_label.setText(str(overdue_count))
            self.week_count_label.setText(str(week_count))
            self.suppliers_count_label.setText(str(len(suppliers_with_outstanding)))
            
        except Exception as e:
            logging.exception("Failed to update summary")

    def load_overdue_purchases(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            
            today = datetime.now().date()
            
            overdue_purchases = self.controller.session.query(Purchase).join(Supplier).filter(  # TODO: Add .all() or .first()
                (Purchase.total_amount - Purchase.paid_amount) > 0,
                Purchase.delivery_date < datetime.now()
            ).all()
            
            self.overdue_table.setRowCount(len(overdue_purchases))
            
            for i, purchase in enumerate(overdue_purchases):
                self.overdue_table.setItem(i, 0, QTableWidgetItem(purchase.purchase_number or f"P-{purchase.id}"))
                self.overdue_table.setItem(i, 1, QTableWidgetItem(purchase.supplier.name if purchase.supplier else ""))
                
                due_date = purchase.delivery_date.strftime('%Y-%m-%d') if purchase.delivery_date else ""
                due_item = QTableWidgetItem(due_date)
                due_item.setForeground(Qt.red)
                self.overdue_table.setItem(i, 2, due_item)
                
                if purchase.delivery_date:
                    days_overdue = (today - purchase.delivery_date.date()).days
                    overdue_item = QTableWidgetItem(str(days_overdue))
                    overdue_item.setForeground(Qt.red)
                    self.overdue_table.setItem(i, 3, overdue_item)
                else:
                    self.overdue_table.setItem(i, 3, QTableWidgetItem("N/A"))
                
                amount_due = purchase.total_amount - purchase.paid_amount
                amount_item = QTableWidgetItem(f"Rs {amount_due:,.2f}")
                amount_item.setForeground(Qt.red)
                self.overdue_table.setItem(i, 4, amount_item)
                
                priority = getattr(purchase, 'priority', 'NORMAL')
                priority_item = QTableWidgetItem(priority)
                if priority == "URGENT":
                    priority_item.setForeground(Qt.red)
                elif priority == "HIGH":
                    priority_item.setForeground(Qt.darkRed)
                self.overdue_table.setItem(i, 5, priority_item)
                
                self.overdue_table.setItem(i, 6, QTableWidgetItem("Never"))  # Last contact placeholder
                
                # Store purchase ID
                self.overdue_table.item(i, 0).setData(Qt.UserRole, purchase.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load overdue purchases: {str(e)}")

    def load_due_soon_purchases(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            
            period_text = self.due_period.currentText()
            days = 7 if "7 days" in period_text else (15 if "15 days" in period_text else 30)
            
            today = datetime.now()
            future_date = today + timedelta(days=days)
            
            due_soon_purchases = self.controller.session.query(Purchase).join(Supplier).filter(  # TODO: Add .all() or .first()
                (Purchase.total_amount - Purchase.paid_amount) > 0,
                Purchase.delivery_date >= today,
                Purchase.delivery_date <= future_date
            ).all()
            
            self.due_soon_table.setRowCount(len(due_soon_purchases))
            
            for i, purchase in enumerate(due_soon_purchases):
                self.due_soon_table.setItem(i, 0, QTableWidgetItem(purchase.purchase_number or f"P-{purchase.id}"))
                self.due_soon_table.setItem(i, 1, QTableWidgetItem(purchase.supplier.name if purchase.supplier else ""))
                
                due_date = purchase.delivery_date.strftime('%Y-%m-%d') if purchase.delivery_date else ""
                self.due_soon_table.setItem(i, 2, QTableWidgetItem(due_date))
                
                if purchase.delivery_date:
                    days_until = (purchase.delivery_date.date() - today.date()).days
                    days_item = QTableWidgetItem(str(days_until))
                    if days_until <= 3:
                        days_item.setForeground(Qt.red)
                    elif days_until <= 7:
                        days_item.setForeground(Qt.darkYellow)
                    self.due_soon_table.setItem(i, 3, days_item)
                else:
                    self.due_soon_table.setItem(i, 3, QTableWidgetItem("N/A"))
                
                amount_due = purchase.total_amount - purchase.paid_amount
                self.due_soon_table.setItem(i, 4, QTableWidgetItem(f"Rs {amount_due:,.2f}"))
                
                priority = getattr(purchase, 'priority', 'NORMAL')
                self.due_soon_table.setItem(i, 5, QTableWidgetItem(priority))
                
                # Store purchase ID
                self.due_soon_table.item(i, 0).setData(Qt.UserRole, purchase.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load due soon purchases: {str(e)}")

    def load_all_outstanding(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            
            outstanding_purchases = self.controller.session.query(Purchase).join(Supplier).filter(  # TODO: Add .all() or .first()
                (Purchase.total_amount - Purchase.paid_amount) > 0
            ).order_by(Purchase.order_date.desc()).all()
            
            self.all_outstanding_table.setRowCount(len(outstanding_purchases))
            
            for i, purchase in enumerate(outstanding_purchases):
                self.all_outstanding_table.setItem(i, 0, QTableWidgetItem(purchase.purchase_number or f"P-{purchase.id}"))
                self.all_outstanding_table.setItem(i, 1, QTableWidgetItem(purchase.supplier.name if purchase.supplier else ""))
                
                order_date = purchase.order_date.strftime('%Y-%m-%d') if purchase.order_date else ""
                self.all_outstanding_table.setItem(i, 2, QTableWidgetItem(order_date))
                
                due_date = purchase.delivery_date.strftime('%Y-%m-%d') if purchase.delivery_date else ""
                self.all_outstanding_table.setItem(i, 3, QTableWidgetItem(due_date))
                
                self.all_outstanding_table.setItem(i, 4, QTableWidgetItem(f"Rs {purchase.total_amount:,.2f}"))
                self.all_outstanding_table.setItem(i, 5, QTableWidgetItem(f"Rs {purchase.paid_amount:,.2f}"))
                
                outstanding = purchase.total_amount - purchase.paid_amount
                outstanding_item = QTableWidgetItem(f"Rs {outstanding:,.2f}")
                if outstanding > 0:
                    outstanding_item.setForeground(Qt.red)
                self.all_outstanding_table.setItem(i, 6, outstanding_item)
                
                priority = getattr(purchase, 'priority', 'NORMAL')
                self.all_outstanding_table.setItem(i, 7, QTableWidgetItem(priority))
                
                self.all_outstanding_table.setItem(i, 8, QTableWidgetItem(purchase.status or ""))
                
                # Store purchase ID
                self.all_outstanding_table.item(i, 0).setData(Qt.UserRole, purchase.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load outstanding purchases: {str(e)}")

    def load_followups(self):
        # Placeholder for follow-up functionality
        pass

    def load_suppliers_filter(self):
        try:
            from pos_app.models.database import Supplier
            
            suppliers = self.controller.session.query(Supplier).filter(  # TODO: Add .all() or .first()
                Supplier.is_active == True
            ).all()
            
            for supplier in suppliers:
                self.supplier_filter.addItem(supplier.name, supplier.id)
                
        except Exception as e:
            logging.exception("Failed to load suppliers filter")

    def record_payment(self):
        # Get selected purchase
        current_table = self.get_current_table()
        selected_rows = current_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a purchase to record payment")
            return
        
        purchase_id = current_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        
        # Open payment dialog (you would implement this)
        QMessageBox.information(self, "Info", f"Record payment for purchase ID: {purchase_id}")

    def schedule_followup(self):
        current_table = self.get_current_table()
        selected_rows = current_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a purchase to schedule follow-up")
            return
        
        # Open follow-up dialog (you would implement this)
        QMessageBox.information(self, "Info", "Schedule follow-up dialog would open here")

    def extend_due_date(self):
        current_table = self.get_current_table()
        selected_rows = current_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a purchase to extend due date")
            return
        
        # Open due date extension dialog (you would implement this)
        QMessageBox.information(self, "Info", "Extend due date dialog would open here")

    def set_reminder(self):
        QMessageBox.information(self, "Info", "Reminder functionality would be implemented here")

    def filter_outstanding(self):
        self.load_all_outstanding()

    def export_report(self):
        QMessageBox.information(self, "Info", "Export report functionality would be implemented here")

    def add_followup_note(self):
        QMessageBox.information(self, "Info", "Add follow-up note dialog would open here")

    def mark_contacted(self):
        QMessageBox.information(self, "Info", "Mark as contacted functionality would be implemented here")

    def get_current_table(self):
        # Return the currently visible table based on active tab
        return self.overdue_table  # Simplified for now
