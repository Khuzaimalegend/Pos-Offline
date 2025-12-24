try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
        QTabWidget, QFrame, QMessageBox, QDateEdit, QSpinBox,
        QListWidget, QListWidgetItem, QCompleter
    )
    from PySide6.QtCore import Qt, QDate, QTimer, QStringListModel, QRect
    from PySide6.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QLineEdit, QTableWidget, QTableWidgetItem, QComboBox,
        QTabWidget, QFrame, QMessageBox, QDateEdit, QSpinBox,
        QListWidget, QListWidgetItem, QCompleter
    )
    from PyQt6.QtCore import Qt, QDate, QTimer, QStringListModel, QRect
    from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
import logging

app_logger = logging.getLogger(__name__)

class UniversalSearchWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        self.setup_ui()
        # Add test data if database is empty
        self.add_test_data_if_needed()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Simple Header
        header = QLabel("🔍 Search")
        header.setStyleSheet("""
            font-size: 32px; 
            font-weight: bold; 
            color: #3b82f6; 
            padding: 15px 0;
            text-align: center;
        """)
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # Clean Search Bar with Suggestions
        search_container = QFrame()
        search_container.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 15px;
                padding: 20px;
                border: 2px solid #334155;
            }
        """)
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)  # No spacing for seamless connection

        # Search input row
        input_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search anything...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 15px 20px;
                border: 2px solid #475569;
                border-radius: 10px 10px 0 0;
                background: #334155;
                color: #e2e8f0;
                font-size: 16px;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background: #475569;
            }
        """)
        self.search_input.textChanged.connect(self.on_search_changed)

        # Add autocomplete suggestions
        self.suggestions_list = QListWidget()
        self.suggestions_list.setMaximumHeight(150)
        self.suggestions_list.setStyleSheet("""
            QListWidget {
                background: #334155;
                border: 2px solid #475569;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 14px;
                outline: none;
                border-top: none;
                border-top-left-radius: 0;
                border-top-right-radius: 0;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #475569;
            }
            QListWidget::item:selected {
                background: #3b82f6;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background: #475569;
            }
        """)
        self.suggestions_list.setVisible(False)
        self.suggestions_list.itemDoubleClicked.connect(self.select_suggestion)

        # Position suggestions below search input
        self.search_input.textChanged.connect(self.update_suggestions)

        self.search_type = QComboBox()
        self.search_type.addItems(["All", "Products", "Customers", "Suppliers"])
        self.search_type.setStyleSheet("""
            QComboBox {
                padding: 15px;
                border: 2px solid #475569;
                border-radius: 10px;
                background: #334155;
                color: #e2e8f0;
                font-size: 16px;
                min-width: 120px;
            }
            QComboBox:hover {
                border-color: #3b82f6;
            }
        """)
        self.search_type.currentTextChanged.connect(self.on_search_changed)

        search_btn = QPushButton("🔍 Search")
        search_btn.setMinimumHeight(40)
        search_btn.clicked.connect(self.perform_search)

        # Add widgets to input row
        input_row.addWidget(self.search_input, 4)
        input_row.addWidget(self.search_type, 1)
        input_row.addWidget(search_btn)

        search_layout.addLayout(input_row)

        # Add suggestions list below search input
        search_layout.addWidget(self.suggestions_list)

        # Advanced filters
        filters_layout = QHBoxLayout()
        
        # Date range
        filters_layout.addWidget(QLabel("From:"))
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        filters_layout.addWidget(self.date_from)
        
        filters_layout.addWidget(QLabel("To:"))
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        filters_layout.addWidget(self.date_to)
        
        # Amount range
        filters_layout.addWidget(QLabel("Min Amount:"))
        self.min_amount = QSpinBox()
        self.min_amount.setRange(0, 1000000)
        self.min_amount.setSuffix(" Rs")
        filters_layout.addWidget(self.min_amount)
        
        filters_layout.addWidget(QLabel("Max Amount:"))
        self.max_amount = QSpinBox()
        self.max_amount.setRange(0, 1000000)
        self.max_amount.setValue(100000)
        self.max_amount.setSuffix(" Rs")
        filters_layout.addWidget(self.max_amount)
        
        filters_layout.addStretch()
        
        clear_btn = QPushButton("Clear Filters")
        clear_btn.clicked.connect(self.clear_filters)
        filters_layout.addWidget(clear_btn)
        
        search_layout.addLayout(filters_layout)
        # Remove the incorrect search_frame reference - search_container is already added above
        # layout.addWidget(search_frame)  # <-- This line was causing the error

        # Results tabs
        self.results_tabs = QTabWidget()
        
        # All Results tab
        self.all_results_table = self.create_results_table([
            "Type", "ID", "Name/Description", "Date", "Amount", "Status", "Actions"
        ])
        self.results_tabs.addTab(self.all_results_table, "All Results")
        
        # Specific result tabs
        self.customers_table = self.create_results_table([
            "ID", "Name", "Type", "Contact", "Credit Limit", "Balance", "Actions"
        ])
        self.results_tabs.addTab(self.customers_table, "Customers")
        
        self.suppliers_table = self.create_results_table([
            "ID", "Name", "Contact", "Email", "Outstanding", "Actions"
        ])
        self.results_tabs.addTab(self.suppliers_table, "Suppliers")
        
        self.products_table = self.create_results_table([
            "ID", "Name", "SKU", "Price", "Stock", "Supplier", "Actions"
        ])
        self.results_tabs.addTab(self.products_table, "Products")
        
        self.sales_table = self.create_results_table([
            "ID", "Date", "Customer", "Total", "Paid", "Status", "Actions"
        ])
        self.results_tabs.addTab(self.sales_table, "Sales")
        
        self.purchases_table = self.create_results_table([
            "ID", "Date", "Supplier", "Total", "Paid", "Status", "Actions"
        ])
        self.results_tabs.addTab(self.purchases_table, "Purchases")
        
        layout.addWidget(self.results_tabs)

        # Results summary
        self.results_summary = QLabel("Ready to search...")
        self.results_summary.setStyleSheet("font-size: 14px; color: #9ca3af; padding: 10px;")
        layout.addWidget(self.results_summary)

    def create_results_table(self, headers):
        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        return table

    def update_suggestions(self):
        """Update autocomplete suggestions based on search input"""
        query = self.search_input.text().strip().lower()

        if not query or len(query) < 1:
            self.suggestions_list.setVisible(False)
            return

        try:
            suggestions = []

            # Get suggestions based on search type
            search_type = self.search_type.currentText()

            if search_type in ["All", "Products"]:
                from pos_app.models.database import Product
                try:
                    products = self.controller.session.query(Product).filter(
                        (Product.name.ilike(f'%{query}%')) |
                        (Product.sku.ilike(f'%{query}%'))
                    ).limit(5).all()
                    for product in products:
                        suggestions.append(f"Product: {product.name} ({product.sku or 'No SKU'})")
                except Exception as e:
                    pass  # Silently handle errors

            if search_type in ["All", "Customers"]:
                from pos_app.models.database import Customer
                try:
                    customers = self.controller.session.query(Customer).filter(
                        (Customer.name.ilike(f'%{query}%')) |
                        (Customer.business_name.ilike(f'%{query}%'))
                    ).limit(5).all()
                    for customer in customers:
                        suggestions.append(f"Customer: {customer.name}")
                except Exception as e:
                    pass  # Silently handle errors

            if search_type in ["All", "Suppliers"]:
                from pos_app.models.database import Supplier
                try:
                    suppliers = self.controller.session.query(Supplier).filter(
                        (Supplier.name.ilike(f'%{query}%')) |
                        (Supplier.business_name.ilike(f'%{query}%'))
                    ).limit(5).all()
                    for supplier in suppliers:
                        suggestions.append(f"Supplier: {supplier.name}")
                except Exception as e:
                    pass  # Silently handle errors

            # Update suggestions list
            self.suggestions_list.clear()
            if suggestions:
                for suggestion in suggestions[:5]:
                    item = QListWidgetItem(suggestion)
                    self.suggestions_list.addItem(item)

                self.suggestions_list.setVisible(True)
            else:
                self.suggestions_list.setVisible(False)

        except Exception as e:
            print(f"Search suggestions error: {e}")
            self.suggestions_list.setVisible(False)

    def select_suggestion(self, item):
        """Handle suggestion selection"""
        if item:
            suggestion_text = item.text()
            # Extract the actual search term from suggestion
            if ":" in suggestion_text:
                search_term = suggestion_text.split(": ", 1)[1]
                if "(" in search_term and ")" in search_term:
                    # For products: "Product Name (SKU)" -> "Product Name"
                    search_term = search_term.split(" (")[0]
                self.search_input.setText(search_term)
            else:
                self.search_input.setText(suggestion_text)

            self.suggestions_list.setVisible(False)
            self.perform_search()

    def on_search_changed(self):
        # Debounced search - wait 500ms after user stops typing
        self.search_timer.stop()
        if self.search_input.text().strip():
            self.search_timer.start(500)

    def perform_search(self):
        try:
            query = self.search_input.text().strip()
            search_type = self.search_type.currentText()

            if not query and search_type == "All":
                self.results_summary.setText("Enter a search term to begin...")
                return

            # Clear previous results
            self.clear_results()

            results_count = 0
            print(f"Performing search for '{query}' in {search_type}")

            if search_type in ["All", "Customers"]:
                results_count += self.search_customers(query)

            if search_type in ["All", "Suppliers"]:
                results_count += self.search_suppliers(query)

            if search_type in ["All", "Products"]:
                results_count += self.search_products(query)

            if search_type in ["All", "Sales"]:
                results_count += self.search_sales(query)

            if search_type in ["All", "Purchases"]:
                results_count += self.search_purchases(query)

            print(f"Search completed. Found {results_count} results")
            self.results_summary.setText(f"Found {results_count} results for '{query}'")

        except Exception as e:
            print(f"Search failed: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Search Error", f"Search failed: {str(e)}")

    def search_customers(self, query):
        try:
            from pos_app.models.database import Customer
            customers = self.controller.session.query(Customer).filter(
                (Customer.name.ilike(f'%{query}%')) |
                (Customer.contact.ilike(f'%{query}%')) |
                (Customer.email.ilike(f'%{query}%')) |
                (Customer.business_name.ilike(f'%{query}%'))
            ).all()
            
            # Populate customers table
            self.customers_table.setRowCount(len(customers))
            for i, customer in enumerate(customers):
                self.customers_table.setItem(i, 0, QTableWidgetItem(str(customer.id)))
                self.customers_table.setItem(i, 1, QTableWidgetItem(customer.name or ""))
                self.customers_table.setItem(i, 2, QTableWidgetItem(str(customer.type) if customer.type else ""))
                self.customers_table.setItem(i, 3, QTableWidgetItem(customer.contact or ""))
                self.customers_table.setItem(i, 4, QTableWidgetItem(f"Rs {customer.credit_limit:,.2f}"))
                self.customers_table.setItem(i, 5, QTableWidgetItem(f"Rs {customer.current_credit:,.2f}"))
                
                # Add to all results
                all_row = self.all_results_table.rowCount()
                self.all_results_table.insertRow(all_row)
                self.all_results_table.setItem(all_row, 0, QTableWidgetItem("Customer"))
                self.all_results_table.setItem(all_row, 1, QTableWidgetItem(str(customer.id)))
                self.all_results_table.setItem(all_row, 2, QTableWidgetItem(customer.name or ""))
                self.all_results_table.setItem(all_row, 3, QTableWidgetItem(customer.created_at.strftime('%Y-%m-%d') if customer.created_at else ""))
                self.all_results_table.setItem(all_row, 4, QTableWidgetItem(f"Rs {customer.current_credit:,.2f}"))
                self.all_results_table.setItem(all_row, 5, QTableWidgetItem("Active" if customer.is_active else "Inactive"))
            
            return len(customers)
        except Exception as e:
            app_logger.exception("Customer search failed")
            return 0

    def search_suppliers(self, query):
        try:
            from pos_app.models.database import Supplier
            suppliers = self.controller.session.query(Supplier).filter(
                (Supplier.name.ilike(f'%{query}%')) |
                (Supplier.contact.ilike(f'%{query}%')) |
                (Supplier.email.ilike(f'%{query}%')) |
                (Supplier.business_name.ilike(f'%{query}%'))
            ).all()
            
            # Populate suppliers table
            self.suppliers_table.setRowCount(len(suppliers))
            for i, supplier in enumerate(suppliers):
                self.suppliers_table.setItem(i, 0, QTableWidgetItem(str(supplier.id)))
                self.suppliers_table.setItem(i, 1, QTableWidgetItem(supplier.name or ""))
                self.suppliers_table.setItem(i, 2, QTableWidgetItem(supplier.contact or ""))
                self.suppliers_table.setItem(i, 3, QTableWidgetItem(supplier.email or ""))
                
                # Calculate outstanding amount
                outstanding = self.calculate_supplier_outstanding(supplier.id)
                self.suppliers_table.setItem(i, 4, QTableWidgetItem(f"Rs {outstanding:,.2f}"))
                
                # Add to all results
                all_row = self.all_results_table.rowCount()
                self.all_results_table.insertRow(all_row)
                self.all_results_table.setItem(all_row, 0, QTableWidgetItem("Supplier"))
                self.all_results_table.setItem(all_row, 1, QTableWidgetItem(str(supplier.id)))
                self.all_results_table.setItem(all_row, 2, QTableWidgetItem(supplier.name or ""))
                self.all_results_table.setItem(all_row, 3, QTableWidgetItem(supplier.created_at.strftime('%Y-%m-%d') if supplier.created_at else ""))
                self.all_results_table.setItem(all_row, 4, QTableWidgetItem(f"Rs {outstanding:,.2f}"))
                self.all_results_table.setItem(all_row, 5, QTableWidgetItem("Active" if supplier.is_active else "Inactive"))
            
            return len(suppliers)
        except Exception as e:
            app_logger.exception("Supplier search failed")
            return 0

    def search_products(self, query):
        try:
            from pos_app.models.database import Product
            products = self.controller.session.query(Product).filter(
                (Product.name.ilike(f'%{query}%')) |
                (Product.sku.ilike(f'%{query}%')) |
                (Product.barcode.ilike(f'%{query}%')) |
                (Product.description.ilike(f'%{query}%'))
            ).all()
            
            # Populate products table
            self.products_table.setRowCount(len(products))
            for i, product in enumerate(products):
                self.products_table.setItem(i, 0, QTableWidgetItem(str(product.id)))
                self.products_table.setItem(i, 1, QTableWidgetItem(product.name or ""))
                self.products_table.setItem(i, 2, QTableWidgetItem(product.sku or ""))
                self.products_table.setItem(i, 3, QTableWidgetItem(f"Rs {product.retail_price:,.2f}"))
                self.products_table.setItem(i, 4, QTableWidgetItem(str(product.stock_level)))
                
                supplier_name = ""
                if product.supplier:
                    supplier_name = product.supplier.name
                self.products_table.setItem(i, 5, QTableWidgetItem(supplier_name))
                
                # Add to all results
                all_row = self.all_results_table.rowCount()
                self.all_results_table.insertRow(all_row)
                self.all_results_table.setItem(all_row, 0, QTableWidgetItem("Product"))
                self.all_results_table.setItem(all_row, 1, QTableWidgetItem(str(product.id)))
                self.all_results_table.setItem(all_row, 2, QTableWidgetItem(product.name or ""))
                self.all_results_table.setItem(all_row, 3, QTableWidgetItem(product.created_at.strftime('%Y-%m-%d') if product.created_at else ""))
                self.all_results_table.setItem(all_row, 4, QTableWidgetItem(f"Rs {product.retail_price:,.2f}"))
                self.all_results_table.setItem(all_row, 5, QTableWidgetItem("Active" if product.is_active else "Inactive"))
            
            return len(products)
        except Exception as e:
            app_logger.exception("Product search failed")
            return 0

    def search_sales(self, query):
        try:
            from pos_app.models.database import Sale, Customer
            sales = self.controller.session.query(Sale).join(Customer, isouter=True).filter(
                (Sale.invoice_number.ilike(f'%{query}%')) |
                (Customer.name.ilike(f'%{query}%'))
            ).all()
            
            # Apply date and amount filters (PySide6/PyQt6 compatible)
            try:
                date_from = self.date_from.date().toPython()
                date_to = self.date_to.date().toPython()
            except AttributeError:
                date_from = self.date_from.date().toPyDate()
                date_to = self.date_to.date().toPyDate()
            min_amt = self.min_amount.value()
            max_amt = self.max_amount.value()
            
            filtered_sales = []
            for sale in sales:
                if sale.sale_date:
                    sale_date = sale.sale_date.date()
                    if date_from <= sale_date <= date_to:
                        if min_amt <= (sale.total_amount or 0) <= max_amt:
                            filtered_sales.append(sale)
            
            # Populate sales table
            self.sales_table.setRowCount(len(filtered_sales))
            for i, sale in enumerate(filtered_sales):
                self.sales_table.setItem(i, 0, QTableWidgetItem(str(sale.id)))
                self.sales_table.setItem(i, 1, QTableWidgetItem(sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else ""))
                
                customer_name = ""
                if sale.customer:
                    customer_name = sale.customer.name
                self.sales_table.setItem(i, 2, QTableWidgetItem(customer_name))
                
                self.sales_table.setItem(i, 3, QTableWidgetItem(f"Rs {sale.total_amount:,.2f}"))
                self.sales_table.setItem(i, 4, QTableWidgetItem(f"Rs {sale.paid_amount:,.2f}"))
                self.sales_table.setItem(i, 5, QTableWidgetItem(str(sale.status) if sale.status else ""))
                
                # Add to all results
                all_row = self.all_results_table.rowCount()
                self.all_results_table.insertRow(all_row)
                self.all_results_table.setItem(all_row, 0, QTableWidgetItem("Sale"))
                self.all_results_table.setItem(all_row, 1, QTableWidgetItem(str(sale.id)))
                self.all_results_table.setItem(all_row, 2, QTableWidgetItem(f"Sale to {customer_name}"))
                self.all_results_table.setItem(all_row, 3, QTableWidgetItem(sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else ""))
                self.all_results_table.setItem(all_row, 4, QTableWidgetItem(f"Rs {sale.total_amount:,.2f}"))
                self.all_results_table.setItem(all_row, 5, QTableWidgetItem(str(sale.status) if sale.status else ""))
            
            return len(filtered_sales)
        except Exception as e:
            app_logger.exception("Sales search failed")
            return 0

    def search_purchases(self, query):
        try:
            from pos_app.models.database import Purchase, Supplier
            purchases = self.controller.session.query(Purchase).join(Supplier, isouter=True).filter(
                (Purchase.purchase_number.ilike(f'%{query}%')) |
                (Supplier.name.ilike(f'%{query}%'))
            ).all()
            
            # Apply date and amount filters
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()
            min_amt = self.min_amount.value()
            max_amt = self.max_amount.value()
            
            filtered_purchases = []
            for purchase in purchases:
                if purchase.order_date:
                    purchase_date = purchase.order_date.date()
                    if date_from <= purchase_date <= date_to:
                        if min_amt <= (purchase.total_amount or 0) <= max_amt:
                            filtered_purchases.append(purchase)
            
            # Populate purchases table
            self.purchases_table.setRowCount(len(filtered_purchases))
            for i, purchase in enumerate(filtered_purchases):
                self.purchases_table.setItem(i, 0, QTableWidgetItem(str(purchase.id)))
                self.purchases_table.setItem(i, 1, QTableWidgetItem(purchase.order_date.strftime('%Y-%m-%d') if purchase.order_date else ""))
                
                supplier_name = ""
                if purchase.supplier:
                    supplier_name = purchase.supplier.name
                self.purchases_table.setItem(i, 2, QTableWidgetItem(supplier_name))
                
                self.purchases_table.setItem(i, 3, QTableWidgetItem(f"Rs {purchase.total_amount:,.2f}"))
                self.purchases_table.setItem(i, 4, QTableWidgetItem(f"Rs {purchase.paid_amount:,.2f}"))
                self.purchases_table.setItem(i, 5, QTableWidgetItem(purchase.status or ""))
                
                # Add to all results
                all_row = self.all_results_table.rowCount()
                self.all_results_table.insertRow(all_row)
                self.all_results_table.setItem(all_row, 0, QTableWidgetItem("Purchase"))
                self.all_results_table.setItem(all_row, 1, QTableWidgetItem(str(purchase.id)))
                self.all_results_table.setItem(all_row, 2, QTableWidgetItem(f"Purchase from {supplier_name}"))
                self.all_results_table.setItem(all_row, 3, QTableWidgetItem(purchase.order_date.strftime('%Y-%m-%d') if purchase.order_date else ""))
                self.all_results_table.setItem(all_row, 4, QTableWidgetItem(f"Rs {purchase.total_amount:,.2f}"))
                self.all_results_table.setItem(all_row, 5, QTableWidgetItem(purchase.status or ""))
            
            return len(filtered_purchases)
        except Exception as e:
            app_logger.exception("Purchases search failed")
            return 0

    def calculate_supplier_outstanding(self, supplier_id):
        try:
            from pos_app.models.database import Purchase
            purchases = self.controller.session.query(Purchase).filter(
                Purchase.supplier_id == supplier_id
            ).all()
            
            total_outstanding = 0
            for purchase in purchases:
                outstanding = (purchase.total_amount or 0) - (purchase.paid_amount or 0)
                if outstanding > 0:
                    total_outstanding += outstanding
            
            return total_outstanding
        except Exception:
            return 0

    def clear_results(self):
        self.all_results_table.setRowCount(0)
        self.customers_table.setRowCount(0)
        self.suppliers_table.setRowCount(0)
        self.products_table.setRowCount(0)
        self.sales_table.setRowCount(0)
        self.purchases_table.setRowCount(0)

    def clear_filters(self):
        self.search_input.clear()
        self.search_type.setCurrentText("All")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_to.setDate(QDate.currentDate())
        self.min_amount.setValue(0)
        self.max_amount.setValue(100000)
        self.clear_results()
        self.results_summary.setText("Filters cleared. Ready to search...")

    def add_test_data_if_needed(self):
        """Add sample data if database is empty for testing"""
        try:
            from pos_app.models.database import Product, Customer, Supplier

            # Check if we have data
            existing_products = self.controller.session.query(Product).count()
            existing_customers = self.controller.session.query(Customer).count()
            existing_suppliers = self.controller.session.query(Supplier).count()

            # Data counts checked for demo setup

            if existing_products == 0:
                # Add sample products
                sample_products = [
                    Product(name="Laptop Dell", sku="LT001", retail_price=50000, wholesale_price=45000, stock_level=10),
                    Product(name="iPhone 15", sku="PH001", retail_price=80000, wholesale_price=75000, stock_level=5),
                    Product(name="Samsung TV", sku="TV001", retail_price=35000, wholesale_price=32000, stock_level=8),
                ]
                for product in sample_products:
                    self.controller.session.add(product)
                print("Added sample products to search widget")

            if existing_customers == 0:
                # Add sample customers
                sample_customers = [
                    Customer(name="John Doe", contact="9876543210", email="john@example.com", credit_limit=50000),
                    Customer(name="Jane Smith", contact="9876543211", email="jane@example.com", credit_limit=75000),
                ]
                for customer in sample_customers:
                    self.controller.session.add(customer)
                print("Added sample customers to search widget")

            if existing_suppliers == 0:
                # Add sample suppliers
                sample_suppliers = [
                    Supplier(name="Tech Distributors", contact="9876543214", email="info@techdist.com"),
                    Supplier(name="Electronics Hub", contact="9876543215", email="sales@electrohub.com"),
                ]
                for supplier in sample_suppliers:
                    self.controller.session.add(supplier)
                print("Added sample suppliers to search widget")

            self.controller.session.commit()
            print("Test data setup complete in search widget")

        except Exception as e:
            print(f"Error setting up test data in search widget: {e}")
            self.controller.session.rollback()
