"""
Dialog for receiving purchase orders and confirming delivery
"""
try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox, QDoubleSpinBox, QFormLayout, QAbstractSpinBox
    )
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QMessageBox, QSpinBox, QDoubleSpinBox, QFormLayout, QAbstractSpinBox
    )
    from PyQt6.QtCore import Qt
from pos_app.models.database import Purchase, PurchaseItem, Product, Supplier

class ReceivePurchaseDialog(QDialog):
    def __init__(self, controller, purchase_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.purchase_id = purchase_id
        self.purchase = None
        self.setup_ui()
        self.load_purchase()
    
    def setup_ui(self):
        self.setWindowTitle("Receive Purchase Order")
        self.setMinimumSize(700, 500)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Receive Purchase Order")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Purchase info
        self.info_label = QLabel()
        self.info_label.setStyleSheet("font-size: 12px; margin-bottom: 15px;")
        layout.addWidget(self.info_label)
        
        # Instructions
        instructions = QLabel(
            "Review the items below and enter the quantity received for each product.\n"
            "Leave as-is to receive the full ordered quantity."
        )
        instructions.setStyleSheet("color: #888; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Items table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Product", "Ordered Qty", "Received Qty", "Unit Cost", "Total"
        ])
        try:
            from PySide6.QtWidgets import QHeaderView
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(1, 100)
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(2, 150)
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(3, 100)
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(4, 100)
        except Exception:
            pass
        try:
            self.table.verticalHeader().setDefaultSectionSize(44)
        except Exception:
            pass
        layout.addWidget(self.table)

        # Summary for partial receive (live)
        self.received_total_label = QLabel("Received Total: Rs 0.00")
        self.payable_label = QLabel("Amount Payable to Supplier: Rs 0.00")
        try:
            self.received_total_label.setStyleSheet("font-size: 13px; font-weight: 600; margin-top: 6px;")
            self.payable_label.setStyleSheet("font-size: 13px; font-weight: 700; margin-top: 2px;")
        except Exception:
            pass
        layout.addWidget(self.received_total_label)
        layout.addWidget(self.payable_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.receive_all_btn = QPushButton("Receive All (Full Delivery)")
        self.receive_all_btn.setProperty('accent', 'Qt.green')
        self.receive_all_btn.setMinimumHeight(40)
        self.receive_all_btn.clicked.connect(self.receive_all)
        
        self.receive_partial_btn = QPushButton("Receive Partial Delivery")
        self.receive_partial_btn.setProperty('accent', 'Qt.blue')
        self.receive_partial_btn.setMinimumHeight(40)
        self.receive_partial_btn.clicked.connect(self.receive_partial)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.receive_all_btn)
        button_layout.addWidget(self.receive_partial_btn)
        button_layout.addStretch()
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_purchase(self):
        try:
            self.purchase = self.controller.session.get(Purchase, self.purchase_id)
            if not self.purchase:
                QMessageBox.critical(self, "Error", "Purchase not found")
                self.reject()
                return
            
            if self.purchase.status == 'RECEIVED':
                QMessageBox.warning(self, "Already Received", 
                                   "This purchase has already been received.")
                self.reject()
                return
            
            # Update info label
            supplier = self.controller.session.get(Supplier, self.purchase.supplier_id) if hasattr(self.purchase, 'supplier_id') else None
            supplier_name = supplier.name if supplier else "Unknown"
            
            self.info_label.setText(
                f"Purchase: {self.purchase.purchase_number} | "
                f"Supplier: {supplier_name} | "
                f"Status: {self.purchase.status} | "
                f"Total: Rs {self.purchase.total_amount:,.2f}"
            )
            
            # Load items
            items = self.controller.session.query(PurchaseItem).filter(  # TODO: Add .all() or .first()
                PurchaseItem.purchase_id == self.purchase_id
            ).all()
            
            self.table.setRowCount(len(items))
            for i, item in enumerate(items):
                product = self.controller.session.get(Product, item.product_id)
                product_name = product.name if product else f"Product #{item.product_id}"
                
                # Product name
                self.table.setItem(i, 0, QTableWidgetItem(product_name))
                
                # Ordered quantity
                self.table.setItem(i, 1, QTableWidgetItem(str(item.quantity)))
                
                # Received quantity (editable spinbox)
                received_spin = QDoubleSpinBox()
                try:
                    received_spin.setDecimals(3)
                except Exception:
                    pass
                try:
                    received_spin.setButtonSymbols(QAbstractSpinBox.NoButtons)
                except Exception:
                    pass
                try:
                    received_spin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                except Exception:
                    pass
                try:
                    received_spin.setMinimumHeight(28)
                except Exception:
                    pass
                try:
                    received_spin.setMinimumWidth(120)
                except Exception:
                    pass
                try:
                    received_spin.setStyleSheet("padding-right: 6px; padding-left: 6px;")
                except Exception:
                    pass
                try:
                    received_spin.setKeyboardTracking(False)
                except Exception:
                    pass
                try:
                    max_qty = float(getattr(item, 'quantity', 0.0) or 0.0)
                except Exception:
                    max_qty = 0.0
                try:
                    received_spin.setRange(0.0, max_qty)
                except Exception:
                    pass
                try:
                    received_spin.setValue(max_qty)  # Default to full quantity
                except Exception:
                    pass
                received_spin.setProperty('product_id', item.product_id)
                try:
                    received_spin.setProperty('unit_cost', float(getattr(item, 'unit_cost', 0.0) or 0.0))
                except Exception:
                    received_spin.setProperty('unit_cost', 0.0)
                try:
                    received_spin.setFocusPolicy(Qt.StrongFocus)
                except Exception:
                    pass
                self.table.setCellWidget(i, 2, received_spin)

                try:
                    self.table.setRowHeight(i, 44)
                except Exception:
                    pass

                try:
                    received_spin.valueChanged.connect(self._update_received_summary)
                except Exception:
                    pass
                
                # Unit cost
                self.table.setItem(i, 3, QTableWidgetItem(f"Rs {item.unit_cost:,.2f}"))
                
                # Total
                total = item.quantity * item.unit_cost
                self.table.setItem(i, 4, QTableWidgetItem(f"Rs {total:,.2f}"))

            try:
                self._update_received_summary()
            except Exception:
                pass
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load purchase: {str(e)}")
            self.reject()

    def _compute_received_total(self) -> float:
        total = 0.0
        try:
            for i in range(self.table.rowCount()):
                spin = self.table.cellWidget(i, 2)
                if not spin:
                    continue
                try:
                    qty = float(spin.value())
                except Exception:
                    qty = 0.0
                try:
                    unit_cost = float(spin.property('unit_cost') or 0.0)
                except Exception:
                    unit_cost = 0.0
                total += (qty * unit_cost)
        except Exception:
            return 0.0
        return float(total)

    def _update_received_summary(self, *args):
        try:
            received_total = float(self._compute_received_total())
        except Exception:
            received_total = 0.0

        try:
            self.received_total_label.setText(f"Received Total: Rs {received_total:,.2f}")
        except Exception:
            pass
        try:
            self.payable_label.setText(f"Amount Payable to Supplier: Rs {received_total:,.2f}")
        except Exception:
            pass
    
    def get_received_items(self):
        """Get dictionary of product_id: received_quantity from table"""
        items_received = {}
        for i in range(self.table.rowCount()):
            spin = self.table.cellWidget(i, 2)
            if spin:
                product_id = spin.property('product_id')
                try:
                    received_qty = float(spin.value())
                except Exception:
                    try:
                        received_qty = float(int(spin.value()))
                    except Exception:
                        received_qty = 0.0
                items_received[product_id] = received_qty
        return items_received
    
    def receive_all(self):
        """Receive all items at full quantity"""
        try:
            # Set all spinboxes to max
            for i in range(self.table.rowCount()):
                spin = self.table.cellWidget(i, 2)
                if spin:
                    try:
                        spin.setValue(float(spin.maximum()))
                    except Exception:
                        try:
                            spin.setValue(int(spin.maximum()))
                        except Exception:
                            pass
            
            # Confirm
            reply = QMessageBox.question(
                self,
                "Confirm Full Delivery",
                f"Receive all items for purchase {self.purchase.purchase_number}?\n\n"
                f"This will update inventory stock levels.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.controller.receive_purchase(self.purchase_id, None)
                QMessageBox.information(self, "Success", 
                                       f"Purchase {self.purchase.purchase_number} received!\n"
                                       f"Inventory has been updated.")
                self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to receive purchase: {str(e)}")
    
    def receive_partial(self):
        """Receive items with quantities specified in table"""
        try:
            items_received = self.get_received_items()
            
            # Check if any items are being received
            if not any(qty > 0 for qty in items_received.values()):
                QMessageBox.warning(self, "No Items", 
                                   "Please specify at least one item to receive.")
                return
            
            # Confirm
            total_items = sum(1 for qty in items_received.values() if qty > 0)
            try:
                received_total = float(self._compute_received_total())
            except Exception:
                received_total = 0.0
            reply = QMessageBox.question(
                self,
                "Confirm Partial Delivery",
                f"Receive {total_items} item(s) for purchase {self.purchase.purchase_number}?\n\n"
                f"Amount Payable to Supplier: Rs {received_total:,.2f}\n\n"
                f"Stock levels will be updated accordingly.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.controller.receive_purchase(self.purchase_id, items_received)
                QMessageBox.information(self, "Success", 
                                       f"Partial delivery received for {self.purchase.purchase_number}!\n"
                                       f"Inventory has been updated.")
                self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to receive purchase: {str(e)}")
