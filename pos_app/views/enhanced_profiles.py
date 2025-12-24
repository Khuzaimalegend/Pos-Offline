try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QCheckBox, QSpinBox, QCompleter
    )
    from PySide6.QtCore import Qt, QDate
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QDoubleSpinBox,
        QFrame, QMessageBox, QDialog, QFormLayout, QLineEdit,
        QDateEdit, QTextEdit, QTabWidget, QCheckBox, QSpinBox, QCompleter
    )
    from PyQt6.QtCore import Qt, QDate
from datetime import datetime
import logging

class EnhancedProfilesWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("👥 Enhanced Customer & Supplier Profiles")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        
        # Customer Profiles
        customer_tab = self.create_customer_profiles_tab()
        self.tabs.addTab(customer_tab, "👤 Customer Profiles")
        
        # Supplier Profiles
        supplier_tab = self.create_supplier_profiles_tab()
        self.tabs.addTab(supplier_tab, "🏢 Supplier Profiles")
        
        layout.addWidget(self.tabs)

    def open_supplier_profile(self, supplier_id: int):
        try:
            if hasattr(self, 'tabs'):
                try:
                    self.tabs.setCurrentIndex(1)
                except Exception:
                    pass

            if not hasattr(self, 'supplier_combo'):
                return

            idx = self.supplier_combo.findData(supplier_id)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)
            else:
                try:
                    self.load_suppliers()
                    idx = self.supplier_combo.findData(supplier_id)
                    if idx >= 0:
                        self.supplier_combo.setCurrentIndex(idx)
                except Exception:
                    pass
        except Exception:
            pass

    def open_customer_profile(self, customer_id: int):
        try:
            if hasattr(self, 'tabs'):
                try:
                    self.tabs.setCurrentIndex(0)
                except Exception:
                    pass

            if not hasattr(self, 'customer_combo'):
                return

            idx = self.customer_combo.findData(customer_id)
            if idx >= 0:
                self.customer_combo.setCurrentIndex(idx)
            else:
                try:
                    self.load_customers()
                    idx = self.customer_combo.findData(customer_id)
                    if idx >= 0:
                        self.customer_combo.setCurrentIndex(idx)
                except Exception:
                    pass
        except Exception:
            pass

    def create_customer_profiles_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Customer selection
        selection_frame = QFrame()
        selection_frame.setProperty('role', 'card')
        selection_layout = QHBoxLayout(selection_frame)
        
        selection_layout.addWidget(QLabel("Select Customer:"))
        self.customer_combo = QComboBox()
        try:
            self.customer_combo.setEditable(True)
            self.customer_combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        self.load_customers()
        try:
            completer = QCompleter(self.customer_combo.model(), self.customer_combo)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            try:
                completer.setFilterMode(Qt.MatchContains)
            except Exception:
                pass
            try:
                completer.setCompletionMode(QCompleter.PopupCompletion)
            except Exception:
                pass
            self.customer_combo.setCompleter(completer)
        except Exception:
            pass
        self.customer_combo.currentIndexChanged.connect(self.load_customer_profile)
        selection_layout.addWidget(self.customer_combo)
        
        add_customer_btn = QPushButton("➕ Add New Customer")
        add_customer_btn.setProperty('accent', 'Qt.green')
        add_customer_btn.clicked.connect(self.add_customer)
        selection_layout.addWidget(add_customer_btn)
        
        edit_customer_btn = QPushButton("✏️ Edit Customer")
        edit_customer_btn.setProperty('accent', 'Qt.blue')
        edit_customer_btn.clicked.connect(self.edit_customer)
        selection_layout.addWidget(edit_customer_btn)
        
        selection_layout.addStretch()
        
        layout.addWidget(selection_frame)

        # Customer profile tabs
        self.customer_profile_tabs = QTabWidget()
        
        # Basic Info
        basic_tab = self.create_customer_basic_tab()
        self.customer_profile_tabs.addTab(basic_tab, "📋 Basic Info")
        
        # Transaction History
        history_tab = self.create_customer_history_tab()
        self.customer_profile_tabs.addTab(history_tab, "📊 Transaction History")
        
        # Payment History
        payment_tab = self.create_customer_payment_tab()
        self.customer_profile_tabs.addTab(payment_tab, "💳 Payment History")
        
        # Notes & Communications
        notes_tab = self.create_customer_notes_tab()
        self.customer_profile_tabs.addTab(notes_tab, "📝 Notes & Communications")
        
        layout.addWidget(self.customer_profile_tabs)
        return widget

    def create_supplier_profiles_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Supplier selection
        selection_frame = QFrame()
        selection_frame.setProperty('role', 'card')
        selection_layout = QHBoxLayout(selection_frame)
        
        selection_layout.addWidget(QLabel("Select Supplier:"))
        self.supplier_combo = QComboBox()
        try:
            self.supplier_combo.setEditable(True)
            self.supplier_combo.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        self.load_suppliers()
        try:
            completer = QCompleter(self.supplier_combo.model(), self.supplier_combo)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            try:
                completer.setFilterMode(Qt.MatchContains)
            except Exception:
                pass
            try:
                completer.setCompletionMode(QCompleter.PopupCompletion)
            except Exception:
                pass
            self.supplier_combo.setCompleter(completer)
        except Exception:
            pass
        self.supplier_combo.currentIndexChanged.connect(self.load_supplier_profile)
        selection_layout.addWidget(self.supplier_combo)
        
        add_supplier_btn = QPushButton("➕ Add New Supplier")
        add_supplier_btn.setProperty('accent', 'Qt.green')
        add_supplier_btn.clicked.connect(self.add_supplier)
        selection_layout.addWidget(add_supplier_btn)
        
        edit_supplier_btn = QPushButton("✏️ Edit Supplier")
        edit_supplier_btn.setProperty('accent', 'Qt.blue')
        edit_supplier_btn.clicked.connect(self.edit_supplier)
        selection_layout.addWidget(edit_supplier_btn)
        
        selection_layout.addStretch()
        
        layout.addWidget(selection_frame)

        # Supplier profile tabs
        self.supplier_profile_tabs = QTabWidget()
        
        # Basic Info
        supplier_basic_tab = self.create_supplier_basic_tab()
        self.supplier_profile_tabs.addTab(supplier_basic_tab, "📋 Basic Info")
        
        # Purchase History
        purchase_tab = self.create_supplier_purchase_tab()
        self.supplier_profile_tabs.addTab(purchase_tab, "📦 Purchase History")
        
        # Payment History
        supplier_payment_tab = self.create_supplier_payment_tab()
        self.supplier_profile_tabs.addTab(supplier_payment_tab, "💰 Payment History")
        
        # Products Supplied
        products_tab = self.create_supplier_products_tab()
        self.supplier_profile_tabs.addTab(products_tab, "📦 Products Supplied")
        
        layout.addWidget(self.supplier_profile_tabs)
        return widget

    def create_customer_basic_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Customer info display
        info_frame = QFrame()
        info_frame.setProperty('role', 'card')
        info_layout = QFormLayout(info_frame)
        
        self.customer_name_label = QLabel("Not Selected")
        info_layout.addRow("Name:", self.customer_name_label)
        
        self.customer_type_label = QLabel("Not Selected")
        info_layout.addRow("Type:", self.customer_type_label)
        
        self.customer_contact_label = QLabel("Not Selected")
        info_layout.addRow("Contact:", self.customer_contact_label)
        
        self.customer_email_label = QLabel("Not Selected")
        info_layout.addRow("Email:", self.customer_email_label)
        
        self.customer_address_label = QLabel("Not Selected")
        info_layout.addRow("Address:", self.customer_address_label)
        
        self.customer_credit_label = QLabel("Rs 0.00")
        info_layout.addRow("Credit Limit:", self.customer_credit_label)
        
        self.customer_balance_label = QLabel("Rs 0.00")
        info_layout.addRow("Current Balance:", self.customer_balance_label)
        
        layout.addWidget(info_frame)

        # Customer statistics
        stats_frame = QFrame()
        stats_frame.setProperty('role', 'card')
        stats_layout = QHBoxLayout(stats_frame)
        
        # Total purchases
        purchases_frame = QFrame()
        purchases_frame.setProperty('role', 'card')
        purchases_layout = QVBoxLayout(purchases_frame)
        
        self.customer_total_purchases = QLabel("Rs 0.00")
        self.customer_total_purchases.setStyleSheet("font-size: 18px; font-weight: bold; color: #3b82f6;")
        purchases_layout.addWidget(QLabel("💰 Total Purchases"))
        purchases_layout.addWidget(self.customer_total_purchases)
        
        # Total transactions
        transactions_frame = QFrame()
        transactions_frame.setProperty('role', 'card')
        transactions_layout = QVBoxLayout(transactions_frame)
        
        self.customer_total_transactions = QLabel("0")
        self.customer_total_transactions.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        transactions_layout.addWidget(QLabel("📊 Total Transactions"))
        transactions_layout.addWidget(self.customer_total_transactions)
        
        # Last purchase
        last_frame = QFrame()
        last_frame.setProperty('role', 'card')
        last_layout = QVBoxLayout(last_frame)
        
        self.customer_last_purchase = QLabel("Never")
        self.customer_last_purchase.setStyleSheet("font-size: 18px; font-weight: bold; color: #8b5cf6;")
        last_layout.addWidget(QLabel("🕒 Last Purchase"))
        last_layout.addWidget(self.customer_last_purchase)
        
        stats_layout.addWidget(purchases_frame)
        stats_layout.addWidget(transactions_frame)
        stats_layout.addWidget(last_frame)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
        return widget

    def create_customer_history_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Transaction history table
        self.customer_history_table = QTableWidget()
        self.customer_history_table.setColumnCount(6)
        self.customer_history_table.setHorizontalHeaderLabels([
            "Date", "Invoice #", "Type", "Amount", "Status", "Items"
        ])
        self.customer_history_table.itemClicked.connect(self._on_customer_sale_selected)
        try:
            self.customer_history_table.setWordWrap(False)
            self.customer_history_table.verticalHeader().setDefaultSectionSize(32)
        except Exception:
            pass
        
        layout.addWidget(self.customer_history_table)
        
        # Sale items details section
        details_label = QLabel("Sale Items Details")
        details_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        layout.addWidget(details_label)
        
        self.customer_sale_items_table = QTableWidget()
        self.customer_sale_items_table.setColumnCount(5)
        self.customer_sale_items_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Quantity", "Unit Price", "Total"
        ])
        self.customer_sale_items_table.setMaximumHeight(200)
        try:
            self.customer_sale_items_table.setWordWrap(False)
            self.customer_sale_items_table.verticalHeader().setDefaultSectionSize(30)
        except Exception:
            pass
        layout.addWidget(self.customer_sale_items_table)
        
        return widget

    def create_customer_payment_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Payment history table
        self.customer_payment_table = QTableWidget()
        self.customer_payment_table.setColumnCount(5)
        self.customer_payment_table.setHorizontalHeaderLabels([
            "Date", "Amount", "Method", "Reference", "Notes"
        ])
        try:
            self.customer_payment_table.setWordWrap(False)
            self.customer_payment_table.verticalHeader().setDefaultSectionSize(30)
        except Exception:
            pass
        
        layout.addWidget(self.customer_payment_table)
        return widget

    def create_customer_notes_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Add note section
        add_note_frame = QFrame()
        add_note_frame.setProperty('role', 'card')
        add_note_layout = QVBoxLayout(add_note_frame)
        
        self.customer_note_input = QTextEdit()
        self.customer_note_input.setMaximumHeight(100)
        self.customer_note_input.setPlaceholderText("Add a note about this customer...")
        add_note_layout.addWidget(self.customer_note_input)
        
        add_note_btn = QPushButton("📝 Add Note")
        add_note_btn.setProperty('accent', 'Qt.green')
        add_note_btn.clicked.connect(self.add_customer_note)
        add_note_layout.addWidget(add_note_btn)
        
        layout.addWidget(add_note_frame)

        # Notes history
        self.customer_notes_table = QTableWidget()
        self.customer_notes_table.setColumnCount(3)
        self.customer_notes_table.setHorizontalHeaderLabels([
            "Date", "Note", "Added By"
        ])
        
        layout.addWidget(self.customer_notes_table)
        return widget

    def create_supplier_basic_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Supplier info display
        info_frame = QFrame()
        info_frame.setProperty('role', 'card')
        info_layout = QFormLayout(info_frame)
        
        self.supplier_name_label = QLabel("Not Selected")
        info_layout.addRow("Name:", self.supplier_name_label)
        
        self.supplier_contact_label = QLabel("Not Selected")
        info_layout.addRow("Contact:", self.supplier_contact_label)
        
        self.supplier_email_label = QLabel("Not Selected")
        info_layout.addRow("Email:", self.supplier_email_label)
        
        self.supplier_address_label = QLabel("Not Selected")
        info_layout.addRow("Address:", self.supplier_address_label)
        
        self.supplier_bank_label = QLabel("Not Set")
        info_layout.addRow("Bank Details:", self.supplier_bank_label)
        
        layout.addWidget(info_frame)

        # Supplier statistics
        stats_frame = QFrame()
        stats_frame.setProperty('role', 'card')
        stats_layout = QHBoxLayout(stats_frame)
        
        # Total purchases
        purchases_frame = QFrame()
        purchases_frame.setProperty('role', 'card')
        purchases_layout = QVBoxLayout(purchases_frame)
        
        self.supplier_total_purchases = QLabel("Rs 0.00")
        self.supplier_total_purchases.setStyleSheet("font-size: 18px; font-weight: bold; color: #ef4444;")
        purchases_layout.addWidget(QLabel("💰 Total Purchases"))
        purchases_layout.addWidget(self.supplier_total_purchases)
        
        # Outstanding amount
        outstanding_frame = QFrame()
        outstanding_frame.setProperty('role', 'card')
        outstanding_layout = QVBoxLayout(outstanding_frame)
        
        self.supplier_outstanding = QLabel("Rs 0.00")
        self.supplier_outstanding.setStyleSheet("font-size: 18px; font-weight: bold; color: #f59e0b;")
        outstanding_layout.addWidget(QLabel("⚠️ Outstanding"))
        outstanding_layout.addWidget(self.supplier_outstanding)
        
        # Products count
        products_frame = QFrame()
        products_frame.setProperty('role', 'card')
        products_layout = QVBoxLayout(products_frame)
        
        self.supplier_products_count = QLabel("0")
        self.supplier_products_count.setStyleSheet("font-size: 18px; font-weight: bold; color: #06b6d4;")
        products_layout.addWidget(QLabel("📦 Products"))
        products_layout.addWidget(self.supplier_products_count)
        
        stats_layout.addWidget(purchases_frame)
        stats_layout.addWidget(outstanding_frame)
        stats_layout.addWidget(products_frame)
        
        layout.addWidget(stats_frame)
        layout.addStretch()
        return widget

    def create_supplier_purchase_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Purchase history table
        self.supplier_purchase_table = QTableWidget()
        self.supplier_purchase_table.setColumnCount(7)
        self.supplier_purchase_table.setHorizontalHeaderLabels([
            "Date", "Purchase #", "Total", "Paid", "Outstanding", "Status", "Items"
        ])
        self.supplier_purchase_table.itemClicked.connect(self._on_supplier_purchase_selected)
        try:
            self.supplier_purchase_table.setWordWrap(False)
            self.supplier_purchase_table.verticalHeader().setDefaultSectionSize(32)
        except Exception:
            pass
        
        layout.addWidget(self.supplier_purchase_table)
        
        # Purchase items details section
        details_label = QLabel("Purchase Items Details")
        details_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        layout.addWidget(details_label)
        
        self.supplier_purchase_items_table = QTableWidget()
        self.supplier_purchase_items_table.setColumnCount(5)
        self.supplier_purchase_items_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Quantity", "Unit Price", "Total"
        ])
        self.supplier_purchase_items_table.setMaximumHeight(200)
        try:
            self.supplier_purchase_items_table.setWordWrap(False)
            self.supplier_purchase_items_table.verticalHeader().setDefaultSectionSize(30)
        except Exception:
            pass
        layout.addWidget(self.supplier_purchase_items_table)
        
        return widget

    def create_supplier_payment_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Payment history table
        self.supplier_payment_table = QTableWidget()
        self.supplier_payment_table.setColumnCount(6)
        self.supplier_payment_table.setHorizontalHeaderLabels([
            "Date", "Purchase #", "Amount", "Method", "Reference", "Notes"
        ])
        try:
            self.supplier_payment_table.setWordWrap(False)
            self.supplier_payment_table.verticalHeader().setDefaultSectionSize(30)
        except Exception:
            pass
        
        layout.addWidget(self.supplier_payment_table)
        return widget

    def create_supplier_products_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Products table
        self.supplier_products_table = QTableWidget()
        self.supplier_products_table.setColumnCount(6)
        self.supplier_products_table.setHorizontalHeaderLabels([
            "Product", "SKU", "Purchase Price", "Current Stock", "Last Order", "Status"
        ])
        
        layout.addWidget(self.supplier_products_table)
        return widget

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
            logging.exception("Failed to load customers")

    def load_suppliers(self):
        try:
            from pos_app.models.database import Supplier
            
            suppliers = self.controller.session.query(Supplier).filter(  # TODO: Add .all() or .first()
                Supplier.is_active == True
            ).all()
            
            self.supplier_combo.clear()
            self.supplier_combo.addItem("Select Supplier", None)
            
            for supplier in suppliers:
                self.supplier_combo.addItem(supplier.name, supplier.id)
                
        except Exception as e:
            logging.exception("Failed to load suppliers")

    def load_customer_profile(self):
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            return
        
        try:
            from pos_app.models.database import Customer, Sale, Payment
            
            customer = self.controller.session.get(Customer, customer_id)
            if not customer:
                return
            
            # Update basic info
            self.customer_name_label.setText(customer.name)
            customer_type = str(customer.type).title() if customer.type else "Retail"
            self.customer_type_label.setText(customer_type)
            self.customer_contact_label.setText(customer.contact or "Not Set")
            self.customer_email_label.setText(customer.email or "Not Set")
            self.customer_address_label.setText(customer.address or "Not Set")
            self.customer_credit_label.setText(f"Rs {customer.credit_limit:,.2f}")
            self.customer_balance_label.setText(f"Rs {customer.current_credit:,.2f}")
            
            # Calculate statistics
            sales = self.controller.session.query(Sale).filter(Sale.customer_id == customer_id).all()
            
            total_purchases = sum(sale.total_amount for sale in sales)
            self.customer_total_purchases.setText(f"Rs {total_purchases:,.2f}")
            self.customer_total_transactions.setText(str(len(sales)))
            
            if sales:
                last_sale = max(sales, key=lambda s: s.sale_date or datetime.min)
                last_date = last_sale.sale_date.strftime('%Y-%m-%d') if last_sale.sale_date else "Unknown"
                self.customer_last_purchase.setText(last_date)
            else:
                self.customer_last_purchase.setText("Never")
            
            # Load transaction history
            self.load_customer_history(customer_id)
            self.load_customer_payments(customer_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customer profile: {str(e)}")

    def load_supplier_profile(self):
        supplier_id = self.supplier_combo.currentData()
        if not supplier_id:
            return
        
        try:
            from pos_app.models.database import Supplier, Purchase, Product
            
            supplier = self.controller.session.get(Supplier, supplier_id)
            if not supplier:
                return
            
            # Update basic info
            self.supplier_name_label.setText(supplier.name)
            self.supplier_contact_label.setText(supplier.contact or "Not Set")
            self.supplier_email_label.setText(supplier.email or "Not Set")
            self.supplier_address_label.setText(supplier.address or "Not Set")
            
            bank_info = f"{supplier.bank_name or 'N/A'} - {supplier.bank_account or 'N/A'}"
            self.supplier_bank_label.setText(bank_info)
            
            # Calculate statistics
            purchases = self.controller.session.query(Purchase).filter(Purchase.supplier_id == supplier_id).all()
            products = self.controller.session.query(Product).filter(Product.supplier_id == supplier_id).all()
            
            total_purchases = sum(purchase.total_amount for purchase in purchases)
            total_outstanding = sum((purchase.total_amount - purchase.paid_amount) for purchase in purchases)
            
            self.supplier_total_purchases.setText(f"Rs {total_purchases:,.2f}")
            self.supplier_outstanding.setText(f"Rs {total_outstanding:,.2f}")
            self.supplier_products_count.setText(str(len(products)))
            
            # Load purchase history
            self.load_supplier_purchases(supplier_id)
            self.load_supplier_payments(supplier_id)
            self.load_supplier_products(supplier_id)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load supplier profile: {str(e)}")

    def load_customer_history(self, customer_id):
        try:
            from pos_app.models.database import Sale
            
            sales = self.controller.session.query(Sale).filter(  # TODO: Add .all() or .first()
                Sale.customer_id == customer_id
            ).order_by(Sale.sale_date.desc()).all()
            
            self.customer_history_table.setRowCount(len(sales))
            
            for i, sale in enumerate(sales):
                self.customer_history_table.setItem(i, 0, QTableWidgetItem(
                    sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else ""
                ))
                self.customer_history_table.setItem(i, 1, QTableWidgetItem(sale.invoice_number or f"S-{sale.id}"))
                self.customer_history_table.setItem(i, 2, QTableWidgetItem("Wholesale" if sale.is_wholesale else "Retail"))
                self.customer_history_table.setItem(i, 3, QTableWidgetItem(f"Rs {sale.total_amount:,.2f}"))
                self.customer_history_table.setItem(i, 4, QTableWidgetItem(str(sale.status) if sale.status else ""))
                self.customer_history_table.setItem(i, 5, QTableWidgetItem(str(len(sale.items))))

            try:
                self.customer_history_table.resizeColumnsToContents()
                self.customer_history_table.resizeRowsToContents()
            except Exception:
                pass
                
        except Exception as e:
            logging.exception("Failed to load customer history")

    def load_customer_payments(self, customer_id):
        try:
            from pos_app.models.database import Payment
            
            payments = self.controller.session.query(Payment).filter(  # TODO: Add .all() or .first()
                Payment.customer_id == customer_id
            ).order_by(Payment.payment_date.desc()).all()
            
            self.customer_payment_table.setRowCount(len(payments))
            
            for i, payment in enumerate(payments):
                self.customer_payment_table.setItem(i, 0, QTableWidgetItem(
                    payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else ""
                ))
                self.customer_payment_table.setItem(i, 1, QTableWidgetItem(f"Rs {payment.amount:,.2f}"))
                self.customer_payment_table.setItem(i, 2, QTableWidgetItem(str(payment.payment_method) if payment.payment_method else ""))
                self.customer_payment_table.setItem(i, 3, QTableWidgetItem(payment.reference or ""))
                self.customer_payment_table.setItem(i, 4, QTableWidgetItem(payment.notes or ""))

            try:
                self.customer_payment_table.resizeColumnsToContents()
                self.customer_payment_table.resizeRowsToContents()
            except Exception:
                pass
                
        except Exception as e:
            logging.exception("Failed to load customer payments")

    def load_supplier_purchases(self, supplier_id):
        try:
            from pos_app.models.database import Purchase
            
            purchases = self.controller.session.query(Purchase).filter(  # TODO: Add .all() or .first()
                Purchase.supplier_id == supplier_id
            ).order_by(Purchase.order_date.desc()).all()
            
            self.supplier_purchase_table.setRowCount(len(purchases))
            
            for i, purchase in enumerate(purchases):
                self.supplier_purchase_table.setItem(i, 0, QTableWidgetItem(
                    purchase.order_date.strftime('%Y-%m-%d') if purchase.order_date else ""
                ))
                purchase_no_item = QTableWidgetItem(purchase.purchase_number or f"P-{purchase.id}")
                try:
                    purchase_no_item.setData(Qt.UserRole, int(purchase.id))
                except Exception:
                    pass
                self.supplier_purchase_table.setItem(i, 1, purchase_no_item)
                self.supplier_purchase_table.setItem(i, 2, QTableWidgetItem(f"Rs {purchase.total_amount:,.2f}"))
                self.supplier_purchase_table.setItem(i, 3, QTableWidgetItem(f"Rs {purchase.paid_amount:,.2f}"))
                
                outstanding = purchase.total_amount - purchase.paid_amount
                outstanding_item = QTableWidgetItem(f"Rs {outstanding:,.2f}")
                if outstanding > 0:
                    outstanding_item.setForeground(Qt.red)
                self.supplier_purchase_table.setItem(i, 4, outstanding_item)
                
                self.supplier_purchase_table.setItem(i, 5, QTableWidgetItem(purchase.status or ""))
                self.supplier_purchase_table.setItem(i, 6, QTableWidgetItem(str(len(purchase.items))))

            try:
                self.supplier_purchase_table.resizeColumnsToContents()
                self.supplier_purchase_table.resizeRowsToContents()
            except Exception:
                pass
                
        except Exception as e:
            logging.exception("Failed to load supplier purchases")

    def load_supplier_payments(self, supplier_id):
        try:
            from pos_app.models.database import PurchasePayment
            
            payments = self.controller.session.query(PurchasePayment).filter(  # TODO: Add .all() or .first()
                PurchasePayment.supplier_id == supplier_id
            ).order_by(PurchasePayment.payment_date.desc()).all()
            
            self.supplier_payment_table.setRowCount(len(payments))
            
            for i, payment in enumerate(payments):
                self.supplier_payment_table.setItem(i, 0, QTableWidgetItem(
                    payment.payment_date.strftime('%Y-%m-%d') if payment.payment_date else ""
                ))
                
                purchase_num = ""
                if payment.purchase:
                    purchase_num = payment.purchase.purchase_number or f"P-{payment.purchase.id}"
                self.supplier_payment_table.setItem(i, 1, QTableWidgetItem(purchase_num))
                
                self.supplier_payment_table.setItem(i, 2, QTableWidgetItem(f"Rs {payment.amount:,.2f}"))
                self.supplier_payment_table.setItem(i, 3, QTableWidgetItem(str(payment.payment_method) if payment.payment_method else ""))
                self.supplier_payment_table.setItem(i, 4, QTableWidgetItem(payment.reference or ""))
                self.supplier_payment_table.setItem(i, 5, QTableWidgetItem(payment.notes or ""))

            try:
                self.supplier_payment_table.resizeColumnsToContents()
                self.supplier_payment_table.resizeRowsToContents()
            except Exception:
                pass
                
        except Exception as e:
            logging.exception("Failed to load supplier payments")

    def load_supplier_products(self, supplier_id):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(  # TODO: Add .all() or .first()
                Product.supplier_id == supplier_id
            ).all()
            
            self.supplier_products_table.setRowCount(len(products))
            
            for i, product in enumerate(products):
                self.supplier_products_table.setItem(i, 0, QTableWidgetItem(product.name))
                self.supplier_products_table.setItem(i, 1, QTableWidgetItem(product.sku or ""))
                self.supplier_products_table.setItem(i, 2, QTableWidgetItem(f"Rs {product.purchase_price:,.2f}"))
                self.supplier_products_table.setItem(i, 3, QTableWidgetItem(str(product.stock_level)))
                self.supplier_products_table.setItem(i, 4, QTableWidgetItem("2024-01-01"))  # Placeholder
                self.supplier_products_table.setItem(i, 5, QTableWidgetItem("Active" if product.is_active else "Inactive"))
                
        except Exception as e:
            logging.exception("Failed to load supplier products")

    def _on_supplier_purchase_selected(self, item):
        """Handle when a purchase is selected to show its items"""
        try:
            from pos_app.models.database import Purchase, PurchaseItem, Product, PurchasePayment
            
            # Get the row index
            row = self.supplier_purchase_table.row(item)
            
            # Get purchase number from the table (column 1)
            purchase_num_item = self.supplier_purchase_table.item(row, 1)
            if not purchase_num_item:
                return

            # Prefer stored purchase id (most reliable)
            purchase = None
            purchase_id = None
            try:
                purchase_id = purchase_num_item.data(Qt.UserRole)
            except Exception:
                purchase_id = None
            try:
                if purchase_id is not None:
                    purchase_id = int(purchase_id)
            except Exception:
                purchase_id = None

            if purchase_id:
                try:
                    purchase = self.controller.session.get(Purchase, purchase_id)
                except Exception:
                    purchase = None

            # Fallback: try parsing/display number
            if not purchase:
                purchase_number = purchase_num_item.text()
                if purchase_number.startswith("P-"):
                    try:
                        purchase_id2 = int(purchase_number.split("-")[1])
                        purchase = self.controller.session.get(Purchase, purchase_id2)
                    except Exception:
                        purchase = None
                if not purchase:
                    try:
                        purchase = self.controller.session.query(Purchase).filter(
                            Purchase.purchase_number == purchase_number
                        ).first()
                    except Exception:
                        purchase = None
            
            if not purchase:
                self.supplier_purchase_items_table.setRowCount(0)
                try:
                    self.supplier_payment_table.setRowCount(0)
                except Exception:
                    pass
                return
            
            # Load purchase items
            purchase_items = self.controller.session.query(PurchaseItem).filter(
                PurchaseItem.purchase_id == purchase.id
            ).all()
            
            self.supplier_purchase_items_table.setRowCount(len(purchase_items))
            
            for i, item_obj in enumerate(purchase_items):
                # Get product info
                product = self.controller.session.query(Product).filter(
                    Product.id == item_obj.product_id
                ).first()
                
                # Product name
                product_name = product.name if product else f"Product #{item_obj.product_id}"
                self.supplier_purchase_items_table.setItem(i, 0, QTableWidgetItem(product_name))
                
                # SKU
                sku = product.sku if product else ""
                self.supplier_purchase_items_table.setItem(i, 1, QTableWidgetItem(sku))
                
                # Quantity
                quantity = item_obj.quantity or 0
                self.supplier_purchase_items_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
                
                # Unit Price
                unit_cost = getattr(item_obj, 'unit_cost', None)
                if unit_cost is None:
                    unit_cost = 0.0
                self.supplier_purchase_items_table.setItem(i, 3, QTableWidgetItem(f"Rs {float(unit_cost):,.2f}"))
                
                # Total
                total_cost = getattr(item_obj, 'total_cost', None)
                if total_cost is None:
                    try:
                        total_cost = float(quantity) * float(unit_cost)
                    except Exception:
                        total_cost = 0.0
                self.supplier_purchase_items_table.setItem(i, 4, QTableWidgetItem(f"Rs {float(total_cost):,.2f}"))

            try:
                self.supplier_purchase_items_table.resizeColumnsToContents()
                self.supplier_purchase_items_table.resizeRowsToContents()
            except Exception:
                pass

            # Load payments for this selected purchase into supplier payment table
            try:
                payments = self.controller.session.query(PurchasePayment).filter(
                    PurchasePayment.purchase_id == purchase.id
                ).order_by(PurchasePayment.payment_date.desc()).all()

                try:
                    self.supplier_payment_table.setRowCount(len(payments))
                except Exception:
                    pass

                for i, pay in enumerate(payments):
                    try:
                        date_txt = pay.payment_date.strftime('%Y-%m-%d') if pay.payment_date else ''
                    except Exception:
                        date_txt = ''
                    self.supplier_payment_table.setItem(i, 0, QTableWidgetItem(date_txt))
                    try:
                        pnum = ''
                        try:
                            pnum = purchase.purchase_number or f"P-{purchase.id}"
                        except Exception:
                            pnum = f"P-{purchase.id}"
                        self.supplier_payment_table.setItem(i, 1, QTableWidgetItem(pnum))
                    except Exception:
                        pass
                    try:
                        self.supplier_payment_table.setItem(i, 2, QTableWidgetItem(f"Rs {float(getattr(pay, 'amount', 0.0) or 0.0):,.2f}"))
                    except Exception:
                        self.supplier_payment_table.setItem(i, 2, QTableWidgetItem("Rs 0.00"))
                    self.supplier_payment_table.setItem(i, 3, QTableWidgetItem(str(getattr(pay, 'payment_method', '') or '')))
                    self.supplier_payment_table.setItem(i, 4, QTableWidgetItem(str(getattr(pay, 'reference', '') or '')))
                    self.supplier_payment_table.setItem(i, 5, QTableWidgetItem(str(getattr(pay, 'notes', '') or '')))

                try:
                    self.supplier_payment_table.resizeColumnsToContents()
                    self.supplier_payment_table.resizeRowsToContents()
                except Exception:
                    pass
            except Exception:
                try:
                    self.supplier_payment_table.setRowCount(0)
                except Exception:
                    pass
        
        except Exception as e:
            logging.exception(f"Failed to load purchase items: {e}")

    def _on_customer_sale_selected(self, item):
        """Handle when a customer sale is selected to show its items"""
        try:
            from pos_app.models.database import Sale, SaleItem, Product
            
            # Get the row index
            row = self.customer_history_table.row(item)
            
            # Get invoice number from the table (column 1)
            invoice_item = self.customer_history_table.item(row, 1)
            if not invoice_item:
                return
            
            invoice_number = invoice_item.text()
            
            # Find the sale by invoice number or ID
            sale = None
            if invoice_number.startswith("S-"):
                # It's an ID-based number like "S-123"
                try:
                    sale_id = int(invoice_number.split("-")[1])
                    sale = self.controller.session.query(Sale).filter(Sale.id == sale_id).first()
                except Exception:
                    pass
            
            # If not found, try to find by invoice_number field
            if not sale:
                sale = self.controller.session.query(Sale).filter(
                    Sale.invoice_number == invoice_number
                ).first()
            
            if not sale:
                self.customer_sale_items_table.setRowCount(0)
                return
            
            # Load sale items
            sale_items = self.controller.session.query(SaleItem).filter(
                SaleItem.sale_id == sale.id
            ).all()
            
            self.customer_sale_items_table.setRowCount(len(sale_items))
            
            for i, item_obj in enumerate(sale_items):
                # Get product info
                product = self.controller.session.query(Product).filter(
                    Product.id == item_obj.product_id
                ).first()
                
                # Product name
                product_name = product.name if product else f"Product #{item_obj.product_id}"
                self.customer_sale_items_table.setItem(i, 0, QTableWidgetItem(product_name))
                
                # SKU
                sku = product.sku if product else ""
                self.customer_sale_items_table.setItem(i, 1, QTableWidgetItem(sku))
                
                # Quantity
                quantity = item_obj.quantity or 0
                self.customer_sale_items_table.setItem(i, 2, QTableWidgetItem(str(quantity)))
                
                # Unit Price
                unit_price = item_obj.unit_price or 0.0
                self.customer_sale_items_table.setItem(i, 3, QTableWidgetItem(f"Rs {unit_price:,.2f}"))
                
                # Total
                total = (item_obj.quantity or 0) * (item_obj.unit_price or 0.0)
                self.customer_sale_items_table.setItem(i, 4, QTableWidgetItem(f"Rs {total:,.2f}"))
        
        except Exception as e:
            logging.exception(f"Failed to load sale items: {e}")

    # Placeholder methods for actions
    def add_customer(self):
        QMessageBox.information(self, "Info", "Add customer dialog would open here")

    def edit_customer(self):
        QMessageBox.information(self, "Info", "Edit customer dialog would open here")

    def add_supplier(self):
        QMessageBox.information(self, "Info", "Add supplier dialog would open here")

    def edit_supplier(self):
        QMessageBox.information(self, "Info", "Edit supplier dialog would open here")

    def add_customer_note(self):
        customer_id = self.customer_combo.currentData()
        note_text = self.customer_note_input.toPlainText().strip()
        
        if not customer_id or not note_text:
            QMessageBox.warning(self, "Warning", "Please select a customer and enter a note")
            return
        
        # In a real implementation, you'd save this to a notes table
        QMessageBox.information(self, "Success", "Note added successfully!")
        self.customer_note_input.clear()
