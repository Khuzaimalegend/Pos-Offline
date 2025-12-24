try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
        QHBoxLayout, QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
        QTabWidget, QTextEdit, QDateEdit, QHeaderView, QGroupBox, QSplitter, QCheckBox,
        QDialogButtonBox, QCompleter, QSpinBox, QDoubleSpinBox, QAbstractItemView, QScrollArea
    )
    from PySide6.QtCore import Qt, QDate
    from PySide6.QtGui import QColor
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
        QHBoxLayout, QDialog, QFormLayout, QLineEdit, QComboBox, QMessageBox,
        QTabWidget, QTextEdit, QDateEdit, QHeaderView, QGroupBox, QSplitter, QCheckBox,
        QDialogButtonBox, QCompleter, QSpinBox, QDoubleSpinBox, QAbstractItemView, QScrollArea
    )
    from PyQt6.QtCore import Qt, QDate
    from PyQt6.QtGui import QColor

from pos_app.models.database import (
    Purchase, PurchaseItem, Product, Supplier, PurchasePayment,
    PaymentMethod, PaymentStatus
)
from pos_app.models.session import session_scope
from datetime import datetime
import calendar


class SelectSupplierDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.selected_id = None
        self.setWindowTitle("Select Supplier")
        layout = QFormLayout(self)
        self.search = QLineEdit()
        self.combo = QComboBox()
        layout.addRow("Search:", self.search)
        layout.addRow("Supplier:", self.combo)
        btn = QPushButton("Select")
        btn.clicked.connect(self._select)
        layout.addRow(btn)
        self._all = self.session.query(Supplier).filter(Supplier.is_active == True).all()
        self._populate()
        self.search.textChanged.connect(self._populate)

    def _populate(self):
        term = (self.search.text() or "").lower()
        items = [s for s in self._all if term in (s.name or '').lower() or term in (s.contact or '').lower()]
        self.combo.clear()
        for s in items:
            self.combo.addItem(f"{s.name} (#{s.id})", s.id)

    def _select(self):
        self.selected_id = self.combo.currentData()
        self.accept()


