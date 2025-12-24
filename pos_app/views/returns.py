"""
Returns Management - Handle product returns and refunds
"""
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
        QTextEdit, QSpinBox, QDoubleSpinBox, QDialog, QMessageBox,
        QDateEdit, QFormLayout, QGroupBox
    )
    from PySide6.QtCore import Qt, QDate, QTimer
    from PySide6.QtGui import QFont, QColor
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
        QTextEdit, QSpinBox, QDoubleSpinBox, QDialog, QMessageBox,
        QDateEdit, QFormLayout, QGroupBox
    )
    from PyQt6.QtCore import Qt, QDate, QTimer
    from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta
from decimal import Decimal

class ReturnsWidget(QWidget):
    """Main returns management widget"""
    
    def __init__(self, controllers):
        super().__init__()
        self.controllers = controllers
        self.setup_ui()
        self.load_returns()
    
    def setup_ui(self):
        """Setup the returns management UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("↩️ Returns Management")
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b;")
        layout.addWidget(header)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Date range filter
        controls_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        controls_layout.addWidget(self.start_date)
        
        controls_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        controls_layout.addWidget(self.end_date)
        
        # Status filter
        controls_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "PENDING", "APPROVED", "COMPLETED", "REJECTED", "CANCELLED"])
        controls_layout.addWidget(self.status_filter)
        
        # Buttons
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.load_returns)
        controls_layout.addWidget(filter_btn)
        
        new_return_btn = QPushButton("➕ New Return")
        new_return_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        new_return_btn.clicked.connect(self.create_new_return)
        controls_layout.addWidget(new_return_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Returns table
        self.returns_table = QTableWidget()
        self.returns_table.setColumnCount(8)
        self.returns_table.setHorizontalHeaderLabels([
            "Return #", "Date", "Customer", "Items", "Refund", "Status", "Reason", "Actions"
        ])
        self.returns_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #e2e8f0;
            }
            QHeaderView::section {
                background: #f8fafc;
                color: #374151;
                font-weight: 600;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #e2e8f0;
            }
        """)
        self.returns_table.itemClicked.connect(self._on_return_selected)
        layout.addWidget(self.returns_table)
        
        # Return details section
        details_label = QLabel("Return Details")
        details_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        layout.addWidget(details_label)
        
        # Return items table
        self.return_items_table = QTableWidget()
        self.return_items_table.setColumnCount(6)
        self.return_items_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Qty", "Unit Price", "Condition", "Notes"
        ])
        self.return_items_table.setMaximumHeight(200)
        self.return_items_table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
            QTableWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #e2e8f0;
            }
        """)
        layout.addWidget(self.return_items_table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.approve_btn = QPushButton("✅ Approve")
        self.approve_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        self.approve_btn.clicked.connect(self.approve_return)
        self.approve_btn.setEnabled(False)
        action_layout.addWidget(self.approve_btn)
        
        self.reject_btn = QPushButton("❌ Reject")
        self.reject_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        self.reject_btn.clicked.connect(self.reject_return)
        self.reject_btn.setEnabled(False)
        action_layout.addWidget(self.reject_btn)
        
        self.complete_btn = QPushButton("✔️ Complete & Refund")
        self.complete_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #059669;
            }
        """)
        self.complete_btn.clicked.connect(self.complete_return)
        self.complete_btn.setEnabled(False)
        action_layout.addWidget(self.complete_btn)
        
        action_layout.addStretch()
        layout.addLayout(action_layout)
        
        self.current_return = None
    
    def load_returns(self):
        """Load returns from database"""
        try:
            from pos_app.models.database import Return, ReturnItem, Product
            
            controller = self.controllers.get('returns') if isinstance(self.controllers, dict) else self.controllers
            
            # Get date range
            start_date = self.start_date.date().toPython() if hasattr(self.start_date.date(), 'toPython') else self.start_date.date()
            end_date = self.end_date.date().toPython() if hasattr(self.end_date.date(), 'toPython') else self.end_date.date()
            
            # Get status filter
            status_filter = self.status_filter.currentText()
            
            # Query returns
            query = controller.session.query(Return).filter(
                Return.return_date >= datetime.combine(start_date, datetime.min.time()),
                Return.return_date <= datetime.combine(end_date, datetime.max.time())
            )
            
            if status_filter != "All":
                query = query.filter(Return.status == status_filter)
            
            returns = query.all()
            
            # Populate table
            self.returns_table.setRowCount(len(returns))
            
            for i, ret in enumerate(returns):
                # Return number
                self.returns_table.setItem(i, 0, QTableWidgetItem(ret.return_number))
                
                # Date
                date_str = ret.return_date.strftime("%Y-%m-%d") if ret.return_date else ""
                self.returns_table.setItem(i, 1, QTableWidgetItem(date_str))
                
                # Customer
                customer_name = ret.customer.name if ret.customer else "Unknown"
                self.returns_table.setItem(i, 2, QTableWidgetItem(customer_name))
                
                # Items count
                items_count = len(ret.items) if ret.items else 0
                self.returns_table.setItem(i, 3, QTableWidgetItem(str(items_count)))
                
                # Refund amount
                refund_item = QTableWidgetItem(f"Rs {ret.refund_amount:,.2f}")
                refund_item.setTextAlignment(Qt.AlignRight)
                self.returns_table.setItem(i, 4, refund_item)
                
                # Status with color
                status_item = QTableWidgetItem(ret.status.value)
                if ret.status.value == "COMPLETED":
                    status_item.setForeground(QColor("#10b981"))
                elif ret.status.value == "APPROVED":
                    status_item.setForeground(QColor("#3b82f6"))
                elif ret.status.value == "REJECTED":
                    status_item.setForeground(QColor("#ef4444"))
                elif ret.status.value == "PENDING":
                    status_item.setForeground(QColor("#f59e0b"))
                self.returns_table.setItem(i, 5, status_item)
                
                # Reason
                reason = ret.reason or "-"
                self.returns_table.setItem(i, 6, QTableWidgetItem(reason))
                
                # Actions (view button)
                view_btn = QPushButton("View")
                view_btn.setStyleSheet("""
                    QPushButton {
                        background: #64748b;
                        color: white;
                        border: none;
                        padding: 4px 12px;
                        border-radius: 4px;
                        font-size: 12px;
                    }
                """)
                view_btn.clicked.connect(lambda checked, ret_id=ret.id: self._view_return(ret_id))
                self.returns_table.setCellWidget(i, 7, view_btn)
        
        except Exception as e:
            print(f"Error loading returns: {e}")
    
    def _on_return_selected(self, item):
        """Handle return selection"""
        try:
            from pos_app.models.database import Return
            
            controller = self.controllers.get('returns') if isinstance(self.controllers, dict) else self.controllers
            
            row = self.returns_table.row(item)
            return_num_item = self.returns_table.item(row, 0)
            
            if not return_num_item:
                return
            
            return_number = return_num_item.text()
            ret = controller.session.query(Return).filter(Return.return_number == return_number).first()
            
            if ret:
                self.current_return = ret
                self._load_return_items(ret)
                
                # Enable/disable buttons based on status
                if ret.status.value == "PENDING":
                    self.approve_btn.setEnabled(True)
                    self.reject_btn.setEnabled(True)
                    self.complete_btn.setEnabled(False)
                elif ret.status.value == "APPROVED":
                    self.approve_btn.setEnabled(False)
                    self.reject_btn.setEnabled(False)
                    self.complete_btn.setEnabled(True)
                else:
                    self.approve_btn.setEnabled(False)
                    self.reject_btn.setEnabled(False)
                    self.complete_btn.setEnabled(False)
        
        except Exception as e:
            print(f"Error selecting return: {e}")
    
    def _load_return_items(self, ret):
        """Load items for a return"""
        try:
            from pos_app.models.database import Product
            
            items = ret.items if ret.items else []
            self.return_items_table.setRowCount(len(items))
            
            for i, item in enumerate(items):
                product = item.product
                
                # Product name
                self.return_items_table.setItem(i, 0, QTableWidgetItem(product.name if product else "Unknown"))
                
                # SKU
                self.return_items_table.setItem(i, 1, QTableWidgetItem(product.sku if product else ""))
                
                # Quantity
                self.return_items_table.setItem(i, 2, QTableWidgetItem(str(item.quantity)))
                
                # Unit price
                price_item = QTableWidgetItem(f"Rs {item.unit_price:,.2f}")
                price_item.setTextAlignment(Qt.AlignRight)
                self.return_items_table.setItem(i, 3, price_item)
                
                # Condition
                self.return_items_table.setItem(i, 4, QTableWidgetItem(item.condition or "-"))
                
                # Notes
                self.return_items_table.setItem(i, 5, QTableWidgetItem(item.notes or "-"))
        
        except Exception as e:
            print(f"Error loading return items: {e}")
    
    def _view_return(self, return_id):
        """View return details"""
        try:
            from pos_app.models.database import Return
            
            controller = self.controllers.get('returns') if isinstance(self.controllers, dict) else self.controllers
            ret = controller.session.query(Return).filter(Return.id == return_id).first()
            
            if ret:
                self.current_return = ret
                self._load_return_items(ret)
        
        except Exception as e:
            print(f"Error viewing return: {e}")
    
    def create_new_return(self):
        """Create a new return"""
        dialog = NewReturnDialog(self.controllers, self)
        if dialog.exec():
            self.load_returns()
    
    def approve_return(self):
        """Approve a return"""
        if not self.current_return:
            return
        
        try:
            from pos_app.models.database import Return, ReturnStatus
            from pos_app.database.db_utils import get_db_session
            
            with get_db_session() as session:
                ret = session.query(Return).filter(Return.id == self.current_return.id).first()
                if ret:
                    ret.status = ReturnStatus.APPROVED
                    session.commit()
                    QMessageBox.information(self, "Success", f"Return {ret.return_number} approved!")
                    self.load_returns()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to approve return: {e}")
    
    def reject_return(self):
        """Reject a return"""
        if not self.current_return:
            return
        
        try:
            from pos_app.models.database import Return, ReturnStatus
            from pos_app.database.db_utils import get_db_session
            
            with get_db_session() as session:
                ret = session.query(Return).filter(Return.id == self.current_return.id).first()
                if ret:
                    ret.status = ReturnStatus.REJECTED
                    session.commit()
                    QMessageBox.information(self, "Success", f"Return {ret.return_number} rejected!")
                    self.load_returns()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reject return: {e}")
    
    def complete_return(self):
        """Complete return and process refund"""
        if not self.current_return:
            return
        
        dialog = CompleteReturnDialog(self.current_return, self.controllers, self)
        if dialog.exec():
            self.load_returns()


