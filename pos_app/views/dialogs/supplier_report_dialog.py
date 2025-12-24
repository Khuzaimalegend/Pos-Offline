"""
Detailed supplier purchase history report
"""
try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit, QGroupBox, QScrollArea, QWidget, QHeaderView
    )
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QMessageBox, QTextEdit, QGroupBox, QScrollArea, QWidget, QHeaderView
    )
    from PyQt6.QtCore import Qt
from pos_app.models.database import Supplier

class SupplierReportDialog(QDialog):
    def __init__(self, controller, supplier_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.supplier_id = supplier_id
        self.supplier = None
        self.history = []
        self.setup_ui()
        self.load_report()
    
    def setup_ui(self):
        self.setWindowTitle("Supplier Purchase History Report")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 980)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        self.header_label = QLabel()
        self.header_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        header_layout.addWidget(self.header_label)
        header_layout.addStretch()
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_csv)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)

        self._purchase_row_by_number = {}

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(12)
        
        # Summary section
        summary_group = QGroupBox("Purchase Summary")
        summary_layout = QVBoxLayout(summary_group)
        self.summary_label = QLabel()
        self.summary_label.setStyleSheet("font-size: 13px; padding: 10px;")
        summary_layout.addWidget(self.summary_label)
        body_layout.addWidget(summary_group)
        
        # Purchases table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Purchase #", "Date", "Status", "Total", "Paid", "Outstanding"
        ])
        try:
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(0, 160)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(1, 190)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(2, 110)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(3, 160)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(4, 160)
            self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(5, 160)
        except Exception:
            pass

        try:
            self.table.verticalHeader().setVisible(False)
            self.table.setMinimumHeight(210)
        except Exception:
            pass
        
        self.table.itemSelectionChanged.connect(self.on_purchase_selected)
        body_layout.addWidget(self.table)
        
        # Items detail section
        items_group = QGroupBox("Purchase Items Detail")
        items_layout = QVBoxLayout(items_group)
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(5)
        self.items_table.setHorizontalHeaderLabels([
            "Product", "Ordered Qty", "Received Qty", "Unit Cost", "Total"
        ])
        try:
            self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            self.items_table.horizontalHeader().resizeSection(1, 110)
            self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            self.items_table.horizontalHeader().resizeSection(2, 110)
            self.items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.items_table.horizontalHeader().resizeSection(3, 130)
            self.items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
            self.items_table.horizontalHeader().resizeSection(4, 140)
        except Exception:
            pass
        try:
            self.items_table.verticalHeader().setVisible(False)
            self.items_table.setMinimumHeight(190)
        except Exception:
            pass
        items_layout.addWidget(self.items_table)
        body_layout.addWidget(items_group)
        
        # Payment history section
        payments_group = QGroupBox("Payment History")
        payments_layout = QVBoxLayout(payments_group)
        self.payments_table = QTableWidget()
        self.payments_table.setColumnCount(6)
        self.payments_table.setHorizontalHeaderLabels([
            "Date & Time", "Amount", "Method", "Reference", "Notes", "Purchase #"
        ])
        try:
            self.payments_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.payments_table.horizontalHeader().resizeSection(0, 180)
            self.payments_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            self.payments_table.horizontalHeader().resizeSection(1, 150)
            self.payments_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            self.payments_table.horizontalHeader().resizeSection(2, 120)
            self.payments_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.payments_table.horizontalHeader().resizeSection(3, 220)
            self.payments_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
            self.payments_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
            self.payments_table.horizontalHeader().resizeSection(5, 160)
        except Exception:
            pass
        self.payments_table.itemClicked.connect(self._on_payment_selected)
        try:
            self.payments_table.verticalHeader().setVisible(False)
            self.payments_table.setMinimumHeight(220)
        except Exception:
            pass
        payments_layout.addWidget(self.payments_table)
        
        # Payment items details section
        details_label = QLabel("Payment Items Details (Products in this payment)")
        details_label.setStyleSheet("font-weight: bold; font-size: 12px; margin-top: 15px;")
        payments_layout.addWidget(details_label)
        
        self.payment_items_table = QTableWidget()
        self.payment_items_table.setColumnCount(5)
        self.payment_items_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Quantity", "Unit Price", "Total"
        ])
        self.payment_items_table.setMaximumHeight(180)
        try:
            self.payment_items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.payment_items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            self.payment_items_table.horizontalHeader().resizeSection(1, 130)
            self.payment_items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            self.payment_items_table.horizontalHeader().resizeSection(2, 100)
            self.payment_items_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.payment_items_table.horizontalHeader().resizeSection(3, 120)
            self.payment_items_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
            self.payment_items_table.horizontalHeader().resizeSection(4, 140)
        except Exception:
            pass
        try:
            self.payment_items_table.verticalHeader().setVisible(False)
        except Exception:
            pass
        payments_layout.addWidget(self.payment_items_table)
        body_layout.addWidget(payments_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.clicked.connect(self.accept)
        body_layout.addWidget(close_btn)

        body_layout.addStretch()
        scroll.setWidget(body)
        layout.addWidget(scroll)
    
    def load_report(self):
        try:
            # Load supplier info
            self.supplier = self.controller.session.get(Supplier, self.supplier_id)
            if not self.supplier:
                QMessageBox.critical(self, "Error", "Supplier not found")
                self.reject()
                return
            
            self.header_label.setText(f"Purchase History: {self.supplier.name}")
            
            # Load purchase history
            self.history = self.controller.get_supplier_purchase_history(self.supplier_id)
            
            # Calculate summary
            total_purchases = len(self.history)
            total_value = sum(p['total_amount'] for p in self.history)
            total_paid = sum(p['paid_amount'] for p in self.history)
            total_outstanding = sum(p['outstanding'] for p in self.history)
            
            # Count status
            ordered_count = sum(1 for p in self.history if p['status'] == 'ORDERED')
            received_count = sum(1 for p in self.history if p['status'] == 'RECEIVED')
            partial_count = sum(1 for p in self.history if p['status'] == 'PARTIAL')
            
            summary_text = (
                f"<b>Total Purchases:</b> {total_purchases}<br>"
                f"<b>Total Value:</b> Rs {total_value:,.2f}<br>"
                f"<b>Total Paid:</b> Rs {total_paid:,.2f}<br>"
                f"<b>Total Outstanding:</b> Rs {total_outstanding:,.2f}<br><br>"
                f"<b>Status Breakdown:</b><br>"
                f"  • Ordered (Pending): {ordered_count}<br>"
                f"  • Received (Complete): {received_count}<br>"
                f"  • Partial Delivery: {partial_count}"
            )
            self.summary_label.setText(summary_text)
            
            # Load purchases into table
            self.table.setRowCount(len(self.history))
            for i, purchase in enumerate(self.history):
                # Purchase number
                self.table.setItem(i, 0, QTableWidgetItem(purchase['purchase_number']))
                
                # Date
                date_str = purchase['date'].strftime('%Y-%m-%d %H:%M') if purchase['date'] else 'N/A'
                self.table.setItem(i, 1, QTableWidgetItem(date_str))
                
                # Status
                status_item = QTableWidgetItem(purchase['status'] or 'UNKNOWN')
                if purchase['status'] == 'ORDERED':
                    status_item.setForeground(Qt.blue)
                elif purchase['status'] == 'RECEIVED':
                    status_item.setForeground(Qt.green)
                elif purchase['status'] == 'PARTIAL':
                    status_item.setForeground(Qt.darkYellow)
                self.table.setItem(i, 2, status_item)
                
                # Total
                total_amt = abs(float(purchase.get('total_amount', 0.0) or 0.0))
                self.table.setItem(i, 3, QTableWidgetItem(f"Rs {total_amt:,.2f}"))
                
                # Paid
                paid_amt = abs(float(purchase.get('paid_amount', 0.0) or 0.0))
                self.table.setItem(i, 4, QTableWidgetItem(f"Rs {paid_amt:,.2f}"))
                
                # Outstanding
                outstanding_val = float(purchase.get('outstanding', 0.0) or 0.0)
                if outstanding_val < 0:
                    outstanding_val = 0.0
                outstanding_item = QTableWidgetItem(f"Rs {outstanding_val:,.2f}")
                if outstanding_val > 0:
                    outstanding_item.setForeground(Qt.red)
                else:
                    outstanding_item.setForeground(Qt.green)
                self.table.setItem(i, 5, outstanding_item)
                
                # Store purchase ID for selection
                self.table.item(i, 0).setData(Qt.UserRole, i)  # Store index
                try:
                    self._purchase_row_by_number[str(purchase.get('purchase_number') or '')] = i
                except Exception:
                    pass
            
            # Load payment history
            self.load_payment_history()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load report: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def load_payment_history(self):
        """Load payment history for the supplier"""
        try:
            from pos_app.models.database import PurchasePayment, Purchase
            
            # Query all purchases for this supplier, then get their payments
            purchases = self.controller.session.query(Purchase).filter(
                Purchase.supplier_id == self.supplier_id
            ).all()
            
            # Collect all payments from these purchases
            payments = []
            for purchase in purchases:
                purchase_payments = self.controller.session.query(PurchasePayment).filter(
                    PurchasePayment.purchase_id == purchase.id
                ).order_by(PurchasePayment.payment_date.desc()).all()
                payments.extend(purchase_payments)
            
            self.payments_table.setRowCount(len(payments))
            
            for row, payment in enumerate(payments):
                # Date & Time
                date_time_str = payment.payment_date.strftime('%Y-%m-%d %H:%M:%S') if payment.payment_date else 'N/A'
                self.payments_table.setItem(row, 0, QTableWidgetItem(date_time_str))
                
                # Amount
                amount_val = abs(float(getattr(payment, 'amount', 0.0) or 0.0))
                amount_str = f"Rs {amount_val:,.2f}"
                self.payments_table.setItem(row, 1, QTableWidgetItem(amount_str))
                
                # Payment Method
                method_str = payment.payment_method or 'N/A'
                self.payments_table.setItem(row, 2, QTableWidgetItem(method_str))
                
                # Reference
                reference_str = payment.reference or '-'
                reference_item = QTableWidgetItem(reference_str)
                try:
                    reference_item.setForeground(Qt.blue)
                    reference_item.setData(Qt.UserRole, None)
                except Exception:
                    pass
                self.payments_table.setItem(row, 3, reference_item)
                
                # Notes
                notes_str = payment.notes or '-'
                self.payments_table.setItem(row, 4, QTableWidgetItem(notes_str))
                
                # Purchase Number
                purchase_num = 'N/A'
                if payment.purchase_id:
                    try:
                        purchase = self.controller.session.query(Purchase).filter(
                            Purchase.id == payment.purchase_id
                        ).first()
                        if purchase:
                            purchase_num = purchase.purchase_number or 'N/A'
                    except Exception:
                        pass
                purchase_item = QTableWidgetItem(purchase_num)
                try:
                    if purchase_num and purchase_num != 'N/A':
                        purchase_item.setForeground(Qt.blue)
                        purchase_item.setData(Qt.UserRole, str(purchase_num))
                        reference_item.setData(Qt.UserRole, str(purchase_num))
                except Exception:
                    pass
                self.payments_table.setItem(row, 5, purchase_item)

            try:
                self.payments_table.resizeColumnsToContents()
                self.payments_table.resizeRowsToContents()
            except Exception:
                pass
        
        except Exception as e:
            print(f"Error loading payment history: {e}")
            # Don't show error dialog, just leave payments table empty
            self.payments_table.setRowCount(0)
    
    def _on_payment_selected(self, item):
        """Show items in the purchase that this payment was for"""
        try:
            from pos_app.models.database import PurchasePayment, Purchase, PurchaseItem, Product
            
            # Get the row index
            row = self.payments_table.row(item)
            
            purchase_number = None
            try:
                if item and item.column() in (3, 5):
                    purchase_number = item.data(Qt.UserRole)
            except Exception:
                pass

            if not purchase_number:
                purchase_num_item = self.payments_table.item(row, 5)
                if not purchase_num_item:
                    self.payment_items_table.setRowCount(0)
                    return
                purchase_number = purchase_num_item.text()

            try:
                if item and item.column() in (3, 5) and purchase_number and purchase_number != 'N/A':
                    target_row = self._purchase_row_by_number.get(str(purchase_number))
                    if target_row is not None:
                        self.table.selectRow(int(target_row))
                        self.on_purchase_selected()
            except Exception:
                pass
            
            # Find the purchase by purchase number or ID
            purchase = None
            if purchase_number != 'N/A' and purchase_number.startswith('P-'):
                # It's an ID-based number like "P-123"
                try:
                    purchase_id = int(purchase_number.split("-")[1])
                    purchase = self.controller.session.query(Purchase).filter(Purchase.id == purchase_id).first()
                except Exception:
                    pass
            
            # If not found, try to find by purchase_number field
            if not purchase and purchase_number != 'N/A':
                purchase = self.controller.session.query(Purchase).filter(
                    Purchase.purchase_number == purchase_number
                ).first()
            
            if not purchase:
                self.payment_items_table.setRowCount(0)
                return
            
            # Load purchase items
            purchase_items = self.controller.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase.id
            ).all()
            
            self.payment_items_table.setRowCount(len(purchase_items))
            
            for i, item_obj in enumerate(purchase_items):
                # Get product info
                product = self.controller.session.query(Product).filter(
                    Product.id == item_obj.product_id
                ).first()
                
                # Product name
                product_name = product.name if product else f"Product #{item_obj.product_id}"
                self.payment_items_table.setItem(i, 0, QTableWidgetItem(product_name))
                
                # SKU
                sku = product.sku if product else ""
                self.payment_items_table.setItem(i, 1, QTableWidgetItem(sku))
                
                # Quantity
                quantity = item_obj.quantity or 0
                self.payment_items_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
                
                # Unit Price
                unit_cost = getattr(item_obj, 'unit_cost', None)
                if unit_cost is None:
                    unit_cost = 0.0
                self.payment_items_table.setItem(i, 3, QTableWidgetItem(f"Rs {float(unit_cost):,.2f}"))
                
                # Total
                total_cost = getattr(item_obj, 'total_cost', None)
                if total_cost is None:
                    try:
                        total_cost = float(quantity) * float(unit_cost)
                    except Exception:
                        total_cost = 0.0
                self.payment_items_table.setItem(i, 4, QTableWidgetItem(f"Rs {float(total_cost):,.2f}"))

            try:
                self.payment_items_table.resizeColumnsToContents()
                self.payment_items_table.resizeRowsToContents()
            except Exception:
                pass
        
        except Exception as e:
            print(f"Error loading payment items: {e}")
            self.payment_items_table.setRowCount(0)
    
    def on_purchase_selected(self):
        """Show items when a purchase is selected"""
        try:
            selected_rows = self.table.selectionModel().selectedRows()
            if not selected_rows:
                self.items_table.setRowCount(0)
                return
            
            row = selected_rows[0].row()
            item = self.table.item(row, 0)
            if not item:
                self.items_table.setRowCount(0)
                return
            
            purchase_index = item.data(Qt.UserRole)
            if purchase_index is None or purchase_index >= len(self.history):
                self.items_table.setRowCount(0)
                return
            
            purchase = self.history[purchase_index]
            items = purchase.get('items', [])
            
            # Load items into detail table
            self.items_table.setRowCount(len(items))
            for i, item_data in enumerate(items):
                self.items_table.setItem(i, 0, QTableWidgetItem(item_data.get('product_name', 'Unknown')))
                qty_val = float(item_data.get('quantity', 0.0) or 0.0)
                recv_val = float(item_data.get('received_quantity', 0.0) or 0.0)
                unit_cost = abs(float(item_data.get('unit_cost', 0.0) or 0.0))
                total = abs(float(item_data.get('total', 0.0) or 0.0))
                self.items_table.setItem(i, 1, QTableWidgetItem(str(qty_val)))
                self.items_table.setItem(i, 2, QTableWidgetItem(str(recv_val)))
                self.items_table.setItem(i, 3, QTableWidgetItem(f"Rs {unit_cost:,.2f}"))
                self.items_table.setItem(i, 4, QTableWidgetItem(f"Rs {total:,.2f}"))
        
        except Exception as e:
            print(f"Error loading purchase items: {e}")
            import traceback
            traceback.print_exc()
            self.items_table.setRowCount(0)
    
    def export_csv(self):
        """Export report to CSV"""
        try:
            import csv
            from datetime import datetime
            import os
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"supplier_report_{self.supplier.name.replace(' ', '_')}_{timestamp}.csv"
            filepath = os.path.join("exports", filename)
            
            # Ensure exports directory exists
            os.makedirs("exports", exist_ok=True)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([f"Supplier Purchase History Report - {self.supplier.name}"])
                writer.writerow([f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                writer.writerow([])
                
                # Write purchases
                writer.writerow(['Purchase #', 'Date', 'Status', 'Product', 'Ordered Qty', 'Received Qty', 'Unit Cost', 'Total'])
                
                for purchase in self.history:
                    date_str = purchase['date'].strftime('%Y-%m-%d %H:%M') if purchase['date'] else 'N/A'
                    for item in purchase['items']:
                        writer.writerow([
                            purchase['purchase_number'],
                            date_str,
                            purchase['status'],
                            item['product_name'],
                            item['quantity'],
                            item['received_quantity'],
                            f"{item['unit_cost']:.2f}",
                            f"{item['total']:.2f}"
                        ])
            
            QMessageBox.information(self, "Export Successful", 
                                   f"Report exported to:\n{filepath}")
        
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Failed to export report: {str(e)}")
