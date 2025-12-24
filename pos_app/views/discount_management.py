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
from datetime import datetime, timedelta
import logging

class DiscountManagementWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("🏷️ Discount Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        
        # Active Discounts
        active_tab = self.create_active_discounts_tab()
        tabs.addTab(active_tab, "🏷️ Active Discounts")
        
        # Product Discounts
        product_tab = self.create_product_discounts_tab()
        tabs.addTab(product_tab, "📦 Product Discounts")
        
        # Customer Discounts
        customer_tab = self.create_customer_discounts_tab()
        tabs.addTab(customer_tab, "👥 Customer Discounts")
        
        layout.addWidget(tabs)

    def create_active_discounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Actions
        actions_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Create Discount")
        add_btn.setProperty('accent', 'Qt.green')
        add_btn.setMinimumHeight(40)
        add_btn.clicked.connect(self.create_discount)
        
        edit_btn = QPushButton("✏️ Edit")
        edit_btn.setProperty('accent', 'Qt.blue')
        edit_btn.setMinimumHeight(40)
        
        deactivate_btn = QPushButton("⏸️ Deactivate")
        deactivate_btn.setProperty('accent', 'orange')
        deactivate_btn.setMinimumHeight(40)
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setProperty('accent', 'Qt.red')
        delete_btn.setMinimumHeight(40)
        
        actions_layout.addWidget(add_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(deactivate_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Discounts table
        self.discounts_table = QTableWidget()
        self.discounts_table.setColumnCount(8)
        self.discounts_table.setHorizontalHeaderLabels([
            "Name", "Type", "Value", "Min Qty", "Min Amount", "Valid From", "Valid To", "Status"
        ])
        
        layout.addWidget(self.discounts_table)
        self.load_discounts()
        return widget

    def create_product_discounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Product discount controls
        controls_frame = QFrame()
        controls_frame.setProperty('role', 'card')
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("Product:"))
        self.product_combo = QComboBox()
        self.load_products()
        controls_layout.addWidget(self.product_combo)
        
        controls_layout.addWidget(QLabel("Discount %:"))
        self.product_discount = QDoubleSpinBox()
        self.product_discount.setRange(0, 100)
        self.product_discount.setSuffix("%")
        controls_layout.addWidget(self.product_discount)
        
        apply_product_btn = QPushButton("Apply Discount")
        apply_product_btn.setProperty('accent', 'Qt.green')
        apply_product_btn.clicked.connect(self.apply_product_discount)
        controls_layout.addWidget(apply_product_btn)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_frame)

        # Product discounts table
        self.product_discounts_table = QTableWidget()
        self.product_discounts_table.setColumnCount(6)
        self.product_discounts_table.setHorizontalHeaderLabels([
            "Product", "Original Price", "Discount %", "Discounted Price", "Valid Until", "Actions"
        ])
        
        layout.addWidget(self.product_discounts_table)
        self.load_product_discounts()
        return widget

    def create_customer_discounts_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Customer discount controls
        controls_frame = QFrame()
        controls_frame.setProperty('role', 'card')
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.load_customers()
        controls_layout.addWidget(self.customer_combo)
        
        controls_layout.addWidget(QLabel("Discount %:"))
        self.customer_discount = QDoubleSpinBox()
        self.customer_discount.setRange(0, 100)
        self.customer_discount.setSuffix("%")
        controls_layout.addWidget(self.customer_discount)
        
        apply_customer_btn = QPushButton("Apply Discount")
        apply_customer_btn.setProperty('accent', 'Qt.green')
        apply_customer_btn.clicked.connect(self.apply_customer_discount)
        controls_layout.addWidget(apply_customer_btn)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_frame)

        # Customer discounts table
        self.customer_discounts_table = QTableWidget()
        self.customer_discounts_table.setColumnCount(5)
        self.customer_discounts_table.setHorizontalHeaderLabels([
            "Customer", "Type", "Discount %", "Applied Date", "Actions"
        ])
        
        layout.addWidget(self.customer_discounts_table)
        self.load_customer_discounts()
        return widget

    def create_discount(self):
        dialog = DiscountDialog(self, self.controller)
        if dialog.exec() == QDialog.Accepted:
            try:
                from pos_app.models.database import Discount, DiscountType, CustomerType
                
                discount_type = DiscountType.PERCENTAGE if dialog.discount_type.currentText() == "Percentage" else DiscountType.FIXED_AMOUNT
                customer_type = None
                if dialog.customer_type.currentText() != "All":
                    customer_type = 'RETAIL' if dialog.customer_type.currentText() == "Retail" else 'WHOLESALE'
                
                discount = Discount(
                    name=dialog.name.text(),
                    description=dialog.description.toPlainText(),
                    discount_type=discount_type,
                    value=dialog.value.value(),
                    min_quantity=dialog.min_quantity.value(),
                    min_amount=dialog.min_amount.value(),
                    max_discount=dialog.max_discount.value() if dialog.max_discount.value() > 0 else None,
                    start_date=dialog.start_date.dateTime().toPython(),
                    end_date=dialog.end_date.dateTime().toPython(),
                    customer_type=customer_type,
                    product_id=dialog.product_combo.currentData() if dialog.product_combo.currentData() else None,
                    is_active=True
                )
                
                self.controller.session.add(discount)
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", "Discount created successfully!")
                self.load_discounts()
                
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to create discount: {str(e)}")

    def apply_product_discount(self):
        try:
            from pos_app.models.database import Product
            
            product_id = self.product_combo.currentData()
            discount_percent = self.product_discount.value()
            
            if not product_id:
                QMessageBox.warning(self, "Warning", "Please select a product")
                return
            
            product = self.controller.session.get(Product, product_id)
            if product:
                product.discount_percentage = discount_percent
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", f"Discount applied to {product.name}")
                self.load_product_discounts()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to apply discount: {str(e)}")

    def apply_customer_discount(self):
        try:
            from pos_app.models.database import Customer
            
            customer_id = self.customer_combo.currentData()
            discount_percent = self.customer_discount.value()
            
            if not customer_id:
                QMessageBox.warning(self, "Warning", "Please select a customer")
                return
            
            customer = self.controller.session.get(Customer, customer_id)
            if customer:
                customer.discount_percentage = discount_percent
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", f"Discount applied to {customer.name}")
                self.load_customer_discounts()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to apply discount: {str(e)}")

    def load_discounts(self):
        try:
            from pos_app.models.database import Discount
            
            discounts = self.controller.session.query(Discount).filter(  # TODO: Add .all() or .first()
                Discount.is_active == True
            ).all()
            
            self.discounts_table.setRowCount(len(discounts))
            
            for i, discount in enumerate(discounts):
                self.discounts_table.setItem(i, 0, QTableWidgetItem(discount.name))
                self.discounts_table.setItem(i, 1, QTableWidgetItem(discount.discount_type.value.replace("_", " ").title()))
                
                if discount.discount_type.value == "percentage":
                    value_text = f"{discount.value}%"
                else:
                    value_text = f"Rs {discount.value:,.2f}"
                self.discounts_table.setItem(i, 2, QTableWidgetItem(value_text))
                
                self.discounts_table.setItem(i, 3, QTableWidgetItem(str(discount.min_quantity)))
                self.discounts_table.setItem(i, 4, QTableWidgetItem(f"Rs {discount.min_amount:,.2f}"))
                
                start_date = discount.start_date.strftime('%Y-%m-%d') if discount.start_date else ""
                self.discounts_table.setItem(i, 5, QTableWidgetItem(start_date))
                
                end_date = discount.end_date.strftime('%Y-%m-%d') if discount.end_date else ""
                self.discounts_table.setItem(i, 6, QTableWidgetItem(end_date))
                
                # Check if discount is currently valid
                now = datetime.now()
                is_valid = True
                if discount.start_date and now < discount.start_date:
                    is_valid = False
                if discount.end_date and now > discount.end_date:
                    is_valid = False
                
                status = "Active" if is_valid else "Expired"
                status_item = QTableWidgetItem(status)
                if not is_valid:
                    status_item.setForeground(Qt.red)
                self.discounts_table.setItem(i, 7, status_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load discounts: {str(e)}")

    def load_product_discounts(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(  # TODO: Add .all() or .first()
                Product.discount_percentage > 0,
                Product.is_active == True
            ).all()
            
            self.product_discounts_table.setRowCount(len(products))
            
            for i, product in enumerate(products):
                self.product_discounts_table.setItem(i, 0, QTableWidgetItem(product.name))
                self.product_discounts_table.setItem(i, 1, QTableWidgetItem(f"Rs {product.retail_price:,.2f}"))
                self.product_discounts_table.setItem(i, 2, QTableWidgetItem(f"{product.discount_percentage}%"))
                
                discounted_price = product.retail_price * (1 - product.discount_percentage / 100)
                self.product_discounts_table.setItem(i, 3, QTableWidgetItem(f"Rs {discounted_price:,.2f}"))
                
                self.product_discounts_table.setItem(i, 4, QTableWidgetItem("Permanent"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load product discounts: {str(e)}")

    def load_customer_discounts(self):
        try:
            from pos_app.models.database import Customer
            
            customers = self.controller.session.query(Customer).filter(  # TODO: Add .all() or .first()
                Customer.discount_percentage > 0,
                Customer.is_active == True
            ).all()
            
            self.customer_discounts_table.setRowCount(len(customers))
            
            for i, customer in enumerate(customers):
                self.customer_discounts_table.setItem(i, 0, QTableWidgetItem(customer.name))
                customer_type = str(customer.type).title() if customer.type else ""
                self.customer_discounts_table.setItem(i, 1, QTableWidgetItem(customer_type))
                self.customer_discounts_table.setItem(i, 2, QTableWidgetItem(f"{customer.discount_percentage}%"))
                
                applied_date = customer.updated_at.strftime('%Y-%m-%d') if customer.updated_at else ""
                self.customer_discounts_table.setItem(i, 3, QTableWidgetItem(applied_date))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customer discounts: {str(e)}")

    def load_products(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(  # TODO: Add .all() or .first()
                Product.is_active == True
            ).all()
            
            self.product_combo.clear()
            self.product_combo.addItem("Select Product", None)
            
            for product in products:
                self.product_combo.addItem(f"{product.name} - Rs {product.retail_price:,.2f}", product.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")

    def load_customers(self):
        try:
            from pos_app.models.database import Customer
            
            customers = self.controller.session.query(Customer).filter(  # TODO: Add .all() or .first()
                Customer.is_active == True
            ).all()
            
            self.customer_combo.clear()
            self.customer_combo.addItem("Select Customer", None)
            
            for customer in customers:
                customer_type = str(customer.type).title() if customer.type else "Retail"
                self.customer_combo.addItem(f"{customer.name} ({customer_type})", customer.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customers: {str(e)}")


class DiscountDialog(QDialog):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Create Discount")
        self.setMinimumSize(500, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., Summer Sale, Bulk Discount")
        layout.addRow("Discount Name:", self.name)

        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.description.setPlaceholderText("Description of the discount...")
        layout.addRow("Description:", self.description)

        self.discount_type = QComboBox()
        self.discount_type.addItems(["Percentage", "Fixed Amount"])
        layout.addRow("Discount Type:", self.discount_type)

        self.value = QDoubleSpinBox()
        self.value.setRange(0, 100000)
        self.value.setDecimals(2)
        layout.addRow("Discount Value:", self.value)

        self.min_quantity = QSpinBox()
        self.min_quantity.setRange(1, 1000)
        self.min_quantity.setValue(1)
        layout.addRow("Minimum Quantity:", self.min_quantity)

        self.min_amount = QDoubleSpinBox()
        self.min_amount.setRange(0, 1000000)
        self.min_amount.setSuffix(" Rs")
        layout.addRow("Minimum Amount:", self.min_amount)

        self.max_discount = QDoubleSpinBox()
        self.max_discount.setRange(0, 100000)
        self.max_discount.setSuffix(" Rs")
        layout.addRow("Maximum Discount (Rs):", self.max_discount)

        self.start_date = QDateEdit()
        self.start_date.setDateTime(datetime.now())
        self.start_date.setCalendarPopup(True)
        layout.addRow("Valid From:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setDateTime(datetime.now() + timedelta(days=30))
        self.end_date.setCalendarPopup(True)
        layout.addRow("Valid Until:", self.end_date)

        self.customer_type = QComboBox()
        self.customer_type.addItems(["All", "Retail", "Wholesale"])
        layout.addRow("Customer Type:", self.customer_type)

        # Product selection
        self.product_combo = QComboBox()
        self.load_products()
        layout.addRow("Specific Product:", self.product_combo)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Create Discount")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addRow(buttons_layout)

    def load_products(self):
        try:
            from pos_app.models.database import Product
            
            self.product_combo.addItem("All Products", None)
            
            products = self.controller.session.query(Product).filter(  # TODO: Add .all() or .first()
                Product.is_active == True
            ).all()
            
            for product in products:
                self.product_combo.addItem(product.name, product.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