class NewReturnDialog(QDialog):
    """Dialog to create a new return"""
    
    def __init__(self, controllers, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.setWindowTitle("New Return")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Customer selection
        form_layout = QFormLayout()
        
        self.customer_combo = QComboBox()
        self._load_customers()
        form_layout.addRow("Customer:", self.customer_combo)
        
        self.reason_combo = QComboBox()
        self.reason_combo.addItems(["Damaged", "Defective", "Wrong Item", "Changed Mind", "Other"])
        form_layout.addRow("Reason:", self.reason_combo)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.notes)
        
        layout.addLayout(form_layout)
        
        # Items section
        items_label = QLabel("Return Items")
        items_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(items_label)
        
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels(["Product", "SKU", "Qty", "Unit Price", "Remove"])
        self.items_table.setMaximumHeight(200)
        layout.addWidget(self.items_table)
        
        # Add item button
        add_item_btn = QPushButton("➕ Add Item")
        add_item_btn.clicked.connect(self._add_item_row)
        layout.addWidget(add_item_btn)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Create Return")
        save_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        save_btn.clicked.connect(self._save_return)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _load_customers(self):
        """Load customers into combo"""
        try:
            from pos_app.models.database import Customer
            
            controller = self.controllers.get('returns') if isinstance(self.controllers, dict) else self.controllers
            customers = controller.session.query(Customer).filter(Customer.is_active == True).all()
            
            for customer in customers:
                self.customer_combo.addItem(customer.name, customer.id)
        
        except Exception as e:
            print(f"Error loading customers: {e}")
    
    def _add_item_row(self):
        """Add a new item row"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        # Product combo
        product_combo = QComboBox()
        self._load_products_into_combo(product_combo)
        self.items_table.setCellWidget(row, 0, product_combo)
        
        # SKU (read-only)
        sku_item = QTableWidgetItem("")
        sku_item.setFlags(sku_item.flags() & ~Qt.ItemIsEditable)
        self.items_table.setItem(row, 1, sku_item)
        
        # Quantity
        qty_spinbox = QSpinBox()
        qty_spinbox.setMinimum(1)
        qty_spinbox.setValue(1)
        self.items_table.setCellWidget(row, 2, qty_spinbox)
        
        # Unit price
        price_spinbox = QDoubleSpinBox()
        price_spinbox.setMinimum(0)
        price_spinbox.setDecimals(2)
        self.items_table.setCellWidget(row, 3, price_spinbox)
        
        # Remove button
        remove_btn = QPushButton("🗑️")
        remove_btn.clicked.connect(lambda: self.items_table.removeRow(row))
        self.items_table.setCellWidget(row, 4, remove_btn)
    
    def _load_products_into_combo(self, combo):
        """Load products into combo"""
        try:
            from pos_app.models.database import Product
            
            controller = self.controllers.get('returns') if isinstance(self.controllers, dict) else self.controllers
            products = controller.session.query(Product).filter(Product.is_active == True).all()
            
            for product in products:
                combo.addItem(product.name, product.id)
        
        except Exception as e:
            print(f"Error loading products: {e}")
    
    def _save_return(self):
        """Save the return"""
        try:
            from pos_app.models.database import Return, ReturnItem, ReturnStatus, Customer, Product
            from pos_app.database.db_utils import get_db_session
            
            customer_id = self.customer_combo.currentData()
            reason = self.reason_combo.currentText()
            notes = self.notes.toPlainText()
            
            if not customer_id:
                QMessageBox.warning(self, "Error", "Please select a customer!")
                return
            
            if self.items_table.rowCount() == 0:
                QMessageBox.warning(self, "Error", "Please add at least one item!")
                return
            
            with get_db_session() as session:
                # Generate return number
                last_return = session.query(Return).order_by(Return.id.desc()).first()
                return_num = f"RET-{(last_return.id + 1) if last_return else 1:06d}"
                
                # Create return
                ret = Return(
                    return_number=return_num,
                    customer_id=customer_id,
                    reason=reason,
                    notes=notes,
                    status=ReturnStatus.PENDING
                )
                session.add(ret)
                session.flush()
                
                # Add items
                for row in range(self.items_table.rowCount()):
                    product_combo = self.items_table.cellWidget(row, 0)
                    qty_spinbox = self.items_table.cellWidget(row, 2)
                    price_spinbox = self.items_table.cellWidget(row, 3)
                    
                    product_id = product_combo.currentData()
                    quantity = qty_spinbox.value()
                    unit_price = price_spinbox.value()
                    
                    item = ReturnItem(
                        return_id=ret.id,
                        product_id=product_id,
                        quantity=quantity,
                        unit_price=unit_price,
                        total=quantity * unit_price
                    )
                    session.add(item)
                
                session.commit()
                QMessageBox.information(self, "Success", f"Return {return_num} created!")
                self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create return: {e}")


class CompleteReturnDialog(QDialog):
    """Dialog to complete a return and process refund"""
    
    def __init__(self, return_obj, controllers, parent=None):
        super().__init__(parent)
        self.return_obj = return_obj
        self.controllers = controllers
        self.setWindowTitle("Complete Return & Refund")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Return info
        info_layout = QFormLayout()
        
        info_layout.addRow("Return #:", QLabel(self.return_obj.return_number))
        info_layout.addRow("Customer:", QLabel(self.return_obj.customer.name if self.return_obj.customer else "Unknown"))
        
        # Calculate total refund
        total_refund = sum(item.total for item in self.return_obj.items) if self.return_obj.items else 0
        info_layout.addRow("Total Refund:", QLabel(f"Rs {total_refund:,.2f}"))
        
        layout.addLayout(info_layout)
        
        # Refund method
        form_layout = QFormLayout()
        
        self.refund_method = QComboBox()
        self.refund_method.addItems(["CASH", "CREDIT_CARD", "DEBIT_CARD", "BANK_TRANSFER", "CREDIT"])
        form_layout.addRow("Refund Method:", self.refund_method)
        
        self.refund_notes = QTextEdit()
        self.refund_notes.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.refund_notes)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        complete_btn = QPushButton("Complete & Refund")
        complete_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        complete_btn.clicked.connect(self._complete_refund)
        button_layout.addWidget(complete_btn)
        
        layout.addLayout(button_layout)
    
    def _complete_refund(self):
        """Complete the refund"""
        try:
            from pos_app.models.database import Return, ReturnStatus, PaymentMethod
            from pos_app.database.db_utils import get_db_session
            from pos_app.controllers.business_logic import BusinessController
            
            refund_method = self.refund_method.currentText()
            notes = self.refund_notes.toPlainText()
            
            total_refund = sum(item.total for item in self.return_obj.items) if self.return_obj.items else 0
            
            with get_db_session() as session:
                ret = session.query(Return).filter(Return.id == self.return_obj.id).first()
                if ret:
                    try:
                        if getattr(ret, 'status', None) == ReturnStatus.COMPLETED:
                            QMessageBox.information(self, "Already Completed", f"Return {ret.return_number} is already completed.")
                            self.accept()
                            return
                    except Exception:
                        pass

                    # Increase stock for each returned item
                    try:
                        bc = BusinessController(session)
                        try:
                            from pos_app.models.database import InventoryLocation
                            loc = InventoryLocation.RETAIL
                        except Exception:
                            loc = None

                        for it in (getattr(ret, 'items', None) or []):
                            try:
                                pid = getattr(it, 'product_id', None)
                                qty = getattr(it, 'quantity', 0)
                                if pid is None:
                                    continue
                                if qty is None:
                                    continue
                                bc.update_stock(
                                    pid,
                                    qty,
                                    movement_type='IN',
                                    reference=f"Return {getattr(ret, 'return_number', '')}",
                                    location=loc,
                                    commit=False
                                )
                            except Exception:
                                # Do not partially complete: bubble up to rollback
                                raise
                    except Exception as e:
                        session.rollback()
                        raise Exception(f"Failed to update stock for return: {e}")

                    ret.status = ReturnStatus.COMPLETED
                    ret.refund_amount = total_refund
                    ret.refund_method = PaymentMethod[refund_method]
                    ret.notes = notes
                    session.commit()
                    
                    QMessageBox.information(self, "Success", f"Return {ret.return_number} completed! Refund: Rs {total_refund:,.2f}")
                    self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to complete return: {e}")