class SelectProductDialog(QDialog):
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.selected_id = None
        self.selected_product = None
        self.setWindowTitle("Select Product - Barcode Search")
        self.setMinimumSize(500, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("🔍 Search Product by Barcode, SKU, or Name")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #3b82f6;
            padding: 10px 0;
        """)
        layout.addWidget(header)
        
        # Barcode search widget
        from pos_app.widgets.barcode_search import BarcodeSearchWidget
        self.barcode_widget = BarcodeSearchWidget(
            session=self.session,
            parent=self,
            show_quantity=False,
            auto_add=False
        )
        self.barcode_widget.product_selected.connect(self._on_product_selected)
        layout.addWidget(self.barcode_widget)
        
        # Selected product info
        self.selected_info = QLabel("No product selected")
        self.selected_info.setStyleSheet("""
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 10px;
            color: #94a3b8;
        """)
        layout.addWidget(self.selected_info)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Select Product")
        button_box.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        
        # Focus the barcode widget
        self.barcode_widget.focus_input()

    def _on_product_selected(self, product):
        """Handle product selection from barcode widget"""
        self.selected_product = product
        self.selected_id = product.id
        
        # Update info display
        info_text = f"""
        <b>{product.name}</b><br>
        SKU: {product.sku or 'N/A'}<br>
        Barcode: {product.barcode or 'N/A'}<br>
        Price: Rs {product.purchase_price or product.retail_price:,.2f}<br>
        Stock: {product.stock_level or 0}
        """
        self.selected_info.setText(info_text)
        self.ok_button.setEnabled(True)


class PurchaseItemWidget(QWidget):
    def __init__(self, session=None, product_id=None, product_name=None, parent=None):
        super().__init__(parent)
        self.session = session
        self.product_id = product_id
        self.setup_ui(product_name)
        
    def setup_ui(self, product_name=None):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Product selector with searchable dropdown
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        try:
            # Qt6 style enum
            self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        except Exception:
            try:
                # Qt5/PySide6 fallback
                self.product_combo.setInsertPolicy(QComboBox.NoInsert)
            except Exception:
                pass
        self.product_combo.setMinimumWidth(260)
        self._load_products()
        completer = QCompleter(self.product_combo.model(), self)
        try:
            completer.setCaseSensitivity(False)
            from PySide6.QtCore import Qt as _Qt
            completer.setFilterMode(_Qt.MatchContains)
        except Exception:
            pass
        self.product_combo.setCompleter(completer)
        
        # Quantity input
        self.quantity = QSpinBox()
        self.quantity.setRange(1, 1000000)
        self.quantity.setValue(1)
        
        # Unit cost input
        self.unit_cost = QDoubleSpinBox()
        self.unit_cost.setRange(0, 1000000)
        self.unit_cost.setDecimals(2)
        self.unit_cost.setPrefix("Rs ")
        
        # Total cost (read-only)
        self.total_cost = QLabel("Rs 0.00")
        
        # Connect signals
        self.quantity.valueChanged.connect(self.update_total)
        self.unit_cost.valueChanged.connect(self.update_total)
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        
        # Add widgets to layout
        layout.addWidget(self.product_combo, 40)
        layout.addWidget(QLabel("Qty:"))
        layout.addWidget(self.quantity, 10)
        layout.addWidget(QLabel("Unit Cost:"))
        layout.addWidget(self.unit_cost, 20)
        layout.addWidget(QLabel("Total:"))
        layout.addWidget(self.total_cost, 20)
        
        # Remove button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedSize(24, 24)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: Qt.white;
                border: none;
                border-radius: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        layout.addWidget(self.remove_btn)
        
        self.update_total()
    
    def update_total(self):
        total = self.quantity.value() * self.unit_cost.value()
        self.total_cost.setText(f"Rs {total:,.2f}")
        # Notify parent dialog so it can update subtotal/total labels
        try:
            parent = self.parent()
            # Walk up until we find a widget with update_totals
            while parent is not None and not hasattr(parent, 'update_totals'):
                parent = parent.parent()
            if parent is not None:
                parent.update_totals()
        except Exception:
            pass
    
    def get_data(self):
        return {
            'product_id': self.product_id,
            'quantity': self.quantity.value(),
            'unit_cost': self.unit_cost.value(),
            'total': self.quantity.value() * self.unit_cost.value()
        }

    def _load_products(self):
        if not self.session:
            return
        try:
            self.product_combo.clear()
            products = self.session.query(Product).filter(Product.is_active == True).all()
            for p in products:
                label = f"{p.name} (SKU: {p.sku or '-'} )"
                self.product_combo.addItem(label, p.id)
            # If preselected
            if self.product_id:
                idx = self.product_combo.findData(self.product_id)
                if idx >= 0:
                    self.product_combo.setCurrentIndex(idx)
        except Exception:
            pass

    def on_product_changed(self, index):
        try:
            pid = self.product_combo.currentData()
            self.product_id = pid
            # Try to set default unit cost from product purchase_price
            if pid and self.session:
                prod = self.session.get(Product, pid)
                if prod and getattr(prod, 'purchase_price', None) is not None:
                    self.unit_cost.setValue(float(prod.purchase_price))
        except Exception:
            pass


class CreatePurchaseDialog(QDialog):
    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Create Purchase Order")
        self.setMinimumSize(900, 650)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header section
        header = QLabel("Create Purchase Order")
        header.setStyleSheet("""
            font-size: 22px;
            font-weight: 700;
            color: #1e293b;
        """)
        sub_header = QLabel("Select a supplier, then add products using barcode search or name.")
        sub_header.setStyleSheet("""
            font-size: 12px;
            color: #64748b;
        """)

        header_layout = QVBoxLayout()
        header_layout.addWidget(header)
        header_layout.addWidget(sub_header)
        main_layout.addLayout(header_layout)

        # Top form card
        form_card = QGroupBox("Order Details")
        form_card.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #4b5563;
            }
        """)
        form_layout = QFormLayout(form_card)
        form_layout.setLabelAlignment(Qt.AlignRight)
        form_layout.setHorizontalSpacing(12)
        form_layout.setVerticalSpacing(8)

        # Supplier selection
        self.supplier_name = QLineEdit()
        self.supplier_name.setReadOnly(True)
        self.supplier_id = None

        supplier_btn = QPushButton("Select Supplier")
        supplier_btn.setMinimumWidth(140)
        supplier_btn.clicked.connect(self.select_supplier)

        supplier_row = QHBoxLayout()
        supplier_row.addWidget(self.supplier_name, 1)
        supplier_row.addWidget(supplier_btn)

        supplier_row_widget = QWidget()
        supplier_row_widget.setLayout(supplier_row)

        # Order details
        self.order_date = QDateEdit()
        self.order_date.setCalendarPopup(True)
        self.order_date.setDate(QDate.currentDate())

        self.expected_delivery = QDateEdit()
        self.expected_delivery.setCalendarPopup(True)
        self.expected_delivery.setDate(QDate.currentDate().addDays(7))

        self.reference = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)

        # Add to form layout
        form_layout.addRow("Supplier:", supplier_row_widget)
        form_layout.addRow("Order Date:", self.order_date)
        form_layout.addRow("Expected Delivery:", self.expected_delivery)
        form_layout.addRow("Reference:", self.reference)
        form_layout.addRow("Notes:", self.notes)

        main_layout.addWidget(form_card)

        # Items section card
        items_group = QGroupBox("Items")
        items_group.setStyleSheet("""
            QGroupBox {
                font-weight: 600;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: #4b5563;
            }
        """)
        items_layout = QVBoxLayout(items_group)
        items_layout.setSpacing(8)

        # Items toolbar (Add + Barcode search)
        toolbar_layout = QHBoxLayout()

        add_item_btn = QPushButton("➕ Add Item (Name)")
        add_item_btn.clicked.connect(self.add_item)

        barcode_btn = QPushButton("📦 Add Item by Barcode")
        barcode_btn.clicked.connect(self.add_item_by_barcode)

        toolbar_layout.addWidget(add_item_btn)
        toolbar_layout.addWidget(barcode_btn)
        toolbar_layout.addStretch()

        items_layout.addLayout(toolbar_layout)

        # Items list container (so rows are actually visible)
        self.items_scroll = QScrollArea()
        try:
            self.items_scroll.setWidgetResizable(True)
        except Exception:
            pass
        try:
            self.items_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except Exception:
            pass
        try:
            self.items_scroll.setMinimumHeight(240)
        except Exception:
            pass

        self.items_container = QWidget()
        self.items_layout = QVBoxLayout(self.items_container)
        self.items_layout.setContentsMargins(0, 0, 0, 0)
        self.items_layout.setSpacing(10)
        self.items_layout.addStretch()

        try:
            self.items_scroll.setWidget(self.items_container)
        except Exception:
            pass

        items_layout.addWidget(self.items_scroll)
        items_layout.addStretch()

        main_layout.addWidget(items_group)

        # Totals row
        totals_layout = QHBoxLayout()
        totals_layout.addStretch()

        self.subtotal_label = QLabel("Subtotal: Rs 0.00")
        self.tax_label = QLabel("Tax (0%): Rs 0.00")
        self.total_label = QLabel("<b>Total: Rs 0.00</b>")

        for lbl in (self.subtotal_label, self.tax_label, self.total_label):
            lbl.setStyleSheet("font-size: 13px; color: #111827;")

        totals_layout.addWidget(self.subtotal_label)
        totals_layout.addSpacing(20)
        totals_layout.addWidget(self.tax_label)
        totals_layout.addSpacing(20)
        totals_layout.addWidget(self.total_label)

        main_layout.addLayout(totals_layout)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.create_purchase)
        button_box.rejected.connect(self.reject)

        main_layout.addWidget(button_box)
        
        # Install event filter to prevent Enter key from triggering save
        self.installEventFilter(self)

        # Add first blank item so the user sees a row immediately
        self.add_item()
    
    def add_item(self):
        item_widget = PurchaseItemWidget(session=self.controller.session)
        item_widget.remove_btn.clicked.connect(
            lambda: self.remove_item(item_widget)
        )
        self.items_layout.insertWidget(
            self.items_layout.count() - 1,  # Insert before the stretch
            item_widget
        )
        self.update_totals()

    def add_item_with_product(self, product):
        """Add an item row pre-selected with the given product (for barcode flows)."""
        try:
            item_widget = PurchaseItemWidget(
                session=self.controller.session,
                product_id=getattr(product, 'id', None),
                product_name=getattr(product, 'name', None),
            )
            # Default quantity 1 and unit cost from product purchase_price or retail_price
            if getattr(product, 'purchase_price', None) is not None:
                item_widget.unit_cost.setValue(float(product.purchase_price))
            elif getattr(product, 'retail_price', None) is not None:
                item_widget.unit_cost.setValue(float(product.retail_price))

            item_widget.remove_btn.clicked.connect(
                lambda: self.remove_item(item_widget)
            )
            self.items_layout.insertWidget(
                self.items_layout.count() - 1,
                item_widget
            )
            self.update_totals()
        except Exception:
            pass
    
    def remove_item(self, item_widget):
        if self.items_layout.count() > 2:  # Don't remove the last item
            item_widget.deleteLater()
            self.update_totals()
    
    def update_totals(self):
        subtotal = 0
        for i in range(self.items_layout.count()):
            item = self.items_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'get_data'):
                subtotal += item.widget().get_data()['total']
        
        # Update labels
        self.subtotal_label.setText(f"Subtotal: Rs {subtotal:,.2f}")
        self.total_label.setText(f"<b>Total: Rs {subtotal:,.2f}</b>")

    def add_item_by_barcode(self):
        """Open a barcode search dialog and add the selected product as a new item row."""
        try:
            dlg = SelectProductDialog(self.controller.session, self)
            if dlg.exec() == QDialog.Accepted and dlg.selected_product:
                self.add_item_with_product(dlg.selected_product)
        except Exception:
            QMessageBox.warning(self, "Error", "Unable to open barcode search for products.")
    
    def select_supplier(self):
        dialog = SelectSupplierDialog(self.controller.session, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_id:
            supplier = self.controller.session.query(Supplier).get(dialog.selected_id)
            if supplier:
                self.supplier_id = supplier.id
                self.supplier_name.setText(f"{supplier.name} ({supplier.contact or 'No contact'})")
    
    def get_data(self):
        items = []
        for i in range(self.items_layout.count()):
            item = self.items_layout.itemAt(i)
            if item.widget() and hasattr(item.widget(), 'get_data'):
                row = item.widget().get_data()
                if row.get('product_id', None):
                    items.append(row)
        # Convert QDate to Python date (compatible with both PyQt6 and PySide6)
        try:
            order_date = self.order_date.date().toPython()
        except AttributeError:
            # PyQt6 doesn't have toPython(), use tostring() and parse
            order_date_str = self.order_date.date().toString("yyyy-MM-dd")
            from datetime import datetime
            order_date = datetime.strptime(order_date_str, "%Y-%m-%d").date()
        
        try:
            expected_delivery = self.expected_delivery.date().toPython()
        except AttributeError:
            # PyQt6 doesn't have toPython(), use toString() and parse
            expected_delivery_str = self.expected_delivery.date().toString("yyyy-MM-dd")
            from datetime import datetime
            expected_delivery = datetime.strptime(expected_delivery_str, "%Y-%m-%d").date()
        
        return {
            'supplier_id': self.supplier_id,
            'order_date': order_date,
            'expected_delivery': expected_delivery,
            'reference': self.reference.text(),
            'notes': self.notes.toPlainText(),
            'items': items,
            'subtotal': sum(item['total'] for item in items),
            'tax_amount': 0,
            'total_amount': sum(item['total'] for item in items)
        }

    def search_supplier(self):
        try:
            dlg = SelectSupplierDialog(self.controller.session, self)
            if dlg.exec() == QDialog.Accepted and dlg.selected_id:
                sup = self.controller.session.get(Supplier, dlg.selected_id)
                self._supplier_id = sup.id
                self.supplier_name.setText(sup.name)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def search_product(self):
        try:
            dlg = SelectProductDialog(self.controller.session, self)
            if dlg.exec() == QDialog.Accepted and dlg.selected_id:
                prod = self.controller.session.get(Product, dlg.selected_id)
                self._product_id = prod.id
                self.product_name.setText(prod.name)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def eventFilter(self, obj, event):
        """Filter Enter/Return key events to prevent accidental purchase creation"""
        try:
            from PySide6.QtCore import QEvent
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import QEvent
            from PyQt6.QtCore import Qt
            
        if event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Only allow Enter on the Save button itself
                if not isinstance(obj, QPushButton):
                    return True  # Block the event
        return super().eventFilter(obj, event)
    
    def create_purchase(self):
        try:
            data = self.get_data()
            if not data.get('supplier_id', None):
                raise ValueError("Please select a supplier.")
            if not data.get('items', None):
                raise ValueError("Please add at least one product item.")
            # Build items list in expected format for controller
            items = [
                {
                    'product_id': int(it['product_id']),
                    'quantity': int(it['quantity']),
                    'unit_cost': float(it['unit_cost'])
                } for it in data['items']
            ]
            p = self.controller.create_purchase(int(data['supplier_id']), items)
            QMessageBox.information(self, "Success", f"Purchase created #{getattr(p, 'purchase_number', getattr(p, 'id', ''))}")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))


