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

class CustomerReportsWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("📊 Customer Reports & Analytics")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        
        # Individual Customer Report
        individual_tab = self.create_individual_report_tab()
        tabs.addTab(individual_tab, "👤 Individual Report")
        
        # Customer Summary
        summary_tab = self.create_customer_summary_tab()
        tabs.addTab(summary_tab, "📋 Customer Summary")
        
        # Sales Analytics
        analytics_tab = self.create_sales_analytics_tab()
        tabs.addTab(analytics_tab, "📈 Sales Analytics")
        
        # Customer Comparison
        comparison_tab = self.create_customer_comparison_tab()
        tabs.addTab(comparison_tab, "⚖️ Customer Comparison")
        
        layout.addWidget(tabs)

    def create_individual_report_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Customer selection and filters
        controls_frame = QFrame()
        controls_frame.setProperty('role', 'card')
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("Customer:"))
        self.customer_combo = QComboBox()
        self.load_customers()
        self.customer_combo.currentIndexChanged.connect(self.generate_individual_report)
        controls_layout.addWidget(self.customer_combo)
        
        controls_layout.addWidget(QLabel("Period:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "Last 30 Days", "Last 3 Months", "Last 6 Months", 
            "Last Year", "All Time", "Custom Range"
        ])
        self.period_combo.currentTextChanged.connect(self.generate_individual_report)
        controls_layout.addWidget(self.period_combo)
        
        controls_layout.addWidget(QLabel("From:"))
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        controls_layout.addWidget(self.from_date)
        
        controls_layout.addWidget(QLabel("To:"))
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        controls_layout.addWidget(self.to_date)
        
        generate_btn = QPushButton("📊 Generate Report")
        generate_btn.setProperty('accent', 'Qt.blue')
        generate_btn.clicked.connect(self.generate_individual_report)
        controls_layout.addWidget(generate_btn)
        
        export_btn = QPushButton("📄 Export")
        export_btn.setProperty('accent', 'Qt.green')
        export_btn.clicked.connect(self.export_individual_report)
        controls_layout.addWidget(export_btn)
        
        layout.addWidget(controls_frame)

        # Customer summary cards
        summary_frame = QFrame()
        summary_frame.setProperty('role', 'card')
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total purchases
        purchases_frame = QFrame()
        purchases_frame.setProperty('role', 'card')
        purchases_layout = QVBoxLayout(purchases_frame)
        
        self.customer_total_purchases = QLabel("Rs 0.00")
        self.customer_total_purchases.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        purchases_layout.addWidget(QLabel("💰 Total Purchases"))
        purchases_layout.addWidget(self.customer_total_purchases)
        
        # Total transactions
        transactions_frame = QFrame()
        transactions_frame.setProperty('role', 'card')
        transactions_layout = QVBoxLayout(transactions_frame)
        
        self.customer_total_transactions = QLabel("0")
        self.customer_total_transactions.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        transactions_layout.addWidget(QLabel("📊 Total Transactions"))
        transactions_layout.addWidget(self.customer_total_transactions)
        
        # Average order value
        avg_frame = QFrame()
        avg_frame.setProperty('role', 'card')
        avg_layout = QVBoxLayout(avg_frame)
        
        self.customer_avg_order = QLabel("Rs 0.00")
        self.customer_avg_order.setStyleSheet("font-size: 20px; font-weight: bold; color: #8b5cf6;")
        avg_layout.addWidget(QLabel("📈 Avg Order Value"))
        avg_layout.addWidget(self.customer_avg_order)
        
        # Outstanding balance
        balance_frame = QFrame()
        balance_frame.setProperty('role', 'card')
        balance_layout = QVBoxLayout(balance_frame)
        
        self.customer_balance = QLabel("Rs 0.00")
        self.customer_balance.setStyleSheet("font-size: 20px; font-weight: bold; color: #ef4444;")
        balance_layout.addWidget(QLabel("⚠️ Outstanding"))
        balance_layout.addWidget(self.customer_balance)
        
        summary_layout.addWidget(purchases_frame)
        summary_layout.addWidget(transactions_frame)
        summary_layout.addWidget(avg_frame)
        summary_layout.addWidget(balance_frame)
        
        layout.addWidget(summary_frame)

        # Transaction history table
        history_label = QLabel("📋 Transaction History")
        history_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px 0 10px 0;")
        layout.addWidget(history_label)
        
        self.individual_history_table = QTableWidget()
        self.individual_history_table.setColumnCount(7)
        self.individual_history_table.setHorizontalHeaderLabels([
            "Date", "Invoice #", "Type", "Items", "Subtotal", "Tax", "Total"
        ])
        
        layout.addWidget(self.individual_history_table)
        return widget

    def create_customer_summary_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Summary filters
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Customer Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Retail", "Wholesale"])
        self.type_filter.currentTextChanged.connect(self.load_customer_summary)
        filter_layout.addWidget(self.type_filter)
        
        filter_layout.addWidget(QLabel("Sort By:"))
        self.sort_filter = QComboBox()
        self.sort_filter.addItems([
            "Total Purchases", "Transaction Count", "Last Purchase", 
            "Outstanding Balance", "Customer Name"
        ])
        self.sort_filter.currentTextChanged.connect(self.load_customer_summary)
        filter_layout.addWidget(self.sort_filter)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_customer_summary)
        filter_layout.addWidget(refresh_btn)
        
        filter_layout.addStretch()
        
        layout.addWidget(filter_frame)

        # Customer summary table
        self.customer_summary_table = QTableWidget()
        self.customer_summary_table.setColumnCount(8)
        self.customer_summary_table.setHorizontalHeaderLabels([
            "Customer", "Type", "Total Purchases", "Transactions", 
            "Avg Order", "Last Purchase", "Outstanding", "Status"
        ])
        
        layout.addWidget(self.customer_summary_table)
        self.load_customer_summary()
        return widget

    def create_sales_analytics_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Analytics period
        period_frame = QFrame()
        period_frame.setProperty('role', 'card')
        period_layout = QHBoxLayout(period_frame)
        
        period_layout.addWidget(QLabel("Analysis Period:"))
        self.analytics_period = QComboBox()
        self.analytics_period.addItems([
            "This Month", "Last 3 Months", "Last 6 Months", 
            "This Year", "Last Year"
        ])
        self.analytics_period.currentTextChanged.connect(self.load_sales_analytics)
        period_layout.addWidget(self.analytics_period)
        
        period_layout.addStretch()
        
        layout.addWidget(period_frame)

        # Analytics summary
        analytics_frame = QFrame()
        analytics_frame.setProperty('role', 'card')
        analytics_layout = QHBoxLayout(analytics_frame)
        
        # Total customers
        customers_frame = QFrame()
        customers_frame.setProperty('role', 'card')
        customers_layout = QVBoxLayout(customers_frame)
        
        self.total_customers_label = QLabel("0")
        self.total_customers_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        customers_layout.addWidget(QLabel("👥 Total Customers"))
        customers_layout.addWidget(self.total_customers_label)
        
        # Active customers
        active_frame = QFrame()
        active_frame.setProperty('role', 'card')
        active_layout = QVBoxLayout(active_frame)
        
        self.active_customers_label = QLabel("0")
        self.active_customers_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        active_layout.addWidget(QLabel("✅ Active Customers"))
        active_layout.addWidget(self.active_customers_label)
        
        # New customers
        new_frame = QFrame()
        new_frame.setProperty('role', 'card')
        new_layout = QVBoxLayout(new_frame)
        
        self.new_customers_label = QLabel("0")
        self.new_customers_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #f59e0b;")
        new_layout.addWidget(QLabel("🆕 New Customers"))
        new_layout.addWidget(self.new_customers_label)
        
        # Revenue per customer
        revenue_frame = QFrame()
        revenue_frame.setProperty('role', 'card')
        revenue_layout = QVBoxLayout(revenue_frame)
        
        self.revenue_per_customer_label = QLabel("Rs 0.00")
        self.revenue_per_customer_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #8b5cf6;")
        revenue_layout.addWidget(QLabel("💰 Revenue/Customer"))
        revenue_layout.addWidget(self.revenue_per_customer_label)
        
        analytics_layout.addWidget(customers_frame)
        analytics_layout.addWidget(active_frame)
        analytics_layout.addWidget(new_frame)
        analytics_layout.addWidget(revenue_frame)
        
        layout.addWidget(analytics_frame)

        # Top customers table
        top_label = QLabel("🏆 Top Customers")
        top_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px 0 10px 0;")
        layout.addWidget(top_label)
        
        self.top_customers_table = QTableWidget()
        self.top_customers_table.setColumnCount(5)
        self.top_customers_table.setHorizontalHeaderLabels([
            "Rank", "Customer", "Total Purchases", "Transactions", "Avg Order"
        ])
        
        layout.addWidget(self.top_customers_table)
        self.load_sales_analytics()
        return widget

    def create_customer_comparison_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Comparison controls
        controls_frame = QFrame()
        controls_frame.setProperty('role', 'card')
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("Customer 1:"))
        self.customer1_combo = QComboBox()
        self.load_customers_for_comparison()
        controls_layout.addWidget(self.customer1_combo)
        
        controls_layout.addWidget(QLabel("Customer 2:"))
        self.customer2_combo = QComboBox()
        self.load_customers_for_comparison()
        controls_layout.addWidget(self.customer2_combo)
        
        compare_btn = QPushButton("⚖️ Compare")
        compare_btn.setProperty('accent', 'Qt.blue')
        compare_btn.clicked.connect(self.compare_customers)
        controls_layout.addWidget(compare_btn)
        
        controls_layout.addStretch()
        
        layout.addWidget(controls_frame)

        # Comparison results
        self.comparison_table = QTableWidget()
        self.comparison_table.setColumnCount(3)
        self.comparison_table.setHorizontalHeaderLabels([
            "Metric", "Customer 1", "Customer 2"
        ])
        
        layout.addWidget(self.comparison_table)
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

    def load_customers_for_comparison(self):
        try:
            from pos_app.models.database import Customer
            
            customers = self.controller.session.query(Customer).filter(  # TODO: Add .all() or .first()
                Customer.is_active == True
            ).all()
            
            for combo in [self.customer1_combo, self.customer2_combo]:
                combo.clear()
                combo.addItem("Select Customer", None)
                
                for customer in customers:
                    combo.addItem(customer.name, customer.id)
                
        except Exception as e:
            logging.exception("Failed to load customers for comparison")

    def generate_individual_report(self):
        customer_id = self.customer_combo.currentData()
        if not customer_id:
            return
        
        try:
            from pos_app.models.database import Customer, Sale, SaleItem
            
            customer = self.controller.session.get(Customer, customer_id)
            if not customer:
                return
            
            # Get date range
            period = self.period_combo.currentText()
            if period == "Custom Range":
                from_date = self.from_date.date().toPython()
                to_date = self.to_date.date().toPython()
            else:
                to_date = datetime.now().date()
                if period == "Last 30 Days":
                    from_date = to_date - timedelta(days=30)
                elif period == "Last 3 Months":
                    from_date = to_date - timedelta(days=90)
                elif period == "Last 6 Months":
                    from_date = to_date - timedelta(days=180)
                elif period == "Last Year":
                    from_date = to_date - timedelta(days=365)
                else:  # All Time
                    from_date = datetime(2000, 1, 1).date()
            
            # Get sales in date range
            sales = self.controller.session.query(Sale).filter(  # TODO: Add .all() or .first()
                Sale.customer_id == customer_id,
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date
            ).all()
            
            # Calculate statistics
            total_purchases = sum(sale.total_amount for sale in sales)
            total_transactions = len(sales)
            avg_order = total_purchases / total_transactions if total_transactions > 0 else 0
            
            # Update summary cards
            self.customer_total_purchases.setText(f"Rs {total_purchases:,.2f}")
            self.customer_total_transactions.setText(str(total_transactions))
            self.customer_avg_order.setText(f"Rs {avg_order:,.2f}")
            self.customer_balance.setText(f"Rs {customer.current_credit:,.2f}")
            
            # Load transaction history
            self.individual_history_table.setRowCount(len(sales))
            
            for i, sale in enumerate(sales):
                self.individual_history_table.setItem(i, 0, QTableWidgetItem(
                    sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else ""
                ))
                self.individual_history_table.setItem(i, 1, QTableWidgetItem(
                    sale.invoice_number or f"S-{sale.id}"
                ))
                self.individual_history_table.setItem(i, 2, QTableWidgetItem(
                    "Wholesale" if sale.is_wholesale else "Retail"
                ))
                self.individual_history_table.setItem(i, 3, QTableWidgetItem(str(len(sale.items))))
                self.individual_history_table.setItem(i, 4, QTableWidgetItem(f"Rs {sale.subtotal:,.2f}"))
                self.individual_history_table.setItem(i, 5, QTableWidgetItem(f"Rs {sale.tax_amount:,.2f}"))
                self.individual_history_table.setItem(i, 6, QTableWidgetItem(f"Rs {sale.total_amount:,.2f}"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate individual report: {str(e)}")

    def load_customer_summary(self):
        try:
            from pos_app.models.database import Customer, Sale
            from sqlalchemy import func
            
            # Build query based on filters
            query = self.controller.session.query(
                Customer.id,
                Customer.name,
                Customer.type,
                Customer.current_credit,
                func.count(Sale.id).label('transaction_count'),
                func.sum(Sale.total_amount).label('total_purchases'),
                func.avg(Sale.total_amount).label('avg_order'),
                func.max(Sale.sale_date).label('last_purchase')
            ).outerjoin(Sale).group_by(Customer.id)
            
            # Apply type filter
            type_filter = self.type_filter.currentText()
            if type_filter != "All Types":
                if type_filter == "Retail":
                    query = query.filter(Customer.type == 'RETAIL')
                elif type_filter == "Wholesale":
                    query = query.filter(Customer.type == 'WHOLESALE')
            
            customers = query.all()
            
            # Sort results
            sort_by = self.sort_filter.currentText()
            if sort_by == "Total Purchases":
                customers = sorted(customers, key=lambda x: x.total_purchases or 0, reverse=True)
            elif sort_by == "Transaction Count":
                customers = sorted(customers, key=lambda x: x.transaction_count or 0, reverse=True)
            elif sort_by == "Last Purchase":
                customers = sorted(customers, key=lambda x: x.last_purchase or datetime.min, reverse=True)
            elif sort_by == "Outstanding Balance":
                customers = sorted(customers, key=lambda x: x.current_credit or 0, reverse=True)
            else:  # Customer Name
                customers = sorted(customers, key=lambda x: x.name)
            
            self.customer_summary_table.setRowCount(len(customers))
            
            for i, customer in enumerate(customers):
                self.customer_summary_table.setItem(i, 0, QTableWidgetItem(customer.name))
                customer_type = str(customer.type).title() if customer.type else ""
                self.customer_summary_table.setItem(i, 1, QTableWidgetItem(customer_type))
                
                total_purchases = customer.total_purchases or 0
                self.customer_summary_table.setItem(i, 2, QTableWidgetItem(f"Rs {total_purchases:,.2f}"))
                
                transaction_count = customer.transaction_count or 0
                self.customer_summary_table.setItem(i, 3, QTableWidgetItem(str(transaction_count)))
                
                avg_order = customer.avg_order or 0
                self.customer_summary_table.setItem(i, 4, QTableWidgetItem(f"Rs {avg_order:,.2f}"))
                
                last_purchase = customer.last_purchase.strftime('%Y-%m-%d') if customer.last_purchase else "Never"
                self.customer_summary_table.setItem(i, 5, QTableWidgetItem(last_purchase))
                
                outstanding = customer.current_credit or 0
                outstanding_item = QTableWidgetItem(f"Rs {outstanding:,.2f}")
                if outstanding > 0:
                    outstanding_item.setForeground(Qt.red)
                self.customer_summary_table.setItem(i, 6, outstanding_item)
                
                # Determine status
                if transaction_count == 0:
                    status = "No Purchases"
                elif customer.last_purchase and (datetime.now() - customer.last_purchase).days > 90:
                    status = "Inactive"
                else:
                    status = "Active"
                
                status_item = QTableWidgetItem(status)
                if status == "Inactive":
                    status_item.setForeground(Qt.red)
                elif status == "No Purchases":
                    status_item.setForeground(Qt.gray)
                else:
                    status_item.setForeground(Qt.green)
                self.customer_summary_table.setItem(i, 7, status_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customer summary: {str(e)}")

    def load_sales_analytics(self):
        try:
            from pos_app.models.database import Customer, Sale
            from sqlalchemy import func
            
            # Get period dates
            period = self.analytics_period.currentText()
            to_date = datetime.now()
            
            if period == "This Month":
                from_date = to_date.replace(day=1)
            elif period == "Last 3 Months":
                from_date = to_date - timedelta(days=90)
            elif period == "Last 6 Months":
                from_date = to_date - timedelta(days=180)
            elif period == "This Year":
                from_date = to_date.replace(month=1, day=1)
            else:  # Last Year
                from_date = to_date.replace(year=to_date.year-1, month=1, day=1)
                to_date = to_date.replace(month=12, day=31)
            
            # Calculate analytics
            total_customers = self.controller.session.query(Customer).filter(  # TODO: Add .all() or .first()
                Customer.is_active == True
            ).count()
            
            active_customers = self.controller.session.query(Customer).join(Sale).filter(  # TODO: Add .all() or .first()
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date
            ).distinct().count()
            
            new_customers = self.controller.session.query(Customer).filter(  # TODO: Add .all() or .first()
                Customer.created_at >= from_date,
                Customer.created_at <= to_date
            ).count()
            
            # Revenue per customer
            total_revenue = self.controller.session.query(func.sum(Sale.total_amount)).filter(  # TODO: Add .all() or .first()
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date
            ).scalar() or 0
            
            revenue_per_customer = total_revenue / active_customers if active_customers > 0 else 0
            
            # Update analytics summary
            self.total_customers_label.setText(str(total_customers))
            self.active_customers_label.setText(str(active_customers))
            self.new_customers_label.setText(str(new_customers))
            self.revenue_per_customer_label.setText(f"Rs {revenue_per_customer:,.2f}")
            
            # Load top customers
            top_customers = self.controller.session.query(
                Customer.name,
                func.sum(Sale.total_amount).label('total'),
                func.count(Sale.id).label('transactions'),
                func.avg(Sale.total_amount).label('avg_order')
            ).join(Sale).filter(
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date
            ).group_by(Customer.id, Customer.name).order_by(
                func.sum(Sale.total_amount).desc()
            ).limit(10).all()
            
            self.top_customers_table.setRowCount(len(top_customers))
            
            for i, (name, total, transactions, avg_order) in enumerate(top_customers):
                self.top_customers_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
                self.top_customers_table.setItem(i, 1, QTableWidgetItem(name))
                self.top_customers_table.setItem(i, 2, QTableWidgetItem(f"Rs {total:,.2f}"))
                self.top_customers_table.setItem(i, 3, QTableWidgetItem(str(transactions)))
                self.top_customers_table.setItem(i, 4, QTableWidgetItem(f"Rs {avg_order:,.2f}"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sales analytics: {str(e)}")

    def compare_customers(self):
        customer1_id = self.customer1_combo.currentData()
        customer2_id = self.customer2_combo.currentData()
        
        if not customer1_id or not customer2_id:
            QMessageBox.warning(self, "Warning", "Please select both customers to compare")
            return
        
        try:
            from pos_app.models.database import Customer, Sale
            from sqlalchemy import func
            
            # Get customer data
            customers_data = {}
            
            for customer_id in [customer1_id, customer2_id]:
                customer = self.controller.session.get(Customer, customer_id)
                
                # Get sales statistics
                sales_stats = self.controller.session.query(
                    func.count(Sale.id).label('transactions'),
                    func.sum(Sale.total_amount).label('total'),
                    func.avg(Sale.total_amount).label('avg_order'),
                    func.max(Sale.sale_date).label('last_purchase')
                ).filter(Sale.customer_id == customer_id).first()
                
                customer_type = str(customer.type).title() if customer.type else "Retail"
                customers_data[customer_id] = {
                    'name': customer.name,
                    'type': customer_type,
                    'transactions': sales_stats.transactions or 0,
                    'total': sales_stats.total or 0,
                    'avg_order': sales_stats.avg_order or 0,
                    'last_purchase': sales_stats.last_purchase.strftime('%Y-%m-%d') if sales_stats.last_purchase else "Never",
                    'outstanding': customer.current_credit or 0,
                    'credit_limit': customer.credit_limit or 0
                }
            
            # Populate comparison table
            metrics = [
                ("Customer Name", "name"),
                ("Customer Type", "type"),
                ("Total Transactions", "transactions"),
                ("Total Purchases", "total"),
                ("Average Order Value", "avg_order"),
                ("Last Purchase", "last_purchase"),
                ("Outstanding Balance", "outstanding"),
                ("Credit Limit", "credit_limit")
            ]
            
            self.comparison_table.setRowCount(len(metrics))
            
            for i, (metric_name, metric_key) in enumerate(metrics):
                self.comparison_table.setItem(i, 0, QTableWidgetItem(metric_name))
                
                value1 = customers_data[customer1_id][metric_key]
                value2 = customers_data[customer2_id][metric_key]
                
                # Format values
                if metric_key in ['total', 'avg_order', 'outstanding', 'credit_limit']:
                    value1_text = f"Rs {value1:,.2f}"
                    value2_text = f"Rs {value2:,.2f}"
                else:
                    value1_text = str(value1)
                    value2_text = str(value2)
                
                self.comparison_table.setItem(i, 1, QTableWidgetItem(value1_text))
                self.comparison_table.setItem(i, 2, QTableWidgetItem(value2_text))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to compare customers: {str(e)}")

    def export_individual_report(self):
        QMessageBox.information(self, "Info", "Export individual report functionality would be implemented here")
