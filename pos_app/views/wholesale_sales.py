try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QFrame, QGridLayout,
        QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QLineEdit,
        QSizePolicy, QHeaderView
    )
    from PySide6.QtCore import Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QFrame, QGridLayout,
        QComboBox, QSpinBox, QDoubleSpinBox, QMessageBox, QLineEdit,
        QSizePolicy, QHeaderView
    )
    from PyQt6.QtCore import Qt
from .sales import ReceiptPreviewDialog  # Import the receipt dialog

class WholesaleSalesWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.current_cart = []
        # Build UI immediately to avoid blank page
        try:
            self.setup_ui()
        except Exception:
            # Fail-safe: do not crash if setup hits a transient error
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        # Header
        header = QLabel("💼 Wholesale Sales")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Quick add row
        barcode_row = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode or type SKU/Name")
        self.barcode_input.returnPressed.connect(self._on_barcode_enter)
        refresh_btn = QPushButton("🔄 Refresh")
        try:
            refresh_btn.setProperty("accent", "Qt.blue")
        except Exception:
            pass
        refresh_btn.setMinimumHeight(44)
        refresh_btn.clicked.connect(self.refresh_lists)
        barcode_row.addWidget(QLabel("Scan/Search:"))
        barcode_row.addWidget(self.barcode_input)
        barcode_row.addWidget(refresh_btn)
        layout.addLayout(barcode_row)

        content = QHBoxLayout()

        # Left side
        left_layout = QVBoxLayout()
        cart_frame = self.create_frame("Wholesale Cart")
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(4)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Quantity", "Price", "Action"])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        try:
            # Clamp Actions column to prevent overflow
            self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
            self.cart_table.horizontalHeader().resizeSection(3, 120)
        except Exception:
            pass
        try:
            self.cart_table.setSelectionBehavior(self.cart_table.QAbstractItemView.SelectRows)
            self.cart_table.setSelectionMode(self.cart_table.QAbstractItemView.SingleSelection)
        except Exception:
            pass
        cart_frame.layout().addWidget(self.cart_table)
        left_layout.addWidget(cart_frame)

        checkout_frame = self.create_frame("Checkout")
        checkout_layout = QGridLayout()

        # Customer selection
        checkout_layout.addWidget(QLabel("Customer:"), 0, 0)
        self.customer_combo = QComboBox()
        checkout_layout.addWidget(self.customer_combo, 0, 1)

        # Show customer balance
        self.customer_balance = QLabel("Balance: Rs 0.00")
        checkout_layout.addWidget(self.customer_balance, 1, 0, 1, 2)
        try:
            self.customer_combo.currentIndexChanged.connect(self._update_customer_balance)
        except Exception:
            pass

        # Payment method (including credit)
        checkout_layout.addWidget(QLabel("Payment:"), 2, 0)
        self.pay_method_combo = QComboBox()
        self.pay_method_combo.addItems(["Credit", "Cash", "Bank"])  # default Credit
        checkout_layout.addWidget(self.pay_method_combo, 2, 1)

        # Amount paid (partial payment)
        checkout_layout.addWidget(QLabel("Amount Paid:"), 3, 0)
        self.amount_paid_input = QDoubleSpinBox()
        self.amount_paid_input.setDecimals(2)
        self.amount_paid_input.setMaximum(1_000_000_000.0)
        self.amount_paid_input.setValue(0.00)
        checkout_layout.addWidget(self.amount_paid_input, 3, 1)

        # Totals
        self.subtotal_label = QLabel("Subtotal: Rs 0.00")
        self.tax_label = QLabel("Tax (10%): Rs 0.00")
        self.total_label = QLabel("Total: Rs 0.00")
        checkout_layout.addWidget(self.subtotal_label, 4, 0, 1, 2)
        checkout_layout.addWidget(self.tax_label, 5, 0, 1, 2)
        checkout_layout.addWidget(self.total_label, 6, 0, 1, 2)

        checkout_btn = QPushButton("Complete Wholesale Sale")
        try:
            checkout_btn.setProperty("accent", "Qt.green")
        except Exception:
            pass
        checkout_btn.setMinimumHeight(44)
        checkout_btn.clicked.connect(self.process_sale)
        checkout_layout.addWidget(checkout_btn, 7, 0, 1, 2)

        checkout_frame.layout().addLayout(checkout_layout)
        left_layout.addWidget(checkout_frame)

        content.addLayout(left_layout, 1)  # Full width for cart and checkout

        layout.addLayout(content)

        # Load customers only (no products table)
        self.load_customers()
        # No products table selection needed

        # Debounced barcode add (no Enter required)
        try:
            from PySide6.QtCore import QTimer
        except ImportError:
            from PyQt6.QtCore import QTimer
        
        self._barcode_timer = QTimer(self)
        self._barcode_timer.setSingleShot(True)
        self._barcode_timer.setInterval(180)
        try:
            self._barcode_timer.timeout.connect(self._on_barcode_enter)
        except Exception:
            pass
        self.barcode_input.textChanged.connect(self._on_barcode_changed)

    # --- Keyboard navigation and shortcuts ---
    def keyPressEvent(self, event):
        try:
            key = event.key()
            if key in (Qt.Key_Return, Qt.Key_Enter):
                # Only complete sale with Ctrl+Enter to avoid scanner auto-submit
                if event.modifiers() & Qt.ControlModifier:
                    self.process_sale()
                    self.barcode_input.setFocus()
                # Otherwise ignore; barcode_input.returnPressed handles adding
                return
            if key == Qt.Key_F5:
                self.refresh_lists()
                self.barcode_input.setFocus()
                return
            if key in (Qt.Key_Plus, Qt.Key_Equal):
                # Products table removed - use barcode input instead
                self.barcode_input.setFocus()
                return
            if key == Qt.Key_Delete:
                # Remove selected cart row
                row = self.cart_table.currentRow()
                if row >= 0:
                    self.remove_from_cart(row)
                self.barcode_input.setFocus()
                return
            if key == Qt.Key_Up:
                # Products table removed - focus on cart navigation instead
                if self.cart_table.rowCount() > 0:
                    current_row = self.cart_table.currentRow()
                    new_row = max(0, current_row - 1)
                    self.cart_table.selectRow(new_row)
                self.barcode_input.setFocus()
                return
            if key == Qt.Key_Down:
                # Products table removed - focus on cart navigation instead
                if self.cart_table.rowCount() > 0:
                    current_row = self.cart_table.currentRow()
                    new_row = min(self.cart_table.rowCount() - 1, current_row + 1)
                    self.cart_table.selectRow(new_row)
                self.barcode_input.setFocus()
                return
        except Exception:
            pass
        super().keyPressEvent(event)

    def showEvent(self, event):
        try:
            self.refresh_lists()
            self.barcode_input.setFocus()
        except Exception:
            pass
        super().showEvent(event)

    def refresh_lists(self):
        self.load_products()
        self.load_customers()
        self._update_customer_balance()

    def create_frame(self, title):
        frame = QFrame()
        # Use global dark theme card style defined as QFrame#card in utils.styles
        frame.setObjectName('card')
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        return frame

    def _on_barcode_enter(self):
        term = (self.barcode_input.text() or "").strip()
        if not term:
            return
        try:
            products = self.controller.get_products() if hasattr(self.controller, 'get_products') else []
            match = None
            for p in products:
                code = getattr(p, 'barcode', None)
                sku = getattr(p, 'sku', None)
                name = getattr(p, 'name', '') or ''
                if term and (term == code or term == sku or term.lower() in name.lower()):
                    match = p
                    break
            if match:
                self.add_to_cart(match, qty=1)
            else:
                QMessageBox.information(self, "Not found", f"No product matches '{term}'")
        finally:
            self.barcode_input.clear()

    def _on_barcode_changed(self, _text):
        try:
            self._barcode_timer.stop()
            if len((_text or '').strip()) >= 3:
                self._barcode_timer.start()
        except Exception:
            pass

    def process_sale(self):
        if not self.current_cart:
            QMessageBox.warning(self, "Warning", "Cart is empty!")
            return
        try:
            # Get selected customer
            customer_id = self.customer_combo.currentData()
            customer_name = self.customer_combo.currentText() if customer_id else "Walk-in Customer"
            
            # Prepare items for sale
            items = [{
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price': item['price']
            } for item in self.current_cart]
            
            pay_method = self.pay_method_combo.currentText()
            try:
                amount_paid = float(self.amount_paid_input.value())
            except (ValueError, TypeError):
                amount_paid = 0.0
            
            # Force wholesale flag
            try:
                # Convert payment method to uppercase to match PostgreSQL enum
                pay_method_upper = pay_method.upper().replace(' ', '_')
                sale = self.controller.create_sale(customer_id, items, True, payment_method=pay_method_upper, amount_paid=amount_paid)
            except TypeError:
                sale = self.controller.create_sale(customer_id, items, True)
            
            # Prepare receipt data for wholesale
            receipt_data = {
                'customer_name': customer_name,
                'sale_type': 'Wholesale',
                'payment_method': pay_method,
                'amount_paid': amount_paid,
                'cashier': 'Admin',  # You can get this from user session
                'items': [{
                    'name': item['name'],
                    'quantity': item['quantity'],
                    'price': item['price']
                } for item in self.current_cart]
            }
            
            # Show receipt preview dialog
            receipt_dialog = ReceiptPreviewDialog(receipt_data, self)
            receipt_dialog.exec()

            # Clear cart and reset after dialog closes
            self.current_cart.clear()
            self.update_cart_table()
            self.update_totals()
            self.amount_paid_input.setValue(0.0)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process sale: {str(e)}")

    def load_products(self):
        # Products table removed - no longer needed
        # Users will add products via barcode scanning or search
        pass

    def load_customers(self):
        customers = self.controller.get_customers()
        self.customer_combo.clear()
        for c in customers:
            # Only show wholesale customers prominently, but allow selecting any with credit limit
            self.customer_combo.addItem(c.name, c.id)
        self._update_customer_balance()

    def _update_customer_balance(self):
        try:
            cid = self.customer_combo.currentData()
            if not cid:
                self.customer_balance.setText("Balance: Rs 0.00")
                return
            cust = None
            # session access through controller
            if hasattr(self.controller, 'session'):
                from models.database import Customer
                cust = self.controller.session.get(Customer, cid)
            bal = getattr(cust, 'current_credit', 0.0) if cust else 0.0
            self.customer_balance.setText(f"Balance: Rs {bal:,.2f}")
        except Exception:
            self.customer_balance.setText("Balance: Rs 0.00")

    def add_to_cart(self, product, qty=1):
        price = getattr(product, 'wholesale_price', None)
        if price is None:
            price = getattr(product, 'retail_price', 0.0)
        self.current_cart.append({
            'product_id': product.id,
            'name': product.name,
            'quantity': qty,
            'price': price or 0.0
        })
        self.update_cart_table()
        self.update_totals()

    def update_cart_table(self):
        self.cart_table.setRowCount(len(self.current_cart))
        for i, item in enumerate(self.current_cart):
            self.cart_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 2, QTableWidgetItem(f"Rs {item['price']:,.2f}"))
            # Simple Remove button without table widget
            remove_btn = QPushButton("Remove")
            remove_btn.setProperty("accent", "Qt.red")
            remove_btn.setProperty("size", "compact")
            remove_btn.setFixedSize(60, 24)
            remove_btn.clicked.connect(lambda checked, row=i: self.remove_from_cart(row))
            self.cart_table.setCellWidget(i, 3, remove_btn)
            try:
                self.cart_table.setRowHeight(i, 36)
            except Exception:
                pass

    def remove_from_cart(self, row):
        if 0 <= row < len(self.current_cart):
            del self.current_cart[row]
            self.update_cart_table()
            self.update_totals()

    def update_totals(self):
        subtotal = sum(item['price'] * item['quantity'] for item in self.current_cart)
        tax = subtotal * 0.1
        total = subtotal + tax
        self.subtotal_label.setText(f"Subtotal: Rs {subtotal:,.2f}")
        self.tax_label.setText(f"Tax (10%): Rs {tax:,.2f}")
        self.total_label.setText(f"Total: Rs {total:,.2f}")
