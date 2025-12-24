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

class TaxManagementWidget(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("📊 Tax Management System")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()
        
        # Tax Rates
        rates_tab = self.create_tax_rates_tab()
        tabs.addTab(rates_tab, "📋 Tax Rates")
        
        # Product Tax Settings
        product_tax_tab = self.create_product_tax_tab()
        tabs.addTab(product_tax_tab, "📦 Product Tax")
        
        # Tax Reports
        reports_tab = self.create_tax_reports_tab()
        tabs.addTab(reports_tab, "📊 Tax Reports")
        
        # Tax Settings
        settings_tab = self.create_tax_settings_tab()
        tabs.addTab(settings_tab, "⚙️ Settings")
        
        layout.addWidget(tabs)

    def create_tax_rates_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Actions
        actions_layout = QHBoxLayout()
        
        add_rate_btn = QPushButton("➕ Add Tax Rate")
        add_rate_btn.setProperty('accent', 'Qt.green')
        add_rate_btn.setMinimumHeight(40)
        add_rate_btn.clicked.connect(self.add_tax_rate)
        
        edit_rate_btn = QPushButton("✏️ Edit Rate")
        edit_rate_btn.setProperty('accent', 'Qt.blue')
        edit_rate_btn.setMinimumHeight(40)
        
        set_default_btn = QPushButton("⭐ Set as Default")
        set_default_btn.setProperty('accent', 'orange')
        set_default_btn.setMinimumHeight(40)
        set_default_btn.clicked.connect(self.set_default_tax)
        
        deactivate_btn = QPushButton("⏸️ Deactivate")
        deactivate_btn.setProperty('accent', 'Qt.red')
        deactivate_btn.setMinimumHeight(40)
        
        actions_layout.addWidget(add_rate_btn)
        actions_layout.addWidget(edit_rate_btn)
        actions_layout.addWidget(set_default_btn)
        actions_layout.addWidget(deactivate_btn)
        actions_layout.addStretch()
        
        layout.addLayout(actions_layout)

        # Tax rates table
        self.tax_rates_table = QTableWidget()
        self.tax_rates_table.setColumnCount(5)
        self.tax_rates_table.setHorizontalHeaderLabels([
            "Tax Name", "Rate (%)", "Description", "Default", "Status"
        ])
        self.tax_rates_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.tax_rates_table)
        self.load_tax_rates()
        return widget

    def create_product_tax_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Product tax controls
        controls_frame = QFrame()
        controls_frame.setProperty('role', 'card')
        controls_layout = QHBoxLayout(controls_frame)
        
        controls_layout.addWidget(QLabel("Product:"))
        self.product_tax_combo = QComboBox()
        self.load_products_for_tax()
        controls_layout.addWidget(self.product_tax_combo)
        
        controls_layout.addWidget(QLabel("Tax Rate:"))
        self.product_tax_rate = QComboBox()
        self.load_tax_rates_combo()
        controls_layout.addWidget(self.product_tax_rate)
        
        apply_tax_btn = QPushButton("Apply Tax")
        apply_tax_btn.setProperty('accent', 'Qt.green')
        apply_tax_btn.clicked.connect(self.apply_product_tax)
        controls_layout.addWidget(apply_tax_btn)
        
        controls_layout.addStretch()
        
        # Bulk operations
        bulk_frame = QFrame()
        bulk_frame.setProperty('role', 'card')
        bulk_layout = QHBoxLayout(bulk_frame)
        
        bulk_layout.addWidget(QLabel("Bulk Apply:"))
        
        self.bulk_category = QComboBox()
        self.bulk_category.addItem("All Products", None)
        self.load_categories_for_bulk()
        bulk_layout.addWidget(self.bulk_category)
        
        self.bulk_tax_rate = QComboBox()
        self.load_tax_rates_combo(self.bulk_tax_rate)
        bulk_layout.addWidget(self.bulk_tax_rate)
        
        bulk_apply_btn = QPushButton("🔄 Bulk Apply")
        bulk_apply_btn.setProperty('accent', 'Qt.blue')
        bulk_apply_btn.clicked.connect(self.bulk_apply_tax)
        bulk_layout.addWidget(bulk_apply_btn)
        
        bulk_layout.addStretch()
        
        layout.addWidget(controls_frame)
        layout.addWidget(bulk_frame)

        # Product tax table
        self.product_tax_table = QTableWidget()
        self.product_tax_table.setColumnCount(6)
        self.product_tax_table.setHorizontalHeaderLabels([
            "Product", "Category", "Base Price", "Tax Rate (%)", "Tax Amount", "Final Price"
        ])
        
        layout.addWidget(self.product_tax_table)
        self.load_product_tax_settings()
        return widget

    def create_tax_reports_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Report filters
        filter_frame = QFrame()
        filter_frame.setProperty('role', 'card')
        filter_layout = QHBoxLayout(filter_frame)
        
        filter_layout.addWidget(QLabel("Period:"))
        self.report_period = QComboBox()
        self.report_period.addItems([
            "Today", "This Week", "This Month", "This Quarter", 
            "This Year", "Custom Range"
        ])
        filter_layout.addWidget(self.report_period)
        
        filter_layout.addWidget(QLabel("From:"))
        self.report_from = QDateEdit()
        self.report_from.setDate(QDate.currentDate().addDays(-30))
        self.report_from.setCalendarPopup(True)
        filter_layout.addWidget(self.report_from)
        
        filter_layout.addWidget(QLabel("To:"))
        self.report_to = QDateEdit()
        self.report_to.setDate(QDate.currentDate())
        self.report_to.setCalendarPopup(True)
        filter_layout.addWidget(self.report_to)
        
        generate_btn = QPushButton("📊 Generate Report")
        generate_btn.setProperty('accent', 'Qt.blue')
        generate_btn.clicked.connect(self.generate_tax_report)
        filter_layout.addWidget(generate_btn)
        
        filter_layout.addStretch()
        
        export_btn = QPushButton("📄 Export")
        export_btn.setProperty('accent', 'Qt.green')
        export_btn.clicked.connect(self.export_tax_report)
        filter_layout.addWidget(export_btn)
        
        layout.addWidget(filter_frame)

        # Tax summary
        summary_frame = QFrame()
        summary_frame.setProperty('role', 'card')
        summary_layout = QHBoxLayout(summary_frame)
        
        # Total tax collected
        tax_frame = QFrame()
        tax_frame.setProperty('role', 'card')
        tax_layout = QVBoxLayout(tax_frame)
        
        self.total_tax_label = QLabel("Rs 0.00")
        self.total_tax_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #3b82f6;")
        tax_layout.addWidget(QLabel("💰 Total Tax Collected"))
        tax_layout.addWidget(self.total_tax_label)
        
        # Total sales
        sales_frame = QFrame()
        sales_frame.setProperty('role', 'card')
        sales_layout = QVBoxLayout(sales_frame)
        
        self.total_sales_label = QLabel("Rs 0.00")
        self.total_sales_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        sales_layout.addWidget(QLabel("🛒 Total Sales"))
        sales_layout.addWidget(self.total_sales_label)
        
        # Average tax rate
        avg_frame = QFrame()
        avg_frame.setProperty('role', 'card')
        avg_layout = QVBoxLayout(avg_frame)
        
        self.avg_tax_label = QLabel("0.00%")
        self.avg_tax_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #8b5cf6;")
        avg_layout.addWidget(QLabel("📊 Average Tax Rate"))
        avg_layout.addWidget(self.avg_tax_label)
        
        summary_layout.addWidget(tax_frame)
        summary_layout.addWidget(sales_frame)
        summary_layout.addWidget(avg_frame)
        
        layout.addWidget(summary_frame)

        # Tax report table
        self.tax_report_table = QTableWidget()
        self.tax_report_table.setColumnCount(7)
        self.tax_report_table.setHorizontalHeaderLabels([
            "Date", "Invoice #", "Customer", "Subtotal", "Tax Rate", "Tax Amount", "Total"
        ])
        
        layout.addWidget(self.tax_report_table)
        self.generate_tax_report()
        return widget

    def create_tax_settings_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # General tax settings
        general_frame = QFrame()
        general_frame.setProperty('role', 'card')
        general_layout = QFormLayout(general_frame)
        
        # Tax calculation method
        self.tax_method = QComboBox()
        self.tax_method.addItems(["Inclusive", "Exclusive"])
        general_layout.addRow("Tax Calculation:", self.tax_method)
        
        # Default tax rate
        self.default_tax = QComboBox()
        self.load_tax_rates_combo(self.default_tax)
        general_layout.addRow("Default Tax Rate:", self.default_tax)
        
        # Tax rounding
        self.tax_rounding = QComboBox()
        self.tax_rounding.addItems(["Round to nearest cent", "Round up", "Round down", "No rounding"])
        general_layout.addRow("Tax Rounding:", self.tax_rounding)
        
        # Tax display
        self.tax_display = QCheckBox("Show tax breakdown on receipts")
        self.tax_display.setChecked(True)
        general_layout.addRow("Receipt Display:", self.tax_display)
        
        # Auto-apply tax
        self.auto_apply = QCheckBox("Automatically apply tax to new products")
        self.auto_apply.setChecked(True)
        general_layout.addRow("Auto Apply:", self.auto_apply)
        
        save_settings_btn = QPushButton("💾 Save Settings")
        save_settings_btn.setProperty('accent', 'Qt.green')
        save_settings_btn.clicked.connect(self.save_tax_settings)
        general_layout.addRow(save_settings_btn)
        
        layout.addWidget(general_frame)

        # Tax exemptions
        exemption_frame = QFrame()
        exemption_frame.setProperty('role', 'card')
        exemption_layout = QVBoxLayout(exemption_frame)
        
        exemption_layout.addWidget(QLabel("🚫 Tax Exemptions"))
        
        # Exemption controls
        exemption_controls = QHBoxLayout()
        
        self.exemption_customer = QComboBox()
        self.exemption_customer.addItem("Select Customer", None)
        self.load_customers_for_exemption()
        exemption_controls.addWidget(self.exemption_customer)
        
        add_exemption_btn = QPushButton("Add Exemption")
        add_exemption_btn.clicked.connect(self.add_tax_exemption)
        exemption_controls.addWidget(add_exemption_btn)
        
        exemption_controls.addStretch()
        exemption_layout.addLayout(exemption_controls)
        
        # Exemptions table
        self.exemptions_table = QTableWidget()
        self.exemptions_table.setColumnCount(4)
        self.exemptions_table.setHorizontalHeaderLabels([
            "Customer", "Type", "Exemption Rate", "Valid Until"
        ])
        exemption_layout.addWidget(self.exemptions_table)
        
        layout.addWidget(exemption_frame)
        
        layout.addStretch()
        return widget

    def add_tax_rate(self):
        dialog = TaxRateDialog(self, self.controller)
        if dialog.exec() == QDialog.Accepted:
            try:
                from pos_app.models.database import TaxRate
                
                tax_rate = TaxRate(
                    name=dialog.name.text(),
                    rate=dialog.rate.value(),
                    description=dialog.description.toPlainText(),
                    is_default=dialog.is_default.isChecked(),
                    is_active=True
                )
                
                # If this is set as default, unset other defaults
                if dialog.is_default.isChecked():
                    self.controller.session.query(TaxRate).update({TaxRate.is_default: False})
                
                self.controller.session.add(tax_rate)
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", "Tax rate added successfully!")
                self.load_tax_rates()
                self.load_tax_rates_combo()
                
            except Exception as e:
                self.controller.session.rollback()
                QMessageBox.critical(self, "Error", f"Failed to add tax rate: {str(e)}")

    def set_default_tax(self):
        selected_rows = self.tax_rates_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "Please select a tax rate to set as default")
            return
        
        try:
            from pos_app.models.database import TaxRate
            
            # Get selected tax rate ID (you'd need to store this in the table)
            row = selected_rows[0].row()
            tax_name = self.tax_rates_table.item(row, 0).text()
            
            # Unset all defaults
            self.controller.session.query(TaxRate).update({TaxRate.is_default: False})
            
            # Set new default
            tax_rate = self.controller.session.query(TaxRate).filter(TaxRate.name == tax_name).first()
            if tax_rate:
                tax_rate.is_default = True
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", f"{tax_name} set as default tax rate!")
                self.load_tax_rates()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to set default tax rate: {str(e)}")

    def apply_product_tax(self):
        try:
            from pos_app.models.database import Product, TaxRate
            
            product_id = self.product_tax_combo.currentData()
            tax_rate_id = self.product_tax_rate.currentData()
            
            if not product_id or not tax_rate_id:
                QMessageBox.warning(self, "Warning", "Please select both product and tax rate")
                return
            
            product = self.controller.session.get(Product, product_id)
            tax_rate = self.controller.session.get(TaxRate, tax_rate_id)
            
            if product and tax_rate:
                product.tax_rate = tax_rate.rate
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", f"Tax rate applied to {product.name}")
                self.load_product_tax_settings()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to apply tax rate: {str(e)}")

    def bulk_apply_tax(self):
        try:
            from pos_app.models.database import Product, TaxRate, Category
            
            category_id = self.bulk_category.currentData()
            tax_rate_id = self.bulk_tax_rate.currentData()
            
            if not tax_rate_id:
                QMessageBox.warning(self, "Warning", "Please select a tax rate")
                return
            
            tax_rate = self.controller.session.get(TaxRate, tax_rate_id)
            if not tax_rate:
                QMessageBox.warning(self, "Warning", "Tax rate not found")
                return
            
            # Build query
            query = self.controller.session.query(Product).filter(Product.is_active == True)
            
            if category_id:
                # Filter by category (you'd need to implement category filtering)
                pass
            
            products = query.all()
            
            # Confirm bulk operation
            reply = QMessageBox.question(
                self, "Confirm Bulk Operation", 
                f"Apply {tax_rate.name} ({tax_rate.rate}%) to {len(products)} products?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                for product in products:
                    product.tax_rate = tax_rate.rate
                
                self.controller.session.commit()
                
                QMessageBox.information(self, "Success", f"Tax rate applied to {len(products)} products!")
                self.load_product_tax_settings()
            
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to bulk apply tax rate: {str(e)}")

    def generate_tax_report(self):
        try:
            from pos_app.models.database import Sale, SaleItem
            from sqlalchemy import func
            
            # Get date range (PySide6 uses toPython, PyQt6 uses toPyDate)
            try:
                from_date = self.report_from.date().toPython()
                to_date = self.report_to.date().toPython()
            except AttributeError:
                from_date = self.report_from.date().toPyDate()
                to_date = self.report_to.date().toPyDate()
            
            # Query sales with tax information
            sales = self.controller.session.query(Sale).filter(
                Sale.sale_date >= from_date,
                Sale.sale_date <= to_date,
                Sale.status == "COMPLETED"
            ).all()
            
            self.tax_report_table.setRowCount(len(sales))
            
            total_tax = 0
            total_sales = 0
            
            for i, sale in enumerate(sales):
                self.tax_report_table.setItem(i, 0, QTableWidgetItem(
                    sale.sale_date.strftime('%Y-%m-%d') if sale.sale_date else ""
                ))
                self.tax_report_table.setItem(i, 1, QTableWidgetItem(sale.invoice_number or f"S-{sale.id}"))
                
                customer_name = sale.customer.name if sale.customer else "Walk-in"
                self.tax_report_table.setItem(i, 2, QTableWidgetItem(customer_name))
                
                self.tax_report_table.setItem(i, 3, QTableWidgetItem(f"Rs {sale.subtotal:,.2f}"))
                
                # Calculate average tax rate for this sale
                avg_tax_rate = 0
                if sale.subtotal > 0:
                    avg_tax_rate = (sale.tax_amount / sale.subtotal) * 100
                
                self.tax_report_table.setItem(i, 4, QTableWidgetItem(f"{avg_tax_rate:.2f}%"))
                self.tax_report_table.setItem(i, 5, QTableWidgetItem(f"Rs {sale.tax_amount:,.2f}"))
                self.tax_report_table.setItem(i, 6, QTableWidgetItem(f"Rs {sale.total_amount:,.2f}"))
                
                total_tax += sale.tax_amount
                total_sales += sale.total_amount
            
            # Update summary
            self.total_tax_label.setText(f"Rs {total_tax:,.2f}")
            self.total_sales_label.setText(f"Rs {total_sales:,.2f}")
            
            avg_tax_rate = (total_tax / total_sales * 100) if total_sales > 0 else 0
            self.avg_tax_label.setText(f"{avg_tax_rate:.2f}%")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate tax report: {str(e)}")

    def load_tax_rates(self):
        try:
            from pos_app.models.database import TaxRate
            
            tax_rates = self.controller.session.query(TaxRate).filter(
                TaxRate.is_active == True
            ).all()
            
            self.tax_rates_table.setRowCount(len(tax_rates))
            
            for i, rate in enumerate(tax_rates):
                self.tax_rates_table.setItem(i, 0, QTableWidgetItem(rate.name))
                self.tax_rates_table.setItem(i, 1, QTableWidgetItem(f"{rate.rate:.2f}%"))
                self.tax_rates_table.setItem(i, 2, QTableWidgetItem(rate.description or ""))
                
                default_item = QTableWidgetItem("Yes" if rate.is_default else "No")
                if rate.is_default:
                    default_item.setForeground(Qt.green)
                self.tax_rates_table.setItem(i, 3, default_item)
                
                self.tax_rates_table.setItem(i, 4, QTableWidgetItem("Active" if rate.is_active else "Inactive"))
                
                # Store tax rate ID
                self.tax_rates_table.item(i, 0).setData(Qt.UserRole, rate.id)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load tax rates: {str(e)}")

    def load_tax_rates_combo(self, combo=None):
        if combo is None:
            combo = self.product_tax_rate
        
        try:
            from pos_app.models.database import TaxRate
            
            combo.clear()
            combo.addItem("No Tax", None)
            
            tax_rates = self.controller.session.query(TaxRate).filter(  # TODO: Add .all() or .first()
                TaxRate.is_active == True
            ).all()
            
            for rate in tax_rates:
                combo.addItem(f"{rate.name} ({rate.rate:.2f}%)", rate.id)
                
        except Exception as e:
            logging.exception("Failed to load tax rates for combo")

    def load_products_for_tax(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(  # TODO: Add .all() or .first()
                Product.is_active == True
            ).all()
            
            self.product_tax_combo.clear()
            for product in products:
                self.product_tax_combo.addItem(f"{product.name} - Rs {product.retail_price:,.2f}", product.id)
                
        except Exception as e:
            logging.exception("Failed to load products for tax")

    def load_categories_for_bulk(self):
        try:
            from pos_app.models.database import Category
            
            categories = self.controller.session.query(Category).all()
            
            for category in categories:
                self.bulk_category.addItem(category.name, category.id)
                
        except Exception as e:
            logging.exception("Failed to load categories for bulk")

    def load_customers_for_exemption(self):
        try:
            from pos_app.models.database import Customer
            
            customers = self.controller.session.query(Customer).filter(  # TODO: Add .all() or .first()
                Customer.is_active == True
            ).all()
            
            for customer in customers:
                self.exemption_customer.addItem(customer.name, customer.id)
                
        except Exception as e:
            logging.exception("Failed to load customers for exemption")

    def load_product_tax_settings(self):
        try:
            from pos_app.models.database import Product
            
            products = self.controller.session.query(Product).filter(  # TODO: Add .all() or .first()
                Product.is_active == True
            ).all()
            
            self.product_tax_table.setRowCount(len(products))
            
            for i, product in enumerate(products):
                self.product_tax_table.setItem(i, 0, QTableWidgetItem(product.name))
                self.product_tax_table.setItem(i, 1, QTableWidgetItem("General"))  # Category placeholder
                self.product_tax_table.setItem(i, 2, QTableWidgetItem(f"Rs {product.retail_price:,.2f}"))
                
                tax_rate = getattr(product, 'tax_rate', 0)
                self.product_tax_table.setItem(i, 3, QTableWidgetItem(f"{tax_rate:.2f}%"))
                
                tax_amount = product.retail_price * (tax_rate / 100)
                self.product_tax_table.setItem(i, 4, QTableWidgetItem(f"Rs {tax_amount:,.2f}"))
                
                final_price = product.retail_price + tax_amount
                self.product_tax_table.setItem(i, 5, QTableWidgetItem(f"Rs {final_price:,.2f}"))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load product tax settings: {str(e)}")

    # Placeholder methods
    def export_tax_report(self):
        QMessageBox.information(self, "Info", "Export tax report functionality would be implemented here")

    def save_tax_settings(self):
        QMessageBox.information(self, "Success", "Tax settings saved successfully!")

    def add_tax_exemption(self):
        QMessageBox.information(self, "Info", "Add tax exemption functionality would be implemented here")


class TaxRateDialog(QDialog):
    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self.setWindowTitle("Add Tax Rate")
        self.setMinimumSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g., GST, VAT, Sales Tax")
        layout.addRow("Tax Name:", self.name)

        self.rate = QDoubleSpinBox()
        self.rate.setRange(0, 100)
        self.rate.setDecimals(2)
        self.rate.setSuffix("%")
        layout.addRow("Tax Rate:", self.rate)

        self.description = QTextEdit()
        self.description.setMaximumHeight(80)
        self.description.setPlaceholderText("Description of this tax rate...")
        layout.addRow("Description:", self.description)

        self.is_default = QCheckBox("Set as default tax rate")
        layout.addRow("Default:", self.is_default)

        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn.setProperty('accent', 'Qt.green')
        save_btn.clicked.connect(self.accept)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addRow(buttons_layout)