class RecordPaymentDialog(QDialog):
    def __init__(self, controller, purchase_id, supplier_id, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.purchase_id = purchase_id
        self.supplier_id = supplier_id
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Record Purchase Payment")
        layout = QFormLayout(self)

        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Enter amount to pay...")

        layout.addRow("Amount:", self.amount_input)

        # Add supplier info
        supplier_label = QLabel(f"Supplier: {self.controller.session.get(Supplier, self.supplier_id).name}")
        layout.addRow("Supplier:", supplier_label)

        btn = QPushButton("💰 Record Payment")
        btn.clicked.connect(self.record_payment)
        layout.addRow(btn)

    def record_payment(self):
        try:
            # Validate amount input
            amount_text = self.amount_input.text().strip()
            if not amount_text:
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric amount.")
                return
            
            try:
                amount = float(amount_text)
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid numeric amount.")
                return
            
            if amount <= 0:
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid amount greater than 0.")
                return

            pp = self.controller.record_purchase_payment(self.purchase_id, self.supplier_id, amount)
            QMessageBox.information(self, "Success", f"Recorded payment of Rs {pp.amount:.2f}")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to record payment: {str(e)}")


class PurchasesWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        # Header
        header_layout = QHBoxLayout()
        header = QLabel("💰 Purchase Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        add_btn = QPushButton("✨ New Purchase")
        add_btn.setProperty('accent', 'Qt.green')
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self.open_create)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Barcode search widget for quick product lookup
        from pos_app.widgets.barcode_search import BarcodeSearchWidget
        self.barcode_widget = BarcodeSearchWidget(
            session=self.controller.session,
            parent=self,
            show_quantity=True,
            auto_add=False
        )
        self.barcode_widget.product_selected.connect(self._on_product_scanned)
        layout.addWidget(self.barcode_widget)
        
        # Action buttons (initially disabled)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 10)
        
        self.receive_btn = QPushButton("📦 Receive Purchase")
        self.receive_btn.setProperty('accent', 'Qt.green')
        self.receive_btn.setMinimumHeight(36)
        self.receive_btn.setEnabled(False)
        self.receive_btn.clicked.connect(self.receive_selected_purchase)
        
        self.record_payment_btn = QPushButton("💰 Record Payment")
        self.record_payment_btn.setProperty('accent', 'orange')
        self.record_payment_btn.setMinimumHeight(36)
        self.record_payment_btn.setEnabled(False)
        self.record_payment_btn.clicked.connect(self.record_payment_selected)
        
        actions_layout.addWidget(self.receive_btn)
        actions_layout.addWidget(self.record_payment_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Financial Summary Section
        summary_frame = QWidget()
        summary_frame.setProperty('role', 'card')
        summary_layout = QHBoxLayout(summary_frame)
        summary_layout.setContentsMargins(15, 10, 15, 10)
        
        # Calculate totals
        try:
            purchases = self.controller.session.query(Purchase).all()
            total_purchases = sum(p.total_amount or 0.0 for p in purchases)
            total_paid = sum(p.paid_amount or 0.0 for p in purchases)
            total_remaining = total_purchases - total_paid
            
            # Total Purchases
            total_label = QLabel(f"💰 Total Purchases: Rs {total_purchases:,.2f}")
            total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #60a5fa;")
            
            # Total Paid
            paid_label = QLabel(f"✅ Total Paid: Rs {total_paid:,.2f}")
            paid_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #34d399;")
            
            # Total Outstanding
            outstanding_label = QLabel(f"⚠️ Outstanding: Rs {total_remaining:,.2f}")
            color = "#ef4444" if total_remaining > 0 else "#34d399"
            outstanding_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
            
            summary_layout.addWidget(total_label)
            summary_layout.addStretch()
            summary_layout.addWidget(paid_label)
            summary_layout.addStretch()
            summary_layout.addWidget(outstanding_label)
            
        except Exception:
            summary_label = QLabel("📊 Purchase Summary - Unable to calculate totals")
            summary_label.setStyleSheet("font-size: 14px; color: #9ca3af;")
            summary_layout.addWidget(summary_label)
        
        layout.addWidget(summary_frame)

        # Purchases Table (removed Actions column)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Date", "Supplier", "Items", "Total Amount", "Paid Amount", "Remaining", "Status"
        ])
        
        # Table selection
        try:
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        except Exception:
            pass
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.selected_purchase_id = None
        self.selected_supplier_id = None
        try:
            from PySide6.QtWidgets import QHeaderView
        except ImportError:
            from PyQt6.QtWidgets import QHeaderView
        
        # Make all columns stretch to fill the screen
        try:
            self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Date
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Supplier
            self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)  # Items
            self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Total Amount
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Paid Amount
            self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)  # Remaining
            self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)  # Status
            self.table.verticalHeader().setVisible(False)
            self.table.setWordWrap(True)
        except Exception:
            pass
        layout.addWidget(self.table, 1)  # Add stretch factor to make table expand
        self.load_purchases()

    def refresh_summary(self):
        """Refresh the financial summary section"""
        try:
            purchases = self.controller.session.query(Purchase).all()
            total_purchases = sum(p.total_amount or 0.0 for p in purchases)
            total_paid = sum(p.paid_amount or 0.0 for p in purchases)
            total_remaining = total_purchases - total_paid
            
            # Find and update summary labels (this is a simplified approach)
            # In a more robust implementation, we'd store references to these labels
            self.load_purchases()  # Reload everything for now
        except Exception:
            pass

    def load_purchases(self):
        purchases = self.controller.session.query(Purchase).order_by(Purchase.id.desc()).all()
        self.table.setRowCount(len(purchases))
        for i, p in enumerate(purchases):
            # Show actual purchase date instead of ID
            try:
                if hasattr(p, 'order_date') and p.order_date:
                    date_str = p.order_date.strftime('%Y-%m-%d %H:%M')
                elif hasattr(p, 'created_at') and p.created_at:
                    date_str = p.created_at.strftime('%Y-%m-%d %H:%M')
                else:
                    date_str = f'Purchase #{p.id}'
                self.table.setItem(i, 0, QTableWidgetItem(date_str))
            except Exception:
                self.table.setItem(i, 0, QTableWidgetItem(f'Purchase #{p.id}'))
            
            # Resolve supplier name
            try:
                sup = self.controller.session.get(Supplier, p.supplier_id) if p.supplier_id else None
                self.table.setItem(i, 1, QTableWidgetItem(sup.name if sup else f"Supplier #{p.supplier_id}"))
            except Exception:
                self.table.setItem(i, 1, QTableWidgetItem(f"Supplier #{p.supplier_id}"))
            
            # Show what items were purchased
            try:
                items = self.controller.session.query(PurchaseItem).filter(PurchaseItem.purchase_id == p.id).all()
                if items:
                    item_summary = []
                    for item in items[:3]:  # Show first 3 items
                        try:
                            product = self.controller.session.get(Product, item.product_id)
                            if product:
                                item_summary.append(f"{product.name} ({item.quantity})")
                            else:
                                item_summary.append(f"Product #{item.product_id} ({item.quantity})")
                        except Exception:
                            item_summary.append(f"Item ({item.quantity})")
                    
                    if len(items) > 3:
                        item_summary.append(f"... +{len(items)-3} more")
                    
                    items_text = ", ".join(item_summary)
                else:
                    items_text = "No items"
                self.table.setItem(i, 2, QTableWidgetItem(items_text))
            except Exception:
                self.table.setItem(i, 2, QTableWidgetItem("Unknown items"))
            
            # Financial information
            total_amount = p.total_amount or 0.0
            paid_amount = p.paid_amount or 0.0
            remaining_amount = total_amount - paid_amount
            
            self.table.setItem(i, 3, QTableWidgetItem(f"Rs {total_amount:,.2f}"))
            self.table.setItem(i, 4, QTableWidgetItem(f"Rs {paid_amount:,.2f}"))
            
            # Color-code remaining amount
            remaining_item = QTableWidgetItem(f"Rs {remaining_amount:,.2f}")
            if remaining_amount > 0:
                remaining_item.setForeground(QColor("#ef4444"))  # Red for outstanding
            else:
                remaining_item.setForeground(QColor("#10b981"))  # Green for fully paid
            self.table.setItem(i, 5, remaining_item)
            
            # Status column - show if received or not
            status_text = p.status or "ORDERED"
            status_item = QTableWidgetItem(status_text)
            
            # Color-code status
            if status_text == "RECEIVED":
                status_item.setForeground(QColor("#10b981"))  # Green for received
            elif status_text == "PARTIAL":
                status_item.setForeground(QColor("#f59e0b"))  # Yellow for partial
            elif status_text == "ORDERED":
                status_item.setForeground(QColor("#6b7280"))  # Gray for ordered
            else:
                status_item.setForeground(QColor("#3b82f6"))  # Blue for other statuses
            
            self.table.setItem(i, 6, status_item)
            
            # Store purchase and supplier IDs for selection handling
            date_item = self.table.item(i, 0)
            if date_item:
                date_item.setData(Qt.UserRole, p.id)
                date_item.setData(Qt.UserRole + 1, p.supplier_id)

    def open_create(self):
        dlg = CreatePurchaseDialog(self.controller, self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_summary()  # Refresh summary and table after new purchase

    def on_selection_changed(self):
        """Enable/disable action buttons based on selection and purchase status"""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # Get purchase and supplier IDs from the table item
            item = self.table.item(row, 0)
            if item:
                self.selected_purchase_id = item.data(Qt.UserRole)
                self.selected_supplier_id = item.data(Qt.UserRole + 1)
                
                # Check purchase status
                purchase = self.controller.session.get(Purchase, self.selected_purchase_id)
                if purchase:
                    # Enable receive button if purchase is PENDING, ORDERED, or PARTIAL
                    can_receive = purchase.status in ['PENDING', 'ORDERED', 'PARTIAL']
                    self.receive_btn.setEnabled(can_receive)
                    
                    # Payment button always enabled if purchase selected
                    self.record_payment_btn.setEnabled(True)
                else:
                    self.receive_btn.setEnabled(False)
                    self.record_payment_btn.setEnabled(False)
                    self.combine_btn.setEnabled(False)
            else:
                self.selected_purchase_id = None
                self.selected_supplier_id = None
                self.receive_btn.setEnabled(False)
                self.record_payment_btn.setEnabled(False)
                self.combine_btn.setEnabled(False)
        else:
            self.selected_purchase_id = None
            self.selected_supplier_id = None
            self.receive_btn.setEnabled(False)
            self.record_payment_btn.setEnabled(False)
            self.combine_btn.setEnabled(False)
        
        # Enable combine button if there are 2+ pending purchases
        try:
            pending_count = self.controller.session.query(Purchase).filter(
                Purchase.status == 'PENDING'
            ).count()
            if pending_count >= 2:
                self.combine_btn.setEnabled(True)
        except Exception:
            pass

    def record_payment_selected(self):
        if self.selected_purchase_id and self.selected_supplier_id:
            self.open_record_payment(self.selected_purchase_id, self.selected_supplier_id)

    def receive_selected_purchase(self):
        if self.selected_purchase_id:
            try:
                from pos_app.views.dialogs.receive_purchase_dialog import ReceivePurchaseDialog
                dlg = ReceivePurchaseDialog(self.controller, self.selected_purchase_id, self)
                if dlg.exec() == QDialog.Accepted:
                    self.refresh_summary()  # Refresh after receiving
            except Exception as e:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Critical)
                msg.setWindowTitle("Error")
                msg.setText(f"Failed to open receive dialog: {str(e)}")
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec()
    
    def open_record_payment(self, purchase_id, supplier_id):
        dlg = RecordPaymentDialog(self.controller, purchase_id, supplier_id, self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_summary()  # Refresh summary and table after payment
    
    def _on_product_scanned(self, product):
        """Handle product scanned from barcode widget"""
        try:
            # Show product info and ask what to do
            try:
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
            except ImportError:
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
            
            # Create a simple dialog instead of using QMessageBox with custom buttons
            dialog = QDialog(self)
            dialog.setWindowTitle("Product Found")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            # Product info
            info_text = (f"<b>{product.name}</b><br><br>"
                        f"SKU: {product.sku or 'N/A'}<br>"
                        f"Barcode: {product.barcode or 'N/A'}<br>"
                        f"Current Stock: {product.stock_level or 0}<br>"
                        f"Purchase Price: Rs {product.purchase_price or 0:,.2f}")
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            create_btn = QPushButton("Create Purchase Order")
            create_btn.clicked.connect(lambda: (self.open_create_with_product(product), dialog.accept()))
            button_layout.addWidget(create_btn)
            
            orders_btn = QPushButton("View Purchase Orders")
            orders_btn.clicked.connect(lambda: (self._show_product_orders(product), dialog.accept()))
            button_layout.addWidget(orders_btn)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.clicked.connect(dialog.reject)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            dialog.exec()
                
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to process scanned product: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
    
    def open_create_with_product(self, product):
        """Open create purchase dialog with a specific product pre-selected"""
        try:
            dlg = CreatePurchaseDialog(self.controller, self)
            # Pre-select the product if possible
            if hasattr(dlg, 'add_item_with_product'):
                dlg.add_item_with_product(product)
            if dlg.exec() == QDialog.Accepted:
                self.refresh_summary()
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to create purchase: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
    
    def _show_product_orders(self, product):
        """Show all purchase orders for this product"""
        try:
            try:
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QTableWidget, QTableWidgetItem
            except ImportError:
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox, QTableWidget, QTableWidgetItem
            
            from pos_app.models.database import Purchase, PurchaseItem
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Purchase Orders - {product.name}")
            dialog.setMinimumSize(600, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Title
            title = QLabel(f"<b>Purchase Orders for: {product.name}</b>")
            layout.addWidget(title)
            
            # Query purchase orders containing this product
            try:
                purchase_items = self.controller.session.query(PurchaseItem).filter(
                    PurchaseItem.product_id == product.id
                ).all()
                
                if not purchase_items:
                    no_orders = QLabel("No purchase orders found for this product.")
                    layout.addWidget(no_orders)
                else:
                    # Create table
                    table = QTableWidget()
                    table.setColumnCount(6)
                    table.setHorizontalHeaderLabels(["PO#", "Supplier", "Qty", "Unit Price", "Total", "Status"])
                    table.setRowCount(len(purchase_items))
                    
                    for row, item in enumerate(purchase_items):
                        purchase = item.purchase
                        supplier_name = purchase.supplier.name if purchase.supplier else "N/A"
                        status = purchase.status or "Pending"
                        
                        table.setItem(row, 0, QTableWidgetItem(str(purchase.id)))
                        table.setItem(row, 1, QTableWidgetItem(supplier_name))
                        table.setItem(row, 2, QTableWidgetItem(str(item.quantity)))
                        table.setItem(row, 3, QTableWidgetItem(f"Rs {item.unit_cost:,.2f}"))
                        table.setItem(row, 4, QTableWidgetItem(f"Rs {item.total_cost:,.2f}"))
                        table.setItem(row, 5, QTableWidgetItem(status))
                    
                    table.resizeColumnsToContents()
                    layout.addWidget(table)
            except Exception as query_err:
                error_label = QLabel(f"Error loading orders: {str(query_err)}")
                layout.addWidget(error_label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec()
            
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to show purchase orders: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
    
    def _show_product_details(self, product):
        """Show detailed product information"""
        try:
            try:
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
            except ImportError:
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Product Details - {product.name}")
            dialog.setMinimumSize(400, 300)
            
            layout = QVBoxLayout(dialog)
            
            details = f"""
            <h3>{product.name}</h3>
            <table>
            <tr><td><b>SKU:</b></td><td>{product.sku or 'N/A'}</td></tr>
            <tr><td><b>Barcode:</b></td><td>{product.barcode or 'N/A'}</td></tr>
            <tr><td><b>Description:</b></td><td>{product.description or 'N/A'}</td></tr>
            <tr><td><b>Purchase Price:</b></td><td>Rs {product.purchase_price or 0:,.2f}</td></tr>
            <tr><td><b>Retail Price:</b></td><td>Rs {product.retail_price or 0:,.2f}</td></tr>
            <tr><td><b>Wholesale Price:</b></td><td>Rs {product.wholesale_price or 0:,.2f}</td></tr>
            <tr><td><b>Current Stock:</b></td><td>{product.stock_level or 0}</td></tr>
            <tr><td><b>Reorder Level:</b></td><td>{product.reorder_level or 0}</td></tr>
            <tr><td><b>Supplier:</b></td><td>{product.supplier.name if product.supplier else 'N/A'}</td></tr>
            <tr><td><b>Unit:</b></td><td>{product.unit or 'N/A'}</td></tr>
            <tr><td><b>Location:</b></td><td>{product.shelf_location or 'N/A'}</td></tr>
            </table>
            """
            
            details_label = QLabel(details)
            details_label.setWordWrap(True)
            layout.addWidget(details_label)
            
            button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            button_box.rejected.connect(dialog.reject)
            layout.addWidget(button_box)
            
            dialog.exec()
            
        except Exception as e:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText(f"Failed to show product details: {str(e)}")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec()
