try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QComboBox, QStackedWidget,
        QTableWidget, QTableWidgetItem, QFrame,
        QDateEdit, QMessageBox
    )
    from PySide6.QtCore import Qt, QDate
    from PySide6.QtGui import QPixmap
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QComboBox, QStackedWidget,
        QTableWidget, QTableWidgetItem, QFrame,
        QDateEdit, QMessageBox
    )
    from PyQt6.QtCore import Qt, QDate
    from PyQt6.QtGui import QPixmap
from pos_app.utils.document_generator import DocumentGenerator
from pos_app.utils.logger import app_logger

class ReportsWidget(QWidget):
    def __init__(self, controllers):
        super().__init__()
        self.controllers = controllers
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("📈 Reports & Analytics")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(header)

        # Report controls
        controls_layout = QHBoxLayout()
        
        # Report type selector
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Sales Summary",
            "Inventory Status",
            "Customer Analysis",
            "Supplier Purchases (Detailed)",
            "Receivables (Customers)",
            "Payables (Suppliers)"
        ])
        self.report_type.currentIndexChanged.connect(self.switch_report)
        
        # Date range
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        try:
            for d in (self.start_date, self.end_date):
                d.setCalendarPopup(True)
                d.setMinimumHeight(36)
        except Exception:
            pass
        
        # Generate button
        generate_btn = QPushButton("Generate Report")
        generate_btn.clicked.connect(self.generate_report)
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_current_report)
        export_pdf_btn = QPushButton("Export PDF")
        export_pdf_btn.clicked.connect(self.export_current_pdf)

        # Supplier filter (used by Supplier Purchases report). Always visible for convenience
        self.supplier_filter = QComboBox()
        self.supplier_filter.addItem("All Suppliers", None)
        try:
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            from pos_app.models.database import Supplier
            suppliers = controller.session.query(Supplier).filter(Supplier.is_active == True).all()
            for s in suppliers:
                self.supplier_filter.addItem(s.name, s.id)
        except Exception:
            pass
        
        controls_layout.addWidget(QLabel("Report Type:"))
        controls_layout.addWidget(self.report_type)
        controls_layout.addWidget(QLabel("From:"))
        controls_layout.addWidget(self.start_date)
        controls_layout.addWidget(QLabel("To:"))
        controls_layout.addWidget(self.end_date)
        # Make buttons consistent in size and use global accent colors
        try:
            generate_btn.setProperty('accent', 'Qt.green')
            export_btn.setProperty('accent', 'Qt.blue')
            export_pdf_btn.setProperty('accent', 'orange')
        except Exception:
            pass
        generate_btn.setMinimumHeight(44)
        export_btn.setMinimumHeight(44)
        export_pdf_btn.setMinimumHeight(44)
        controls_layout.addWidget(QLabel("Supplier:"))
        controls_layout.addWidget(self.supplier_filter)
        controls_layout.addWidget(generate_btn)
        controls_layout.addWidget(export_btn)
        controls_layout.addWidget(export_pdf_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)

        # Report content area
        self.report_stack = QStackedWidget()
        
        # Create different report widgets
        self.sales_report = self.create_report_widget()
        self.inventory_report = self.create_report_widget()
        self.customer_report = self.create_report_widget()
        self.supplier_report = self.create_report_widget()
        self.receivables_report = self.create_report_widget()
        self.payables_report = self.create_report_widget()
        
        self.report_stack.addWidget(self.sales_report)
        self.report_stack.addWidget(self.inventory_report)
        self.report_stack.addWidget(self.customer_report)
        self.report_stack.addWidget(self.supplier_report)
        self.report_stack.addWidget(self.receivables_report)
        self.report_stack.addWidget(self.payables_report)
        
        layout.addWidget(self.report_stack)

    def create_report_widget(self):
        widget = QFrame()
        # Use global dark theme card style defined as QFrame#card in utils.styles
        widget.setObjectName('card')
        
        layout = QVBoxLayout(widget)
        
        # Summary section
        summary = QFrame()
        # Dark summary container style
        summary.setStyleSheet("background-color: #0b1220; border: 1px solid #1f2937; border-radius: 8px; padding: 10px;")
        summary_layout = QHBoxLayout(summary)
        
        # Add placeholder summary cards
        for _ in range(4):
            card = QFrame()
            # Dark mini-card style for metrics
            card.setStyleSheet("background-color: #111827; border: 1px solid #1f2937; border-radius: 8px; padding: 10px;")
            card_layout = QVBoxLayout(card)
            value_lbl = QLabel("0")
            label_lbl = QLabel("Metric")
            try:
                value_lbl.setWordWrap(False)
                label_lbl.setWordWrap(False)
                value_lbl.setAlignment(Qt.AlignLeft)
                label_lbl.setAlignment(Qt.AlignLeft)
            except Exception:
                pass
            card_layout.addWidget(value_lbl)
            card_layout.addWidget(label_lbl)
            summary_layout.addWidget(card)
        
        layout.addWidget(summary)
        
        # Chart preview (used by sales report)
        chart_label = QLabel()
        chart_label.setObjectName('chart_label')
        chart_label.setFixedHeight(180)
        chart_label.setAlignment(Qt.AlignCenter)
        chart_label.setStyleSheet('background-color: #0b1220; border: 1px solid #1f2937;')
        layout.addWidget(chart_label)

        # Table for detailed data
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Date", "Item", "Quantity", "Amount", "Status"])
        try:
            from PySide6.QtWidgets import QHeaderView
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setWordWrap(False)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)
        except Exception:
            pass
        layout.addWidget(table)
        
        return widget

    def switch_report(self, index):
        # Map combo index to stack widget index
        self.report_stack.setCurrentIndex(index)

    def generate_report(self):
        # Get date range (PySide6 uses toPython, PyQt6 uses toPyDate)
        try:
            start = self.start_date.date().toPython()
            end = self.end_date.date().toPython()
        except AttributeError:
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
        
        # Get current report type
        report_type = self.report_type.currentText()
        
        # Generate appropriate report
        if report_type == "Sales Summary":
            self.generate_sales_report(start, end)
        elif report_type == "Inventory Status":
            self.generate_inventory_report()
        elif report_type == "Customer Analysis":
            self.generate_customer_report(start, end)
        elif report_type == "Supplier Purchases (Detailed)":
            self.generate_supplier_report(start, end)
        elif report_type == "Receivables (Customers)":
            self.generate_receivables_report()
        elif report_type == "Payables (Suppliers)":
            self.generate_payables_report()

    def generate_sales_report(self, start_date, end_date):
        try:
            # Use the reports controller (BusinessController) to fetch sales with product names
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            from pos_app.models.database import Sale, SaleItem, Product
            from datetime import datetime, timedelta
            
            # Convert dates to datetime objects for proper filtering
            # Start at beginning of start_date, end at end of end_date
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())
            
            # Query sales with items for detailed breakdown - sorted by date
            sales_query = controller.session.query(Sale).filter(
                Sale.sale_date >= start_datetime,
                Sale.sale_date <= end_datetime
            ).order_by(Sale.sale_date.desc()).all()
            
            # Build table with product names from SaleItems
            table = self.sales_report.findChild(QTableWidget)
            if table is None:
                return
            
            # Flatten sales to show one row per product sold
            rows = []
            product_quantities = {}  # Track quantities by product for most/least sold
            total_sales_amount = 0.0
            
            for s in sales_query:
                items = controller.session.query(SaleItem, Product).join(Product).filter(SaleItem.sale_id == s.id).all()
                if items:
                    for sale_item, product in items:
                        product_name = product.name if product else 'Unknown'
                        quantity = getattr(sale_item, 'quantity', 0)
                        amount = getattr(sale_item, 'total', 0.0)
                        try:
                            if getattr(s, 'is_refund', False):
                                # Show refund as positive quantities/amounts, labeled in status.
                                quantity = float(quantity or 0)
                                amount = float(amount or 0.0)
                        except Exception:
                            pass
                        
                        rows.append({
                            'date': str(getattr(s, 'sale_date', '')),
                            'product_name': product_name,
                            'quantity': quantity,
                            'amount': amount,
                            'invoice': (f"REFUND {getattr(s, 'invoice_number', '')}" if getattr(s, 'is_refund', False) else getattr(s, 'invoice_number', ''))
                        })
                        
                        # Track product quantities
                        product_quantities[product_name] = product_quantities.get(product_name, 0) + quantity
                        total_sales_amount += amount
                else:
                    # No items, show just the sale
                    amount = getattr(s, 'total_amount', 0.0)
                    try:
                        if getattr(s, 'is_refund', False):
                            amount = float(amount or 0.0)
                    except Exception:
                        pass
                    rows.append({
                        'date': str(getattr(s, 'sale_date', '')),
                        'product_name': getattr(s, 'invoice_number', '') or '',
                        'quantity': '-',
                        'amount': amount,
                        'invoice': (f"REFUND {getattr(s, 'status', '')}" if getattr(s, 'is_refund', False) else getattr(s, 'status', ''))
                    })
                    total_sales_amount += amount
            
            table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                table.setItem(i, 0, QTableWidgetItem(row['date']))
                table.setItem(i, 1, QTableWidgetItem(row['product_name']))
                table.setItem(i, 2, QTableWidgetItem(str(row['quantity'])))
                table.setItem(i, 3, QTableWidgetItem(f"Rs {float(row['amount']):.2f}"))
                table.setItem(i, 4, QTableWidgetItem(row['invoice']))
            
            # Calculate metrics
            most_sold_product = ""
            most_sold_qty = 0
            least_sold_product = ""
            least_sold_qty = float('inf')
            total_products_sold = 0
            
            if product_quantities:
                # Find most sold
                most_sold_product, most_sold_qty = max(product_quantities.items(), key=lambda x: x[1])
                # Find least sold
                least_sold_product, least_sold_qty = min(product_quantities.items(), key=lambda x: x[1])
                # Total products sold
                total_products_sold = sum(product_quantities.values())
            
            # Update summary cards
            try:
                summary = self.sales_report.findChildren(QFrame)[0]
                if hasattr(summary, 'layout'):
                    lay = summary.layout()
                    if lay and lay.count() >= 4:
                        # Card 0: Most Sold Product
                        card0 = lay.itemAt(0).widget()
                        if card0 and card0.layout().count() >= 2:
                            card0.layout().itemAt(0).widget().setText(f"{most_sold_product} ({most_sold_qty})")
                            card0.layout().itemAt(1).widget().setText("Most Sold")
                        
                        # Card 1: Least Sold Product
                        card1 = lay.itemAt(1).widget()
                        if card1 and card1.layout().count() >= 2:
                            card1.layout().itemAt(0).widget().setText(f"{least_sold_product} ({least_sold_qty})")
                            card1.layout().itemAt(1).widget().setText("Least Sold")
                        
                        # Card 2: Total Products Sold
                        card2 = lay.itemAt(2).widget()
                        if card2 and card2.layout().count() >= 2:
                            card2.layout().itemAt(0).widget().setText(str(total_products_sold))
                            card2.layout().itemAt(1).widget().setText("Total Sold")
                        
                        # Card 3: Total Sales Amount
                        card3 = lay.itemAt(3).widget()
                        if card3 and card3.layout().count() >= 2:
                            card3.layout().itemAt(0).widget().setText(f"Rs {total_sales_amount:,.2f}")
                            card3.layout().itemAt(1).widget().setText("Total Sales")
            except Exception as e:
                print(f"Error updating summary cards: {e}")
            # Generate sales chart and preview
            try:
                dg = DocumentGenerator()
                # Build sales_by_day series from sales
                sales_by_day = {}
                for s in sales_query:
                    key = str(getattr(s, 'sale_date', '').date()) if getattr(s, 'sale_date', None) else ''
                    sales_by_day.setdefault(key, 0.0)
                    amt = float(getattr(s, 'total_amount', 0) or 0)
                    try:
                        if getattr(s, 'is_refund', False):
                            amt = -amt
                    except Exception:
                        pass
                    sales_by_day[key] += amt
                sorted_items = sorted(sales_by_day.items())
                if sorted_items:
                    chart_path = dg.generate_sales_chart(sorted_items)
                    chart_label = self.sales_report.findChild(QLabel, 'chart_label')
                    if chart_label and chart_path:
                        pix = QPixmap(chart_path)
                        if not pix.isNull():
                            chart_label.setPixmap(pix.scaled(chart_label.width(), chart_label.height(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except Exception:
                app_logger.exception('Failed to generate/preview sales chart')
        except Exception:
            app_logger.exception("Failed to generate sales report")
            
    def export_current_report(self):
        try:
            dg = DocumentGenerator()
            # Determine which report is visible
            idx = self.report_stack.currentIndex()
            widget = self.report_stack.currentWidget()
            table = widget.findChild(QTableWidget)
            if table is None:
                return
            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
            rows = []
            for r in range(table.rowCount()):
                row = []
                for c in range(table.columnCount()):
                    item = table.item(r, c)
                    row.append(item.text() if item else '')
                rows.append(row)
            path = dg.export_to_csv(rows, headers)
            try:
                from PySide6.QtWidgets import QMessageBox
            except ImportError:
                from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(self, "Exported", f"CSV exported to: {path}")
        except Exception:
            app_logger.exception("Failed to export current report")

    def export_current_pdf(self):
        try:
            idx = self.report_stack.currentIndex()
            report_type = self.report_type.currentText()
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            if report_type == 'Sales Summary':
                try:
                    start = self.start_date.date().toPython()
                    end = self.end_date.date().toPython()
                except AttributeError:
                    start = self.start_date.date().toPyDate()
                    end = self.end_date.date().toPyDate()
                dg = DocumentGenerator()

                sales = None
                try:
                    if hasattr(controller, 'get_sales_report'):
                        sales = controller.get_sales_report(start, end)
                except Exception:
                    sales = None

                if sales is not None:
                    path = dg.generate_sales_report_pdf(sales)
                    QMessageBox.information(self, 'Exported', f'PDF exported to: {path}')
                    return

                # Fallback: export the currently rendered Sales Summary table as a text report
                try:
                    widget = self.report_stack.currentWidget()
                    table = widget.findChild(QTableWidget) if widget is not None else None
                    if table is None:
                        QMessageBox.information(self, 'Not Available', 'Sales report data not available for PDF export.')
                        return

                    headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]
                    rows = []
                    for r in range(table.rowCount()):
                        row = []
                        for c in range(table.columnCount()):
                            item = table.item(r, c)
                            row.append(item.text() if item else '')
                        rows.append(row)

                    path = dg.export_to_csv(rows, headers)
                    QMessageBox.information(self, 'Exported', f'Exported (fallback CSV) to: {path}')
                except Exception:
                    QMessageBox.information(self, 'Not Available', 'Sales report data not available for PDF export.')
            else:
                QMessageBox.information(self, 'Not Implemented', 'PDF export for this report is not implemented yet.')
        except Exception:
            app_logger.exception('Failed to export PDF for current report')

    def generate_inventory_report(self):
        try:
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            products = controller.get_inventory_report()
            table = self.inventory_report.findChild(QTableWidget)
            if table is None:
                return
            table.setRowCount(len(products))
            for i, p in enumerate(products):
                table.setItem(i, 0, QTableWidgetItem(str(getattr(p, 'id', ''))))
                table.setItem(i, 1, QTableWidgetItem(str(getattr(p, 'name', '') or '')))
                table.setItem(i, 2, QTableWidgetItem(str(getattr(p, 'stock_level', 0) if getattr(p, 'stock_level', None) is not None else 0)))
                rp = getattr(p, 'retail_price', None)
                table.setItem(i, 3, QTableWidgetItem(f"Rs {rp:.2f}" if rp is not None else ""))
                table.setItem(i, 4, QTableWidgetItem(str(getattr(p, 'status', ''))))
        except Exception:
            app_logger.exception("Failed to generate inventory report")

    def generate_customer_report(self, start_date, end_date):
        try:
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            customers = controller.get_customer_report(start_date, end_date)
            table = self.customer_report.findChild(QTableWidget)
            if table is None:
                return
            table.setRowCount(len(customers))
            for i, c in enumerate(customers):
                table.setItem(i, 0, QTableWidgetItem(str(getattr(c, 'name', '') or '')))
                table.setItem(i, 1, QTableWidgetItem(str(getattr(c, 'contact', '') or '')))
                table.setItem(i, 2, QTableWidgetItem(str(getattr(c, 'email', '') or '')))
                table.setItem(i, 3, QTableWidgetItem(str(getattr(c, 'current_credit', 0))))
                table.setItem(i, 4, QTableWidgetItem("") )
        except Exception:
            app_logger.exception("Failed to generate customer report")

    def generate_supplier_report(self, start_date, end_date):
        try:
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            table = self.supplier_report.findChild(QTableWidget)
            if table is None:
                return

            # Configure detailed columns: Date, Supplier, Product, Quantity, Unit Cost, Line Total, Purchase #
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels(["Date", "Supplier", "Product", "Quantity", "Unit Cost", "Line Total", "Purchase #"]) 

            from pos_app.models.database import Purchase, PurchaseItem, Product, Supplier
            q = controller.session.query(
                Purchase.order_date,
                Supplier.name,
                Product.name,
                PurchaseItem.quantity,
                PurchaseItem.unit_cost,
                Purchase.purchase_number
            ).join(Supplier, Supplier.id == Purchase.supplier_id)
            q = q.join(PurchaseItem, PurchaseItem.purchase_id == Purchase.id)
            q = q.join(Product, Product.id == PurchaseItem.product_id)
            q = q.filter(Purchase.order_date.between(start_date, end_date))
            # Optional supplier filter
            sel_sup = self.supplier_filter.currentData()
            if sel_sup:
                q = q.filter(Purchase.supplier_id == sel_sup)
            # Sort by date descending (most recent first)
            q = q.order_by(Purchase.order_date.desc())
            rows = q.all()

            table.setRowCount(len(rows))
            total_qty = 0
            total_amount = 0.0
            for i, (pdate, sname, pname, qty, unit_cost, pnum) in enumerate(rows):
                line_total = float(unit_cost or 0.0) * int(qty or 0)
                total_qty += int(qty or 0)
                total_amount += line_total
                table.setItem(i, 0, QTableWidgetItem(str(pdate.date() if pdate else "")))
                table.setItem(i, 1, QTableWidgetItem(sname or ""))
                table.setItem(i, 2, QTableWidgetItem(pname or ""))
                table.setItem(i, 3, QTableWidgetItem(str(qty or 0)))
                table.setItem(i, 4, QTableWidgetItem(f"Rs {float(unit_cost or 0.0):,.2f}"))
                table.setItem(i, 5, QTableWidgetItem(f"Rs {line_total:,.2f}"))
                table.setItem(i, 6, QTableWidgetItem(pnum or ""))

            # Update summary cards at top of widget
            try:
                # find summary frame and set first two cards values
                summary = self.supplier_report.findChildren(QFrame)[0]
                # dive into its layout
                if hasattr(summary, 'layout'):
                    lay = summary.layout()
                    if lay and lay.count() >= 2:
                        # card 1: total lines
                        card0 = lay.itemAt(0).widget()
                        card1 = lay.itemAt(1).widget()
                        if card0 and card0.layout().count() >= 1:
                            card0.layout().itemAt(0).widget().setText(str(len(rows)))
                            card0.layout().itemAt(1).widget().setText("Lines")
                        if card1 and card1.layout().count() >= 1:
                            card1.layout().itemAt(0).widget().setText(f"Rs {total_amount:,.2f}")
                            card1.layout().itemAt(1).widget().setText("Total Amount")
            except Exception:
                pass
        except Exception:
            app_logger.exception("Failed to generate supplier report")

    def generate_receivables_report(self):
        try:
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            customers = controller.get_receivables_report() if hasattr(controller, 'get_receivables_report') else []
            # Use dedicated receivables_report table
            table = self.receivables_report.findChild(QTableWidget)
            if table is None:
                return
            table.setRowCount(len(customers))
            for i, c in enumerate(customers):
                table.setItem(i, 0, QTableWidgetItem(str(getattr(c, 'name', '') or '')))
                table.setItem(i, 1, QTableWidgetItem(str(getattr(c, 'contact', '') or '')))
                table.setItem(i, 2, QTableWidgetItem(str(getattr(c, 'email', '') or '')))
                bal = float(getattr(c, 'current_credit', 0.0) or 0.0)
                table.setItem(i, 3, QTableWidgetItem(f"Rs {bal:,.2f}"))
                table.setItem(i, 4, QTableWidgetItem("Wholesale" if str(getattr(c, 'type', '')).lower().find('wholesale') >= 0 else ""))
        except Exception:
            app_logger.exception("Failed to generate receivables report")

    def generate_payables_report(self):
        try:
            controller = self.controllers.get('reports') if isinstance(self.controllers, dict) else self.controllers
            suppliers = controller.get_payables_report() if hasattr(controller, 'get_payables_report') else []
            # Use dedicated payables_report table
            table = self.payables_report.findChild(QTableWidget)
            if table is None:
                return
            table.setRowCount(len(suppliers))
            from pos_app.models.database import Purchase
            for i, s in enumerate(suppliers):
                table.setItem(i, 0, QTableWidgetItem(str(getattr(s, 'name', '') or '')))
                table.setItem(i, 1, QTableWidgetItem(str(getattr(s, 'contact', '') or '')))
                table.setItem(i, 2, QTableWidgetItem(str(getattr(s, 'email', '') or '')))
                try:
                    purchases = controller.session.query(Purchase).filter(Purchase.supplier_id == s.id).all()
                    outstanding = sum((p.total_amount or 0.0) - (p.paid_amount or 0.0) for p in purchases)
                    table.setItem(i, 3, QTableWidgetItem(f"Rs {outstanding:,.2f}"))
                except Exception:
                    table.setItem(i, 3, QTableWidgetItem("Rs 0.00"))
                table.setItem(i, 4, QTableWidgetItem(""))
        except Exception:
            app_logger.exception("Failed to generate payables report")
