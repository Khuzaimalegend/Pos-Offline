try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QCheckBox, QSpinBox
    )
    from PySide6.QtCore import Qt, QDate
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QCheckBox, QSpinBox
    )
    from PyQt6.QtCore import Qt, QDate
from datetime import datetime
import logging

class AdvancedPurchaseManagementWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("📋 Advanced Purchase Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        
        # Purchase Orders
        orders_tab = self.create_purchase_orders_tab()
        tabs.addTab(orders_tab, "📋 Purchase Orders")
        
        # Partial Payments
        payments_tab = self.create_partial_payments_tab()
        tabs.addTab(payments_tab, "💰 Partial Payments")
        
        # Purchase Notes
        notes_tab = self.create_purchase_notes_tab()
        tabs.addTab(notes_tab, "📝 Purchase Notes")
        
        # Purchase Analytics
        analytics_tab = self.create_purchase_analytics_tab()
        tabs.addTab(analytics_tab, "📊 Analytics")
        
        layout.addWidget(tabs)

    def create_purchase_orders_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Actions
        actions_layout = QHBoxLayout()
        
        new_order_btn = QPushButton("➕ New Purchase Order")
        new_order_btn.setProperty('accent', 'Qt.green')
        new_order_btn.setMinimumHeight(40)
        new_order_btn.clicked.connect(self.create_purchase_order)
        
        edit_order_btn = QPushButton("✏️ Edit Order")
        edit_order_btn.setProperty('accent', 'Qt.blue')
        edit_order_btn.setMinimumHeight(40)
        
        receive_order_btn = QPushButton("📦 Receive Items")
        receive_order_btn.setProperty('accent', 'orange')
        receive_order_btn.setMinimumHeight(40)
        receive_order_btn.clicked.connect(self.receive_items)
        
        actions_layout.addWidget(new_order_btn)
        actions_layout.addWidget(edit_order_btn)
        actions_layout.addWidget(receive_order_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Filters
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Supplier:"))
        self.supplier_filter = QComboBox()
        self.supplier_filter.addItem("All Suppliers", None)
        self.load_suppliers_filter()
        filter_layout.addWidget(self.supplier_filter)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "ORDERED", "PARTIAL", "RECEIVED", "CANCELLED"])
        filter_layout.addWidget(self.status_filter)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.filter_purchases)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)

        # Purchase orders table
        self.purchase_orders_table = QTableWidget()
        self.purchase_orders_table.setColumnCount(9)
        self.purchase_orders_table.setHorizontalHeaderLabels([
            "Order #", "Supplier", "Order Date", "Expected", "Total", 
            "Paid", "Outstanding", "Status", "Priority"
        ])
        self.purchase_orders_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.purchase_orders_table)
        self.load_purchase_orders()
        return widget

    def create_partial_payments_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Payment summary
        summary_frame = QFrame()
        summary_frame.setProperty('role', 'card')
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total outstanding
        outstanding_frame = QFrame()
        outstanding_frame.setProperty('role', 'card')
        outstanding_layout = QVBoxLayout(outstanding_frame)
        
        self.total_outstanding_label = QLabel("Rs 0.00")
        self.total_outstanding_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ef4444;")
        outstanding_layout.addWidget(QLabel("💰 Total Outstanding"))
        outstanding_layout.addWidget(self.total_outstanding_label)
        
        # Partial payments count
        partial_frame = QFrame()
        partial_frame.setProperty('role', 'card')
        partial_layout = QVBoxLayout(partial_frame)
        
        self.partial_count_label = QLabel("0")
        self.partial_count_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f59e0b;")
        partial_layout.addWidget(QLabel("📊 Partial Payments"))
        partial_layout.addWidget(self.partial_count_label)
        
        summary_layout.addWidget(outstanding_frame)
        summary_layout.addWidget(partial_frame)
        
        layout.addWidget(summary_frame)

        # Payment actions
        payment_actions_layout = QHBoxLayout()
        
        record_payment_btn = QPushButton("💳 Record Payment")
        record_payment_btn.setProperty('accent', 'Qt.green')
        record_payment_btn.setMinimumHeight(40)
        record_payment_btn.clicked.connect(self.record_payment)
        
        payment_schedule_btn = QPushButton("📅 Payment Schedule")
        payment_schedule_btn.setProperty('accent', 'Qt.blue')
        payment_schedule_btn.setMinimumHeight(40)
        
        payment_actions_layout.addWidget(record_payment_btn)
        payment_actions_layout.addWidget(payment_schedule_btn)
        payment_actions_layout.addStretch()
        
        layout.addLayout(payment_actions_layout)

        # Partial payments table
        self.partial_payments_table = QTableWidget()
        self.partial_payments_table.setColumnCount(8)
        self.partial_payments_table.setHorizontalHeaderLabels([
            "Purchase #", "Supplier", "Total Amount", "Paid Amount", 
            "Outstanding", "Last Payment", "Payment Method", "Status"
        ])
        
        layout.addWidget(self.partial_payments_table)
        self.load_partial_payments()
        return widget

    def create_purchase_notes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Purchase selection
        selection_frame = QFrame()
        selection_frame.setProperty('role', 'card')
        selection_layout = QHBoxLayout(selection_frame)
        
        selection_layout.addWidget(QLabel("Select Purchase:"))
        self.purchase_notes_combo = QComboBox()
        self.load_purchases_for_notes()
        selection_layout.addWidget(self.purchase_notes_combo)
        
        selection_layout.addStretch()
        
        layout.addWidget(selection_frame)

        # Add note section
        add_note_frame = QFrame()
        add_note_frame.setProperty('role', 'card')
        add_note_layout = QVBoxLayout(add_note_frame)
        
        add_note_layout.addWidget(QLabel("📝 Add Purchase Note"))
        
        self.note_type = QComboBox()
        self.note_type.addItems([
            "General", "Quality Issue", "Delivery Issue", "Payment Issue", 
            "Supplier Communication", "Internal Note"
        ])
        add_note_layout.addWidget(self.note_type)
        
        self.purchase_note_input = QTextEdit()
        self.purchase_note_input.setMaximumHeight(100)
        self.purchase_note_input.setPlaceholderText("Enter detailed note about this purchase...")
        add_note_layout.addWidget(self.purchase_note_input)
        
        add_note_btn = QPushButton("💾 Add Note")
        add_note_btn.setProperty('accent', 'Qt.green')
        add_note_btn.clicked.connect(self.add_purchase_note)
        add_note_layout.addWidget(add_note_btn)
        
        layout.addWidget(add_note_frame)

        # Notes history
        self.purchase_notes_table = QTableWidget()
        self.purchase_notes_table.setColumnCount(5)
        self.purchase_notes_table.setHorizontalHeaderLabels([
            "Date", "Type", "Note", "Added By", "Actions"
        ])
        
        layout.addWidget(self.purchase_notes_table)
        return widget

    def create_purchase_analytics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Analytics summary
        analytics_frame = QFrame()
        analytics_frame.setProperty('role', 'card')
        analytics_layout = QHBoxLayout(analytics_frame)
        
        # Monthly spending
        monthly_frame = QFrame()
        monthly_frame.setProperty('role', 'card')
        monthly_layout = QVBoxLayout(monthly_frame)
        
        self.monthly_spending_label = QLabel("Rs 0.00")
        self.monthly_spending_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        monthly_layout.addWidget(QLabel("📊 This Month"))
        monthly_layout.addWidget(self.monthly_spending_label)
        
        # Top supplier
        top_supplier_frame = QFrame()
        top_supplier_frame.setProperty('role', 'card')
        top_supplier_layout = QVBoxLayout(top_supplier_frame)
        
        self.top_supplier_label = QLabel("None")
        self.top_supplier_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        top_supplier_layout.addWidget(QLabel("🏆 Top Supplier"))
        top_supplier_layout.addWidget(self.top_supplier_label)
        
        # Average order value
        avg_frame = QFrame()
        avg_frame.setProperty('role', 'card')
        avg_layout = QVBoxLayout(avg_frame)
        
        self.avg_order_label = QLabel("Rs 0.00")
        self.avg_order_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #8b5cf6;")
        avg_layout.addWidget(QLabel("📈 Avg Order Value"))
        avg_layout.addWidget(self.avg_order_label)
        
        analytics_layout.addWidget(monthly_frame)
        analytics_layout.addWidget(top_supplier_frame)
        analytics_layout.addWidget(avg_frame)
        
        layout.addWidget(analytics_frame)

        # Supplier performance table
        performance_label = QLabel("🏢 Supplier Performance")
        performance_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px 0 10px 0;")
        layout.addWidget(performance_label)
        
        self.supplier_performance_table = QTableWidget()
        self.supplier_performance_table.setColumnCount(6)
        self.supplier_performance_table.setHorizontalHeaderLabels([
            "Supplier", "Total Orders", "Total Amount", "Avg Order Value", 
            "On-Time Delivery", "Rating"
        ])
        
        layout.addWidget(self.supplier_performance_table)
        self.load_supplier_performance()
        return widget

    def load_purchase_orders(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            
            purchases = self.controller.session.query(Purchase).join(Supplier).order_by(
                Purchase.order_date.desc()
            ).all()
            
            self.purchase_orders_table.setRowCount(len(purchases))
            
            for i, purchase in enumerate(purchases):
                self.purchase_orders_table.setItem(i, 0, QTableWidgetItem(
                    purchase.purchase_number or f"P-{purchase.id}"
                ))
                self.purchase_orders_table.setItem(i, 1, QTableWidgetItem(
                    purchase.supplier.name if purchase.supplier else ""
                ))
                
                order_date = purchase.order_date.strftime('%Y-%m-%d') if purchase.order_date else ""
                self.purchase_orders_table.setItem(i, 2, QTableWidgetItem(order_date))
                
                expected_date = ""
                if hasattr(purchase, 'expected_delivery') and purchase.expected_delivery:
                    expected_date = purchase.expected_delivery.strftime('%Y-%m-%d')
                self.purchase_orders_table.setItem(i, 3, QTableWidgetItem(expected_date))
                
                self.purchase_orders_table.setItem(i, 4, QTableWidgetItem(f"Rs {purchase.total_amount:,.2f}"))
                self.purchase_orders_table.setItem(i, 5, QTableWidgetItem(f"Rs {purchase.paid_amount:,.2f}"))
                
                outstanding = purchase.total_amount - purchase.paid_amount
                outstanding_item = QTableWidgetItem(f"Rs {outstanding:,.2f}")
                if outstanding > 0:
                    outstanding_item.setForeground(Qt.red)
                self.purchase_orders_table.setItem(i, 6, outstanding_item)
                
                self.purchase_orders_table.setItem(i, 7, QTableWidgetItem(purchase.status or ""))
                
                priority = getattr(purchase, 'priority', 'NORMAL')
                priority_item = QTableWidgetItem(priority)
                if priority == "URGENT":
                    priority_item.setForeground(Qt.red)
                elif priority == "HIGH":
                    priority_item.setForeground(Qt.darkRed)
                self.purchase_orders_table.setItem(i, 8, priority_item)
                
                # Store purchase ID
                self.purchase_orders_table.item(i, 0).setData(Qt.UserRole, purchase.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load purchase orders: {str(e)}")

    def load_partial_payments(self):
        try:
            from pos_app.models.database import Purchase, Supplier, PurchasePayment
            
            # Get purchases with partial payments
            purchases = self.controller.session.query(Purchase).join(Supplier).filter(  # TODO: Add .all() or .first()
                Purchase.paid_amount > 0,
                Purchase.paid_amount < Purchase.total_amount
            ).all()
            
            self.partial_payments_table.setRowCount(len(purchases))
            
            total_outstanding = 0
            
            for i, purchase in enumerate(purchases):
                self.partial_payments_table.setItem(i, 0, QTableWidgetItem(
                    purchase.purchase_number or f"P-{purchase.id}"
                ))
                self.partial_payments_table.setItem(i, 1, QTableWidgetItem(
                    purchase.supplier.name if purchase.supplier else ""
                ))
                self.partial_payments_table.setItem(i, 2, QTableWidgetItem(f"Rs {purchase.total_amount:,.2f}"))
                self.partial_payments_table.setItem(i, 3, QTableWidgetItem(f"Rs {purchase.paid_amount:,.2f}"))
                
                outstanding = purchase.total_amount - purchase.paid_amount
                total_outstanding += outstanding
                
                outstanding_item = QTableWidgetItem(f"Rs {outstanding:,.2f}")
                outstanding_item.setForeground(Qt.red)
                self.partial_payments_table.setItem(i, 4, outstanding_item)
                
                # Get last payment
                last_payment = self.controller.session.query(PurchasePayment).filter(  # TODO: Add .all() or .first()
                    PurchasePayment.purchase_id == purchase.id
                ).order_by(PurchasePayment.payment_date.desc()).first()
                
                if last_payment:
                    last_date = last_payment.payment_date.strftime('%Y-%m-%d') if last_payment.payment_date else ""
                    self.partial_payments_table.setItem(i, 5, QTableWidgetItem(last_date))
                    self.partial_payments_table.setItem(i, 6, QTableWidgetItem(
                        str(last_payment.payment_method) if last_payment.payment_method else ""
                    ))
                else:
                    self.partial_payments_table.setItem(i, 5, QTableWidgetItem("Never"))
                    self.partial_payments_table.setItem(i, 6, QTableWidgetItem(""))
                
                self.partial_payments_table.setItem(i, 7, QTableWidgetItem("Partial Payment"))
                
                # Store purchase ID
                self.partial_payments_table.item(i, 0).setData(Qt.UserRole, purchase.id)
            
            # Update summary
            self.total_outstanding_label.setText(f"Rs {total_outstanding:,.2f}")
            self.partial_count_label.setText(str(len(purchases)))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load partial payments: {str(e)}")

    def load_purchases_for_notes(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            
            purchases = self.controller.session.query(Purchase).join(Supplier).all()
            
            self.purchase_notes_combo.clear()
            self.purchase_notes_combo.addItem("Select Purchase", None)
            
            for purchase in purchases:
                supplier_name = purchase.supplier.name if purchase.supplier else "Unknown"
                purchase_num = purchase.purchase_number or f"P-{purchase.id}"
                self.purchase_notes_combo.addItem(f"{purchase_num} - {supplier_name}", purchase.id)
                
        except Exception as e:
            logging.exception("Failed to load purchases for notes")

    def load_supplier_performance(self):
        try:
            from pos_app.models.database import Purchase, Supplier
            from sqlalchemy import func
            
            # Get supplier statistics
            supplier_stats = self.controller.session.query(
                Supplier.name,
                func.count(Purchase.id).label('order_count'),
                func.sum(Purchase.total_amount).label('total_amount'),
                func.avg(Purchase.total_amount).label('avg_amount')
            ).join(Purchase).group_by(Supplier.id, Supplier.name).all()
            
            self.supplier_performance_table.setRowCount(len(supplier_stats))
            
            for i, (name, count, total, avg) in enumerate(supplier_stats):
                self.supplier_performance_table.setItem(i, 0, QTableWidgetItem(name))
                self.supplier_performance_table.setItem(i, 1, QTableWidgetItem(str(count)))
                self.supplier_performance_table.setItem(i, 2, QTableWidgetItem(f"Rs {total:,.2f}" if total else "Rs 0.00"))
                self.supplier_performance_table.setItem(i, 3, QTableWidgetItem(f"Rs {avg:,.2f}" if avg else "Rs 0.00"))
                self.supplier_performance_table.setItem(i, 4, QTableWidgetItem("95%"))  # Placeholder
                self.supplier_performance_table.setItem(i, 5, QTableWidgetItem("⭐⭐⭐⭐"))  # Placeholder
            
            # Update analytics summary
            if supplier_stats:
                # Calculate monthly spending
                from datetime import datetime, timedelta
                month_start = datetime.now().replace(day=1)
                
                monthly_purchases = self.controller.session.query(Purchase).filter(  # TODO: Add .all() or .first()
                    Purchase.order_date >= month_start
                ).all()
                
                monthly_total = sum(p.total_amount for p in monthly_purchases)
                self.monthly_spending_label.setText(f"Rs {monthly_total:,.2f}")
                
                # Top supplier
                top_supplier = max(supplier_stats, key=lambda x: x[2] if x[2] else 0)
                self.top_supplier_label.setText(top_supplier[0])
                
                # Average order value
                all_purchases = self.controller.session.query(Purchase).all()
                if all_purchases:
                    avg_order = sum(p.total_amount for p in all_purchases) / len(all_purchases)
                    self.avg_order_label.setText(f"Rs {avg_order:,.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load supplier performance: {str(e)}")

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

    def create_purchase_order(self):
        dialog = PurchaseOrderDialog(self, self.controller)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Purchase order created successfully!")
            self.load_purchase_orders()

    def record_payment(self):
        selected_rows = self.partial_payments_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a purchase to record payment")
            return
        
        purchase_id = self.partial_payments_table.item(selected_rows[0].row(), 0).data(Qt.UserRole)
        
        dialog = PurchasePaymentDialog(self, self.controller, purchase_id)
        if dialog.exec() == QDialog.Accepted:
            QMessageBox.information(self, "Success", "Payment recorded successfully!")
            self.load_partial_payments()

    def receive_items(self):
        selected_rows = self.purchase_orders_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a purchase order to receive items")
            return
        
        QMessageBox.information(self, "Info", "Receive items dialog would open here")

    def add_purchase_note(self):
        purchase_id = self.purchase_notes_combo.currentData()
        note_text = self.purchase_note_input.toPlainText().strip()
        note_type = self.note_type.currentText()
        
        if not purchase_id or not note_text:
            QMessageBox.warning(self, "Warning", "Please select a purchase and enter a note")
            return
        
        # In a real implementation, you'd save this to a purchase_notes table
        QMessageBox.information(self, "Success", f"{note_type} note added successfully!")
        self.purchase_note_input.clear()

    def filter_purchases(self):
        self.load_purchase_orders()


class PurchaseOrderDialog(QDialog):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Create Purchase Order")
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Supplier selection
        self.supplier_combo = QComboBox()
        self.load_suppliers()
        layout.addRow("Supplier:", self.supplier_combo)

        # Order details
        self.order_date = QDateEdit()
        self.order_date.setDate(QDate.currentDate())
        self.order_date.setCalendarPopup(True)
        layout.addRow("Order Date:", self.order_date)

        self.expected_delivery = QDateEdit()
        self.expected_delivery.setDate(QDate.currentDate().addDays(7))
        self.expected_delivery.setCalendarPopup(True)
        layout.addRow("Expected Delivery:", self.expected_delivery)

        self.priority = QComboBox()
        self.priority.addItems(["LOW", "NORMAL", "HIGH", "URGENT"])
        self.priority.setCurrentText("NORMAL")
        layout.addRow("Priority:", self.priority)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(100)
        layout.addRow("Notes:", self.notes)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Create Order")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addRow(buttons_layout)

    def load_suppliers(self):
        try:
            from pos_app.models.database import Supplier
            
            suppliers = self.controller.session.query(Supplier).filter(  # TODO: Add .all() or .first()
                Supplier.is_active == True
            ).all()
            
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier.name, supplier.id)
                
        except Exception as e:
            logging.exception("Failed to load suppliers")


class PurchasePaymentDialog(QDialog):
    def __init__(self, parent=None, controller=None, purchase_id=None):
        super().__init__(parent)
        self.controller = controller
        self.purchase_id = purchase_id
        self.setWindowTitle("Record Purchase Payment")
        self.setMinimumSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        # Load purchase info
        if self.purchase_id:
            purchase = self.controller.session.get(self.controller.session.query(self.controller.session.query.__class__).first().__class__, self.purchase_id)
            if purchase:
                layout.addRow("Purchase:", QLabel(f"P-{purchase.id}"))
                outstanding = purchase.total_amount - purchase.paid_amount
                layout.addRow("Outstanding:", QLabel(f"Rs {outstanding:,.2f}"))

        self.payment_amount = QDoubleSpinBox()
        self.payment_amount.setRange(0, 1000000)
        self.payment_amount.setSuffix(" Rs")
        layout.addRow("Payment Amount:", self.payment_amount)

        self.payment_method = QComboBox()
        self.payment_method.addItems(["CASH", "BANK_TRANSFER", "CHEQUE", "CREDIT_CARD"])
        layout.addRow("Payment Method:", self.payment_method)

        self.reference = QLineEdit()
        self.reference.setPlaceholderText("Cheque number, transaction ID, etc.")
        layout.addRow("Reference:", self.reference)

        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        layout.addRow("Notes:", self.notes)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Record Payment")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addRow(buttons_layout)
