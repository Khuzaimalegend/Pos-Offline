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

class WarehouseRetailInventoryWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🏪 Warehouse & Retail Inventory")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        
        # Warehouse Inventory
        warehouse_tab = self.create_warehouse_tab()
        tabs.addTab(warehouse_tab, "🏭 Warehouse")
        
        # Retail Inventory
        retail_tab = self.create_retail_tab()
        tabs.addTab(retail_tab, "🏪 Retail Store")
        
        # Stock Transfer
        transfer_tab = self.create_transfer_tab()
        tabs.addTab(transfer_tab, "🔄 Stock Transfer")
        
        # Stock Movements
        movements_tab = self.create_movements_tab()
        tabs.addTab(movements_tab, "📊 Stock Movements")
        
        layout.addWidget(tabs)

    def create_warehouse_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Warehouse summary
        summary_frame = QFrame()
        summary_frame.setProperty('role', 'card')
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total warehouse value
        value_frame = QFrame()
        value_frame.setProperty('role', 'card')
        value_layout = QVBoxLayout(value_frame)
        
        self.warehouse_value_label = QLabel("Rs 0.00")
        self.warehouse_value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        value_layout.addWidget(QLabel("💰 Total Warehouse Value"))
        value_layout.addWidget(self.warehouse_value_label)
        
        # Total items
        items_frame = QFrame()
        items_frame.setProperty('role', 'card')
        items_layout = QVBoxLayout(items_frame)
        
        self.warehouse_items_label = QLabel("0")
        self.warehouse_items_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        items_layout.addWidget(QLabel("📦 Total Items"))
        items_layout.addWidget(self.warehouse_items_label)
        
        # Low stock alerts
        alerts_frame = QFrame()
        alerts_frame.setProperty('role', 'card')
        alerts_layout = QVBoxLayout(alerts_frame)
        
        self.warehouse_alerts_label = QLabel("0")
        self.warehouse_alerts_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #ef4444;")
        alerts_layout.addWidget(QLabel("⚠️ Low Stock Alerts"))
        alerts_layout.addWidget(self.warehouse_alerts_label)
        
        summary_layout.addWidget(value_frame)
        summary_layout.addWidget(items_frame)
        summary_layout.addWidget(alerts_frame)
        
        layout.addWidget(summary_frame)

        # Warehouse actions
        actions_layout = QHBoxLayout()
        
        receive_btn = QPushButton("📥 Receive Stock")
        receive_btn.setProperty('accent', 'Qt.green')
        receive_btn.setMinimumHeight(40)
        receive_btn.clicked.connect(self.receive_warehouse_stock)
        
        adjust_btn = QPushButton("⚖️ Stock Adjustment")
        adjust_btn.setProperty('accent', 'Qt.blue')
        adjust_btn.setMinimumHeight(40)
        adjust_btn.clicked.connect(self.adjust_warehouse_stock)
        
        transfer_btn = QPushButton("🔄 Transfer to Retail")
        transfer_btn.setProperty('accent', 'orange')
        transfer_btn.setMinimumHeight(40)
        transfer_btn.clicked.connect(self.transfer_to_retail)
        
        actions_layout.addWidget(receive_btn)
        actions_layout.addWidget(adjust_btn)
        actions_layout.addWidget(transfer_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Warehouse inventory table
        self.warehouse_table = QTableWidget()
        self.warehouse_table.setColumnCount(8)
        self.warehouse_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Warehouse Stock", "Location", "Reorder Level", 
            "Value", "Last Updated", "Status"
        ])
        self.warehouse_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.warehouse_table)
        self.load_warehouse_inventory()
        return widget

    def create_retail_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Retail summary
        summary_frame = QFrame()
        summary_frame.setProperty('role', 'card')
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total retail value
        value_frame = QFrame()
        value_frame.setProperty('role', 'card')
        value_layout = QVBoxLayout(value_frame)
        
        self.retail_value_label = QLabel("Rs 0.00")
        self.retail_value_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #8b5cf6;")
        value_layout.addWidget(QLabel("💰 Total Retail Value"))
        value_layout.addWidget(self.retail_value_label)
        
        # Total items
        items_frame = QFrame()
        items_frame.setProperty('role', 'card')
        items_layout = QVBoxLayout(items_frame)
        
        self.retail_items_label = QLabel("0")
        self.retail_items_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #06b6d4;")
        items_layout.addWidget(QLabel("🛍️ Items on Display"))
        items_layout.addWidget(self.retail_items_label)
        
        # Out of stock
        stock_frame = QFrame()
        stock_frame.setProperty('role', 'card')
        stock_layout = QVBoxLayout(stock_frame)
        
        self.retail_outofstock_label = QLabel("0")
        self.retail_outofstock_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f59e0b;")
        stock_layout.addWidget(QLabel("❌ Out of Stock"))
        stock_layout.addWidget(self.retail_outofstock_label)
        
        summary_layout.addWidget(value_frame)
        summary_layout.addWidget(items_frame)
        summary_layout.addWidget(stock_frame)
        
        layout.addWidget(summary_frame)

        # Retail actions
        actions_layout = QHBoxLayout()
        
        restock_btn = QPushButton("📦 Restock from Warehouse")
        restock_btn.setProperty('accent', 'Qt.green')
        restock_btn.setMinimumHeight(40)
        restock_btn.clicked.connect(self.restock_from_warehouse)
        
        adjust_retail_btn = QPushButton("⚖️ Stock Adjustment")
        adjust_retail_btn.setProperty('accent', 'Qt.blue')
        adjust_retail_btn.setMinimumHeight(40)
        adjust_retail_btn.clicked.connect(self.adjust_retail_stock)
        
        return_btn = QPushButton("↩️ Return to Warehouse")
        return_btn.setProperty('accent', 'orange')
        return_btn.setMinimumHeight(40)
        return_btn.clicked.connect(self.return_to_warehouse)
        
        actions_layout.addWidget(restock_btn)
        actions_layout.addWidget(adjust_retail_btn)
        actions_layout.addWidget(return_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Retail inventory table
        self.retail_table = QTableWidget()
        self.retail_table.setColumnCount(8)
        self.retail_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Retail Stock", "Shelf Location", "Min Display", 
            "Value", "Last Sale", "Status"
        ])
        self.retail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.retail_table)
        self.load_retail_inventory()
        return widget

    def create_transfer_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Transfer form
        transfer_frame = QFrame()
        transfer_frame.setProperty('role', 'card')
        transfer_layout = QFormLayout(transfer_frame)
        
        # Product selection
        self.transfer_product = QComboBox()
        self.load_products_for_transfer()
        transfer_layout.addRow("Product:", self.transfer_product)
        
        # Transfer direction
        self.transfer_direction = QComboBox()
        self.transfer_direction.addItems(["Warehouse → Retail", "Retail → Warehouse"])
        transfer_layout.addRow("Direction:", self.transfer_direction)
        
        # Quantity
        self.transfer_quantity = QSpinBox()
        self.transfer_quantity.setRange(1, 10000)
        transfer_layout.addRow("Quantity:", self.transfer_quantity)
        
        # Notes
        self.transfer_notes = QLineEdit()
        self.transfer_notes.setPlaceholderText("Transfer reason/notes...")
        transfer_layout.addRow("Notes:", self.transfer_notes)
        
        # Transfer button
        transfer_btn = QPushButton("🔄 Execute Transfer")
        transfer_btn.setProperty('accent', 'Qt.green')
        transfer_btn.setMinimumHeight(40)
        transfer_btn.clicked.connect(self.execute_transfer)
        transfer_layout.addRow(transfer_btn)
        
        layout.addWidget(transfer_frame)

        # Recent transfers
        recent_label = QLabel("📋 Recent Transfers")
        recent_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px 0 10px 0;")
        layout.addWidget(recent_label)

        # Recent transfers table
        self.transfers_table = QTableWidget()
        self.transfers_table.setColumnCount(7)
        self.transfers_table.setHorizontalHeaderLabels([
            "Date", "Product", "Direction", "Quantity", "From Stock", "To Stock", "Notes"
        ])
        
        layout.addWidget(self.transfers_table)
        self.load_recent_transfers()
        return widget

    def create_movements_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filters
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Product:"))
        self.movement_product_filter = QComboBox()
        self.movement_product_filter.addItem("All Products", None)
        self.load_products_for_filter()
        filter_layout.addWidget(self.movement_product_filter)
        
        filter_layout.addWidget(QLabel("Location:"))
        self.movement_location_filter = QComboBox()
        self.movement_location_filter.addItems(["All Locations", "Warehouse", "Retail"])
        filter_layout.addWidget(self.movement_location_filter)
        
        filter_layout.addWidget(QLabel("Type:"))
        self.movement_type_filter = QComboBox()
        self.movement_type_filter.addItems(["All Types", "IN", "OUT", "ADJUSTMENT", "TRANSFER"])
        filter_layout.addWidget(self.movement_type_filter)
        
        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.filter_movements)
        filter_layout.addWidget(filter_btn)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)

        # Stock movements table
        self.movements_table = QTableWidget()
        self.movements_table.setColumnCount(7)
        self.movements_table.setHorizontalHeaderLabels([
            "Date", "Product", "Location", "Type", "Quantity", "Reference", "Notes"
        ])
        
        layout.addWidget(self.movements_table)
        self.load_stock_movements()
        return widget

    def load_warehouse_inventory(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(
                Product.is_active == True,
                Product.warehouse_stock > 0
            ).all()
            
            self.warehouse_table.setRowCount(len(products))
            
            total_value = 0
            total_items = 0
            low_stock_count = 0
            
            for i, product in enumerate(products):
                self.warehouse_table.setItem(i, 0, QTableWidgetItem(product.name))
                self.warehouse_table.setItem(i, 1, QTableWidgetItem(product.sku or ""))
                
                # Warehouse stock with color coding
                stock_item = QTableWidgetItem(str(product.warehouse_stock))
                if product.warehouse_stock <= product.reorder_level:
                    stock_item.setForeground(Qt.red)
                    low_stock_count += 1
                self.warehouse_table.setItem(i, 2, stock_item)
                
                self.warehouse_table.setItem(i, 3, QTableWidgetItem(product.warehouse_location or ""))
                self.warehouse_table.setItem(i, 4, QTableWidgetItem(str(product.reorder_level)))
                
                # Calculate value
                value = product.warehouse_stock * product.purchase_price
                total_value += value
                total_items += product.warehouse_stock
                
                self.warehouse_table.setItem(i, 5, QTableWidgetItem(f"Rs {value:,.2f}"))
                
                updated = product.updated_at.strftime('%Y-%m-%d') if product.updated_at else ""
                self.warehouse_table.setItem(i, 6, QTableWidgetItem(updated))
                
                status = "Low Stock" if product.warehouse_stock <= product.reorder_level else "Normal"
                status_item = QTableWidgetItem(status)
                if status == "Low Stock":
                    status_item.setForeground(Qt.red)
                self.warehouse_table.setItem(i, 7, status_item)
                
                # Store product ID
                self.warehouse_table.item(i, 0).setData(Qt.UserRole, product.id)
            
            # Update summary
            self.warehouse_value_label.setText(f"Rs {total_value:,.2f}")
            self.warehouse_items_label.setText(f"{total_items:,}")
            self.warehouse_alerts_label.setText(str(low_stock_count))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load warehouse inventory: {str(e)}")

    def load_retail_inventory(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(
                Product.is_active == True
            ).all()
            
            self.retail_table.setRowCount(len(products))
            
            total_value = 0
            total_items = 0
            out_of_stock_count = 0
            
            for i, product in enumerate(products):
                self.retail_table.setItem(i, 0, QTableWidgetItem(product.name))
                self.retail_table.setItem(i, 1, QTableWidgetItem(product.sku or ""))
                
                # Retail stock with color coding
                retail_stock = getattr(product, 'retail_stock', 0)
                stock_item = QTableWidgetItem(str(retail_stock))
                if retail_stock == 0:
                    stock_item.setForeground(Qt.red)
                    out_of_stock_count += 1
                elif retail_stock <= 5:  # Assuming min display is 5
                    stock_item.setForeground(Qt.darkYellow)
                self.retail_table.setItem(i, 2, stock_item)
                
                self.retail_table.setItem(i, 3, QTableWidgetItem(product.shelf_location or ""))
                self.retail_table.setItem(i, 4, QTableWidgetItem("5"))  # Min display placeholder
                
                # Calculate value
                value = retail_stock * product.retail_price
                total_value += value
                total_items += retail_stock
                
                self.retail_table.setItem(i, 5, QTableWidgetItem(f"Rs {value:,.2f}"))
                
                self.retail_table.setItem(i, 6, QTableWidgetItem("2024-01-01"))  # Last sale placeholder
                
                status = "Out of Stock" if retail_stock == 0 else ("Low" if retail_stock <= 5 else "Normal")
                status_item = QTableWidgetItem(status)
                if status == "Out of Stock":
                    status_item.setForeground(Qt.red)
                elif status == "Low":
                    status_item.setForeground(Qt.darkYellow)
                self.retail_table.setItem(i, 7, status_item)
                
                # Store product ID
                self.retail_table.item(i, 0).setData(Qt.UserRole, product.id)
            
            # Update summary
            self.retail_value_label.setText(f"Rs {total_value:,.2f}")
            self.retail_items_label.setText(f"{total_items:,}")
            self.retail_outofstock_label.setText(str(out_of_stock_count))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load retail inventory: {str(e)}")

    def load_products_for_transfer(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(
                Product.is_active == True
            ).all()
            
            self.transfer_product.clear()
            for product in products:
                warehouse_stock = getattr(product, 'warehouse_stock', 0)
                retail_stock = getattr(product, 'retail_stock', 0)
                self.transfer_product.addItem(
                    f"{product.name} (W:{warehouse_stock}, R:{retail_stock})", 
                    product.id
                )
                
        except Exception as e:
            logging.exception("Failed to load products for transfer")

    def load_products_for_filter(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(
                Product.is_active == True
            ).all()
            
            for product in products:
                self.movement_product_filter.addItem(product.name, product.id)
                
        except Exception as e:
            logging.exception("Failed to load products for filter")

    def load_recent_transfers(self):
        try:
            from pos_app.models.database import StockMovement, Product
            
            transfers = self.controller.session.query(StockMovement).join(Product).filter(  # TODO: Add .all() or .first()
                StockMovement.movement_type == "TRANSFER"
            ).order_by(StockMovement.date.desc()).limit(50).all()
            
            self.transfers_table.setRowCount(len(transfers))
            
            for i, transfer in enumerate(transfers):
                self.transfers_table.setItem(i, 0, QTableWidgetItem(
                    transfer.date.strftime('%Y-%m-%d %H:%M') if transfer.date else ""
                ))
                self.transfers_table.setItem(i, 1, QTableWidgetItem(transfer.product.name if transfer.product else ""))
                
                # Determine direction from notes or reference
                direction = "Warehouse → Retail"  # Default
                if "retail" in (transfer.notes or "").lower() and "warehouse" in (transfer.notes or "").lower():
                    direction = "Retail → Warehouse" if transfer.quantity < 0 else "Warehouse → Retail"
                
                self.transfers_table.setItem(i, 2, QTableWidgetItem(direction))
                self.transfers_table.setItem(i, 3, QTableWidgetItem(str(abs(transfer.quantity))))
                self.transfers_table.setItem(i, 4, QTableWidgetItem(""))  # From stock placeholder
                self.transfers_table.setItem(i, 5, QTableWidgetItem(""))  # To stock placeholder
                self.transfers_table.setItem(i, 6, QTableWidgetItem(transfer.notes or ""))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load recent transfers: {str(e)}")

    def load_stock_movements(self):
        try:
            from pos_app.models.database import StockMovement, Product
            
            movements = self.controller.session.query(StockMovement).join(Product).order_by(
                StockMovement.date.desc()
            ).limit(100).all()
            
            self.movements_table.setRowCount(len(movements))
            
            for i, movement in enumerate(movements):
                self.movements_table.setItem(i, 0, QTableWidgetItem(
                    movement.date.strftime('%Y-%m-%d %H:%M') if movement.date else ""
                ))
                self.movements_table.setItem(i, 1, QTableWidgetItem(movement.product.name if movement.product else ""))
                
                location = getattr(movement, 'location', None)
                location_text = str(location) if location else "Unknown"
                self.movements_table.setItem(i, 2, QTableWidgetItem(location_text))
                
                self.movements_table.setItem(i, 3, QTableWidgetItem(movement.movement_type))
                
                # Color code quantity based on type
                qty_item = QTableWidgetItem(str(movement.quantity))
                if movement.movement_type == "OUT":
                    qty_item.setForeground(Qt.red)
                elif movement.movement_type == "IN":
                    qty_item.setForeground(Qt.green)
                self.movements_table.setItem(i, 4, qty_item)
                
                self.movements_table.setItem(i, 5, QTableWidgetItem(movement.reference or ""))
                self.movements_table.setItem(i, 6, QTableWidgetItem(movement.notes or ""))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load stock movements: {str(e)}")

    def execute_transfer(self):
        try:
            product_id = self.transfer_product.currentData()
            direction = self.transfer_direction.currentText()
            quantity = self.transfer_quantity.value()
            notes = self.transfer_notes.text()
            
            if not product_id:
                QMessageBox.warning(self, "Warning", "Please select a product")
                return
            
            from pos_app.models.database import Product, StockMovement, InventoryLocation
            
            product = self.controller.session.get(Product, product_id)
            if not product:
                QMessageBox.warning(self, "Warning", "Product not found")
                return
            
            # Check stock availability
            if "Warehouse → Retail" in direction:
                if getattr(product, 'warehouse_stock', 0) < quantity:
                    QMessageBox.warning(self, "Warning", "Insufficient warehouse stock")
                    return
                
                # Update stocks
                product.warehouse_stock = getattr(product, 'warehouse_stock', 0) - quantity
                product.retail_stock = getattr(product, 'retail_stock', 0) + quantity
                
                # Create stock movements
                # Warehouse OUT
                warehouse_out = StockMovement(
                    product_id=product_id,
                    date=datetime.now(),
                    movement_type="OUT",
                    quantity=quantity,
                    location=InventoryLocation.WAREHOUSE,
                    reference=f"Transfer to Retail",
                    notes=notes
                )
                
                # Retail IN
                retail_in = StockMovement(
                    product_id=product_id,
                    date=datetime.now(),
                    movement_type="IN",
                    quantity=quantity,
                    location=InventoryLocation.RETAIL,
                    reference=f"Transfer from Warehouse",
                    notes=notes
                )
                
            else:  # Retail → Warehouse
                if getattr(product, 'retail_stock', 0) < quantity:
                    QMessageBox.warning(self, "Warning", "Insufficient retail stock")
                    return
                
                # Update stocks
                product.retail_stock = getattr(product, 'retail_stock', 0) - quantity
                product.warehouse_stock = getattr(product, 'warehouse_stock', 0) + quantity
                
                # Create stock movements
                # Retail OUT
                retail_out = StockMovement(
                    product_id=product_id,
                    date=datetime.now(),
                    movement_type="OUT",
                    quantity=quantity,
                    location=InventoryLocation.RETAIL,
                    reference=f"Transfer to Warehouse",
                    notes=notes
                )
                
                # Warehouse IN
                warehouse_in = StockMovement(
                    product_id=product_id,
                    date=datetime.now(),
                    movement_type="IN",
                    quantity=quantity,
                    location=InventoryLocation.WAREHOUSE,
                    reference=f"Transfer from Retail",
                    notes=notes
                )
            
            # Update total stock
            product.stock_level = getattr(product, 'warehouse_stock', 0) + getattr(product, 'retail_stock', 0)
            
            self.controller.session.commit()
            
            QMessageBox.information(self, "Success", f"Transfer completed successfully!")
            
            # Refresh all tables
            self.load_warehouse_inventory()
            self.load_retail_inventory()
            self.load_recent_transfers()
            self.load_stock_movements()
            
            # Clear form
            self.transfer_quantity.setValue(1)
            self.transfer_notes.clear()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to execute transfer: {str(e)}")

    # Placeholder methods for other actions
    def receive_warehouse_stock(self):
        QMessageBox.information(self, "Info", "Receive warehouse stock dialog would open here")

    def adjust_warehouse_stock(self):
        QMessageBox.information(self, "Info", "Warehouse stock adjustment dialog would open here")

    def transfer_to_retail(self):
        QMessageBox.information(self, "Info", "Quick transfer to retail dialog would open here")

    def restock_from_warehouse(self):
        QMessageBox.information(self, "Info", "Restock from warehouse dialog would open here")

    def adjust_retail_stock(self):
        QMessageBox.information(self, "Info", "Retail stock adjustment dialog would open here")

    def return_to_warehouse(self):
        QMessageBox.information(self, "Info", "Return to warehouse dialog would open here")

    def filter_movements(self):
        self.load_stock_movements()
