import os
import html

try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDateEdit,
        QFrame, QMessageBox, QGroupBox, QFormLayout, QHeaderView, QAbstractItemView
    )
    from PySide6.QtPrintSupport import QPrinter, QPrintDialog
    from PySide6.QtGui import QFont, QColor, QPageSize, QPageLayout, QTextDocument
    from PySide6.QtCore import Qt, QDate, QRect, QSizeF, QMarginsF
    qt_version = "PySide6"
except ImportError:
    try:
        from PyQt6.QtWidgets import (
            QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDateEdit,
            QFrame, QMessageBox, QGroupBox, QFormLayout, QHeaderView, QAbstractItemView
        )
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt6.QtGui import QFont, QColor, QPageSize, QPageLayout, QTextDocument
        from PyQt6.QtCore import Qt, QDate, QRect, QSizeF, QMarginsF
        qt_version = "PyQt6"
    except ImportError:
        raise ImportError("Neither PySide6 nor PyQt6 is available. Please install one of them.")
from pos_app.models.database import Customer, Sale, Payment
from datetime import datetime, time
import json

class CustomerStatementDialog(QDialog):
    def __init__(self, controllers, customer_id, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.customer_id = customer_id
        self.output_dir = os.path.join(os.getcwd(), "documents")
        os.makedirs(self.output_dir, exist_ok=True)
        self.setup_ui()
        self.load_customer_data()
        self.load_statement_data()

    def setup_ui(self):
        self.setWindowTitle("Customer Statement")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header with customer info
        header_layout = QHBoxLayout()

        self.customer_info_label = QLabel("Customer: Loading...")
        self.customer_info_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1e293b;
            padding: 10px;
            background: #f8fafc;
            border-radius: 8px;
            border: 2px solid #e2e8f0;
        """)
        header_layout.addWidget(self.customer_info_label)

        # Export buttons
        export_btn = QPushButton("Export PDF")
        export_btn.setProperty('accent', 'Qt.blue')
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.export_pdf)

        print_btn = QPushButton("Print")
        print_btn.setProperty('accent', 'Qt.green')
        print_btn.setMinimumHeight(40)
        print_btn.clicked.connect(self.print_statement)

        header_layout.addStretch()
        header_layout.addWidget(export_btn)
        header_layout.addWidget(print_btn)

        layout.addLayout(header_layout)

        # Filters
        filters_group = QGroupBox("Filters")
        filters_layout = QHBoxLayout(filters_group)

        filters_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.setCalendarPopup(True)
        filters_layout.addWidget(self.start_date)

        filters_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        filters_layout.addWidget(self.end_date)

        self.transaction_type = QComboBox()
        self.transaction_type.addItems(["All", "Sales", "Payments"])
        filters_layout.addWidget(QLabel("Type:"))
        filters_layout.addWidget(self.transaction_type)

        filter_btn = QPushButton("🔍 Filter")
        filter_btn.clicked.connect(self.load_statement_data)
        filters_layout.addWidget(filter_btn)

        layout.addWidget(filters_group)

        # Summary cards
        summary_layout = QHBoxLayout()

        self.total_sales_label = QLabel("Total Sales: Rs 0.00")
        self.total_payments_label = QLabel("Total Payments: Rs 0.00")
        self.outstanding_label = QLabel("Outstanding: Rs 0.00")

        for label in [self.total_sales_label, self.total_payments_label, self.outstanding_label]:
            label.setStyleSheet("""
                padding: 15px;
                background: #f1f5f9;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                color: #334155;
                text-align: center;
            """)
            summary_layout.addWidget(label)

        layout.addLayout(summary_layout)

        # Statement table
        table_group = QGroupBox("Transaction History")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(5)  # Fixed: Only 5 columns needed
        self.table.setHorizontalHeaderLabels([
            "Date", "Description", "Debit", "Credit", "Balance"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Date
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Description
        header.resizeSection(0, 120)
        header.resizeSection(1, 200)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)

        table_layout.addWidget(self.table)
        layout.addWidget(table_group)

        # Action buttons
        buttons_layout = QHBoxLayout()

        close_btn = QPushButton("❌ Close")
        close_btn.setProperty('accent', 'Qt.red')
        close_btn.clicked.connect(self.reject)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setProperty('accent', 'Qt.blue')
        refresh_btn.clicked.connect(self.load_statement_data)

        buttons_layout.addWidget(refresh_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)

    def load_customer_data(self):
        """Load customer information"""
        try:
            customer = self.controllers['customers'].session.get(Customer, self.customer_id)
            if customer:
                self.customer_info_label.setText(f"Customer: {customer.name} (ID: {customer.id})")
            else:
                self.customer_info_label.setText("Customer not found")
        except Exception as e:
            self.customer_info_label.setText(f"Error loading customer: {str(e)}")

    def load_statement_data(self):
        """Load customer statement data"""
        try:
            print("DEBUG: Starting to load statement data...")
            
            # Convert QDate to Python date (compatible with both PyQt6 and PySide6)
            try:
                start_date = self.start_date.date().toPython()
            except AttributeError:
                # PyQt6 doesn't have toPython(), use toString() and parse
                start_date_str = self.start_date.date().toString("yyyy-MM-dd")
                from datetime import datetime
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            
            try:
                end_date = self.end_date.date().toPython()
            except AttributeError:
                # PyQt6 doesn't have toPython(), use toString() and parse
                end_date_str = self.end_date.date().toString("yyyy-MM-dd")
                from datetime import datetime
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            trans_type = self.transaction_type.currentText()
            print(f"DEBUG: Date range: {start_date} to {end_date}, Type: {trans_type}")

            # Get customer data first
            customer = self.controllers['customers'].session.get(Customer, self.customer_id)
            if not customer:
                print(f"ERROR: Customer {self.customer_id} not found!")
                QMessageBox.warning(self, "Error", "Customer not found!")
                return
            
            print(f"DEBUG: Found customer: {customer.name}")
            self.customer = customer  # Store for printing

            # Get sales for this customer (with item names)
            sales = []
            if trans_type in ["All", "Sales"]:
                try:
                    # Use direct session query for better control
                    sales = self.controllers['customers'].session.query(Sale).filter(
                        Sale.customer_id == self.customer_id,
                        Sale.sale_date >= start_date,
                        Sale.sale_date <= end_date
                    ).order_by(Sale.sale_date.desc()).all()  # Most recent first
                    
                    print(f"DEBUG: Found {len(sales)} sales for customer {self.customer_id}")
                    
                    # Debug: Print first sale details
                    if sales:
                        first_sale = sales[0]
                        print(f"DEBUG: First sale - ID: {first_sale.id}, Date: {first_sale.sale_date}, Total: {first_sale.total_amount}")
                        
                except Exception as e:
                    print(f"ERROR loading sales: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        self.controllers['customers'].session.rollback()
                    except Exception:
                        pass
                    sales = []

            # Get payments for this customer
            payments = []
            if trans_type in ["All", "Payments"]:
                try:
                    # Use direct session query for better control
                    payments = self.controllers['customers'].session.query(Payment).filter(
                        Payment.customer_id == self.customer_id,
                        Payment.payment_date >= start_date,
                        Payment.payment_date <= end_date
                    ).order_by(Payment.payment_date.desc()).all()  # Most recent first
                    
                    print(f"DEBUG: Found {len(payments)} payments for customer {self.customer_id}")
                    
                    # Debug: Print first payment details
                    if payments:
                        first_payment = payments[0]
                        print(f"DEBUG: First payment - ID: {first_payment.id}, Date: {first_payment.payment_date}, Amount: {first_payment.amount}")
                        
                except Exception as e:
                    print(f"ERROR loading payments: {e}")
                    import traceback
                    traceback.print_exc()
                    try:
                        self.controllers['customers'].session.rollback()
                    except Exception:
                        pass
                    payments = []

            # Combine and sort transactions
            transactions = []

            # Add sales as debit transactions with product names
            for sale in sales:
                try:
                    items = list(getattr(sale, 'items', []) or [])
                    if items:
                        names = []
                        for it in items:
                            try:
                                product_name = getattr(getattr(it, 'product', None), 'name', '')
                                if product_name:
                                    names.append(product_name)
                            except Exception:
                                pass
                        names_str = ", ".join(names) if names else f"{len(items)} item(s)"
                    else:
                        names_str = "Sale Items"
                except Exception:
                    names_str = "Sale Items"
                
                sale_amount = getattr(sale, 'total_amount', 0) or 0
                invoice_num = getattr(sale, 'invoice_number', f"INV-{sale.id}")
                
                transactions.append({
                    'date': sale.sale_date,
                    'type': 'Sale',
                    'description': f"{names_str} ({invoice_num})",
                    'debit': sale_amount,
                    'credit': 0,
                    'reference': sale.id
                })
                print(f"DEBUG: Added sale transaction: {sale.sale_date} - {names_str} - Rs {sale_amount}")

            # Add payments as credit transactions
            for payment in payments:
                try:
                    pm = getattr(payment, 'payment_method', None)
                    pm_text = str(pm) if pm is not None else 'N/A'
                except Exception:
                    pm_text = 'N/A'
                
                payment_amount = getattr(payment, 'amount', 0) or 0
                
                transactions.append({
                    'date': payment.payment_date,
                    'type': 'Payment',
                    'description': f"Payment - {pm_text}",
                    'debit': 0,
                    'credit': payment_amount,
                    'reference': payment.id
                })
                print(f"DEBUG: Added payment transaction: {payment.payment_date} - {pm_text} - Rs {payment_amount}")

            # Sort by date (most recent first)
            transactions.sort(key=lambda x: x['date'], reverse=True)

            # Calculate running balance
            balance = 0.0
            for trans in transactions:
                balance += trans['credit'] - trans['debit']
                trans['balance'] = balance

            print(f"DEBUG: Total transactions to display: {len(transactions)}")

            # Update table
            self.table.setRowCount(len(transactions))

            if not transactions:
                print("DEBUG: No transactions found - showing empty message")
                # Show a message when no transactions found
                self.table.setRowCount(1)
                self.table.setSpan(0, 0, 1, 5)  # Span all columns
                no_data_item = QTableWidgetItem("No transactions found for the selected period")
                no_data_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(0, 0, no_data_item)
                
                # Clear summary
                self.total_sales_label.setText("Total Sales: Rs 0.00")
                self.total_payments_label.setText("Total Payments: Rs 0.00")
                self.outstanding_label.setText("Outstanding: Rs 0.00")
                self.outstanding_label.setStyleSheet("""
                    padding: 15px;
                    background: #f1f5f9;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    color: #000000;
                    text-align: center;
                """)
            else:
                print(f"DEBUG: Populating table with {len(transactions)} transactions")
                # Fill table with transaction data
                for row, trans in enumerate(transactions):
                    # Date
                    date_item = QTableWidgetItem(trans['date'].strftime('%Y-%m-%d'))
                    date_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, 0, date_item)
                    
                    # Description
                    desc_item = QTableWidgetItem(trans['description'])
                    self.table.setItem(row, 1, desc_item)
                    
                    # Debit - only show if > 0
                    debit_text = f"Rs {trans['debit']:.2f}" if trans['debit'] > 0 else ""
                    debit_item = QTableWidgetItem(debit_text)
                    debit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, 2, debit_item)
                    
                    # Credit - only show if > 0
                    credit_text = f"Rs {trans['credit']:.2f}" if trans['credit'] > 0 else ""
                    credit_item = QTableWidgetItem(credit_text)
                    credit_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(row, 3, credit_item)
                    
                    # Balance - always show
                    balance_item = QTableWidgetItem(f"Rs {trans['balance']:.2f}")
                    balance_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    if trans['balance'] < 0:
                        balance_item.setBackground(QColor('#fee2e2'))  # Light red for negative
                    self.table.setItem(row, 4, balance_item)
                
                # Calculate totals
                total_sales = sum(t['debit'] for t in transactions if t['type'] == 'Sale')
                total_payments = sum(t['credit'] for t in transactions if t['type'] == 'Payment')
                outstanding_balance = balance
                
                print(f"DEBUG: Totals - Sales: Rs {total_sales}, Payments: Rs {total_payments}, Balance: Rs {outstanding_balance}")
                
                # Update summary labels
                self.total_sales_label.setText(f"Total Sales: Rs {total_sales:.2f}")
                self.total_payments_label.setText(f"Total Payments: Rs {total_payments:.2f}")
                self.outstanding_label.setText(f"Outstanding: Rs {outstanding_balance:.2f}")
                
                # Style outstanding label based on balance
                if outstanding_balance > 0:
                    color = '#dc2626'  # Red for customer owes money
                elif outstanding_balance < 0:
                    color = '#16a34a'  # Green for customer has credit
                else:
                    color = '#000000'  # Black for balanced
                
        except Exception as e:
            print(f"CRITICAL ERROR in load_statement_data: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load statement data: {str(e)}")

    def export_pdf(self):
        """Export statement to PDF using HTML rendering"""
        filename = f"customer_statement_{self.customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setResolution(300)
        printer.setPageMargins(QMarginsF(12.7, 12.7, 12.7, 18), QPageLayout.Unit.Millimeter)

        html_content = self._build_statement_html()
        self._print_html_document(printer, html_content)

        QMessageBox.information(self, "Exported", f"Statement exported to: {filepath}")

    def _build_statement_html(self):
        start_date, end_date = self._get_selected_dates()
        data = self._gather_statement_data(start_date, end_date)
        shop_info = self._get_shop_info()
        customer_name = getattr(self.customer, "name", "N/A") if getattr(self, "customer", None) else "N/A"
        customer_address = getattr(self.customer, "address", "N/A") if getattr(self, "customer", None) else "N/A"
        customer_phone = getattr(self.customer, "phone", "N/A") if getattr(self, "customer", None) else "N/A"
        period_text = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        generated_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def esc(value):
            return html.escape(str(value) if value is not None else "")

        rows_html = []
        combined_rows = data["sale_rows"] + data["payment_rows"]
        if not combined_rows:
            rows_html.append(
                "<tr><td colspan='6' class='empty'>No transactions found for the selected period.</td></tr>"
            )
        else:
            for row in combined_rows:
                rows_html.append(
                    "<tr>"
                    f"<td>{esc(row['date'])}</td>"
                    f"<td>{esc(row['description'])}</td>"
                    f"<td class='numeric'>{esc(row['quantity'])}</td>"
                    f"<td class='numeric'>{esc(row['discount'])}</td>"
                    f"<td class='numeric'>{esc(row['price'])}</td>"
                    f"<td class='numeric'>{esc(row['subtotal'])}</td>"
                    "</tr>"
                )

        summary_cards = [
            ("Total Sales", self._format_currency(data["total_sales"])),
            ("Total Payments", self._format_currency(data["total_payments"])),
            ("Balance", self._format_currency(data["balance"])),
        ]
        summary_html = "".join(
            f"<div class='summary-card'><div class='label'>{esc(label)}</div>"
            f"<div class='value'>{esc(value)}</div></div>"
            for label, value in summary_cards
        )

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <style>
        @page {{
            margin: 18mm;
        }}
        body {{
            font-family: 'Segoe UI', 'Arial', sans-serif;
            margin: 0;
            padding: 1rem 1.5rem 1.5rem 1.5rem;
            color: #0f172a;
            background: #ffffff;
            font-size: 10px;
            line-height: 1.2;
        }}
        .header {{
            text-align: center;
            margin-bottom: 0.8rem;
        }}
        .header h1 {{
            margin: 0;
            font-size: 1.8em;
            letter-spacing: 0.12em;
        }}
        .header p {{
            margin: 0.2rem 0;
            color: #475569;
            font-size: 1.1em;
        }}
        .bill-to {{
            margin-top: 1rem;
            padding: 0.8rem;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            background: #f8fafc;
        }}
        .bill-to h2 {{
            margin: 0 0 0.5rem 0;
            font-size: 1.1em;
            color: #475569;
            letter-spacing: 0.08em;
        }}
        .summary-section {{
            margin-top: 1rem;
        }}
        .summary-card {{
            display: inline-block;
            min-width: 120px;
            margin-right: 1rem;
            margin-bottom: 0.5rem;
            padding: 0.7rem 0.8rem;
            border-radius: 4px;
            background: linear-gradient(135deg, #eef2ff, #eff6ff);
            border: 1px solid #dbeafe;
        }}
        .summary-card .label {{
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 0.12em;
            color: #6366f1;
            margin-bottom: 0.3rem;
        }}
        .summary-card .value {{
            font-size: 1.2em;
            font-weight: 700;
        }}
        table {{
            width: 95%;
            max-width: 1400px;
            border-collapse: collapse;
            margin: 2rem auto 1.5rem auto;
            table-layout: fixed;
            font-size: 1.4rem;
            border: 3px solid #1e293b;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        th {{
            text-align: center;
            padding: 2rem 2rem;
            background: #000000 !important;
            color: #ffffff !important;
            font-size: 1.6rem !important;
            font-weight: 900 !important;
            border: 3px solid #ffffff !important;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.8);
            height: 60px !important;
            line-height: 1.2;
        }}
        td {{
            padding: 1.2rem 1.8rem;
            border: 2px solid #e2e8f0;
            font-size: 1.2rem;
            color: #0f172a;
            vertical-align: middle;
            text-align: center;
            background: #ffffff;
            font-weight: 500;
        }}
        td.numeric {{
            text-align: right;
            font-variant-numeric: tabular-nums;
        }}
        tr:nth-child(even) td {{
            background-color: #f8fafc;
        }}
        tr {{
            min-height: 2rem;
        }}
        .section-title {{
            margin-top: 1.2rem;
            font-size: 0.9rem;
            letter-spacing: 0.22em;
            color: #94a3b8;
        }}
        .footer {{
            margin-top: 1rem;
            text-align: center;
            font-size: 0.8rem;
            color: #94a3b8;
        }}
        .empty {{
            text-align: center;
            padding: 1.5rem 0;
            color: #94a3b8;
            font-size: 1rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <p class="section-title">CUSTOMER STATEMENT</p>
        <h1>{esc(shop_info['name'])}</h1>
        <p>{esc(shop_info['address'])}</p>
        <p>Contact: {esc(shop_info['phone'])}</p>
        <p>Statement Period: {esc(period_text)}</p>
    </div>

    <div class="bill-to">
        <h2>BILL TO</h2>
        <p><strong>Name:</strong> {esc(customer_name)}</p>
        <p><strong>Address:</strong> {esc(customer_address)}</p>
        <p><strong>Phone:</strong> {esc(customer_phone)}</p>
    </div>

    <table style="border-collapse: collapse; width: 95%; margin: 2rem auto; table-layout: fixed;">
        <thead style="display: table-header-group;">
            <tr>
                <th style="text-align: center; padding: 4px 6px; background: #ffffff; color: #000000; font-size: 8px; font-weight: bold; border: 2px solid #000000; white-space: nowrap;">DATE</th>
                <th style="text-align: center; padding: 4px 6px; background: #ffffff; color: #000000; font-size: 8px; font-weight: bold; border: 2px solid #000000; white-space: nowrap;">DESCRIPTION</th>
                <th style="text-align: center; padding: 4px 6px; background: #ffffff; color: #000000; font-size: 8px; font-weight: bold; border: 2px solid #000000; white-space: nowrap;">QTY</th>
                <th style="text-align: center; padding: 4px 6px; background: #ffffff; color: #000000; font-size: 8px; font-weight: bold; border: 2px solid #000000; white-space: nowrap;">DISCOUNT</th>
                <th style="text-align: center; padding: 4px 6px; background: #ffffff; color: #000000; font-size: 8px; font-weight: bold; border: 2px solid #000000; white-space: nowrap;">PRICE</th>
                <th style="text-align: center; padding: 4px 6px; background: #ffffff; color: #000000; font-size: 8px; font-weight: bold; border: 2px solid #000000; white-space: nowrap;">SUBTOTAL</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows_html)}
        </tbody>
        <tfoot>
            <tr style="background: linear-gradient(135deg, #f1f5f9, #e2e8f0); border-top: 3px solid #1e293b;">
                <td colspan="5" style="text-align: right; font-weight: 700; font-size: 1.1rem; padding: 0.5rem 1rem;">TOTAL OF THAT SALE:</td>
                <td style="text-align: center; font-weight: 800; font-size: 1.2rem; color: #1e293b; padding: 0.5rem 1rem;">{self._format_currency(data["total_sales"])}</td>
            </tr>
            <tr style="background: linear-gradient(135deg, #e8f4f8, #d1ecf1); border-top: 2px solid #0c4a6e;">
                <td colspan="5" style="text-align: right; font-weight: 700; font-size: 1.1rem; padding: 0.5rem 1rem;">TOTAL PAID:</td>
                <td style="text-align: center; font-weight: 800; font-size: 1.2rem; color: #0c4a6e; padding: 0.5rem 1rem;">{self._format_currency(data["total_payments"])}</td>
            </tr>
            <tr style="background: linear-gradient(135deg, #fef2f2, #fee2e2); border-top: 2px solid #dc2626;">
                <td colspan="5" style="text-align: right; font-weight: 700; font-size: 1.1rem; padding: 0.5rem 1rem;">AMOUNT DUE:</td>
                <td style="text-align: center; font-weight: 800; font-size: 1.2rem; color: #dc2626; padding: 0.5rem 1rem;">{self._format_currency(data["balance"])}</td>
            </tr>
        </tfoot>
    </table>

    <div class="footer">
        <p>Generated on {esc(generated_text)}</p>
        <p>Thank you for your business!</p>
    </div>
</body>
</html>
"""
        return html_content

    def _gather_statement_data(self, start_date, end_date):
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        session = self.controllers['customers'].session

        sales = session.query(Sale).filter(
            Sale.customer_id == self.customer_id,
            Sale.sale_date >= start_dt,
            Sale.sale_date <= end_dt
        ).order_by(Sale.sale_date.desc()).all()

        sale_rows = []
        if sales:
            # Only show the last/most recent sale
            latest_sale = sales[0]
            sale_date_text = latest_sale.sale_date.strftime('%Y-%m-%d') if latest_sale.sale_date else ""
            items = list(getattr(latest_sale, 'items', []) or [])
            if not items:
                subtotal = getattr(latest_sale, 'total_amount', 0) or 0
                sale_rows.append({
                    "date": sale_date_text,
                    "description": "Sale Items",
                    "quantity": str(getattr(latest_sale, 'total_quantity', 1) or 1),
                    "discount": "-",
                    "price": self._format_currency(subtotal),
                    "subtotal": self._format_currency(subtotal)
                })
            else:
                for idx, item in enumerate(items):
                    product = getattr(item, 'product', None)
                    product_name = getattr(product, 'name', 'Unknown Item') if product else 'Unknown Item'
                    quantity = getattr(item, 'quantity', 1) or 1
                    discount = getattr(item, 'discount', 0)
                    price = getattr(item, 'unit_price', getattr(item, 'price', 0)) or 0
                    subtotal = getattr(item, 'subtotal', getattr(item, 'total', price * quantity)) or (price * quantity)
                    if isinstance(discount, (int, float)):
                        discount_text = f"{discount:.1f}%"
                    else:
                        discount_text = str(discount or "-")
                    sale_rows.append({
                        "date": sale_date_text if idx == 0 else "",
                        "description": product_name,
                        "quantity": str(quantity),
                        "discount": discount_text,
                        "price": self._format_currency(price),
                        "subtotal": self._format_currency(subtotal)
                    })

        # Calculate totals properly
        total_sales = sum(getattr(sale, 'total_amount', 0) or 0 for sale in sales)
        
        # Get all payments made by this customer in the date range
        payments = session.query(Payment).filter(
            Payment.customer_id == self.customer_id,
            Payment.payment_date >= start_dt,
            Payment.payment_date <= end_dt,
            Payment.status == 'COMPLETED'
        ).all()
        
        total_payments = sum(getattr(payment, 'amount', 0) or 0 for payment in payments)
        
        # Amount due = total sales - total payments
        balance = total_sales - total_payments

        return {
            "sale_rows": sale_rows,
            "payment_rows": [],  # Empty payment rows
            "total_sales": total_sales,
            "total_payments": total_payments,
            "balance": balance
        }

    def _print_html_document(self, printer, html_content):
        document = QTextDocument()
        document.setDocumentMargin(24)
        document.setDefaultFont(QFont("Segoe UI", 9))
        document.setHtml(html_content)

        try:
            page_rect = printer.pageRect(QPrinter.Point)
            document.setPageSize(QSizeF(page_rect.width(), page_rect.height()))
        except Exception:
            pass

        if hasattr(document, "print"):
            document.print(printer)
        else:
            document.print_(printer)

    def _get_selected_dates(self):
        def to_py_date(qdate):
            try:
                return qdate.toPython()
            except AttributeError:
                return datetime.strptime(qdate.toString("yyyy-MM-dd"), "%Y-%m-%d").date()

        return to_py_date(self.start_date.date()), to_py_date(self.end_date.date())

    def _format_currency(self, value):
        try:
            return f"Rs {float(value):,.2f}"
        except Exception:
            return f"Rs {value}"

    def _get_shop_info(self):
        """Get shop information from settings"""
        try:
            try:
                from PySide6.QtCore import QSettings
            except ImportError:
                from PyQt6.QtCore import QSettings

            settings = QSettings()
            shop_name = settings.value("business_name", "Sarhad General Store")
            shop_address = settings.value("business_address", "Madni Chowk")
            shop_phone = settings.value("business_phone", "+923225031977")

            return {
                'name': shop_name,
                'address': shop_address,
                'phone': shop_phone
            }
        except Exception:
            # Fallback values
            return {
                'name': "Your Shop Name",
                'address': "Your Address",
                'phone': "Your Phone"
            }

    def print_statement(self):
        """Print customer statement with proper formatting and printer selection"""
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrintDialog
            from PySide6.QtGui import QPageSize, QPageLayout
        except ImportError:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
            from PyQt6.QtGui import QPageSize, QPageLayout

        # Create printer
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        printer.setResolution(300)

        # Show printer selection dialog
        dialog = QPrintDialog(printer, self)
        dialog.setWindowTitle("Print Customer Statement")
        if dialog.exec() != QPrintDialog.Accepted:
            return

        html_content = self._build_statement_html()
        self._print_html_document(printer, html_content)

    def add_print_button(self):
        """Add a print button to the customer statement dialog"""
        try:
            # Find the button layout or create one
            button_layout = QHBoxLayout()
            
            print_btn = QPushButton("Print Statement")
            print_btn.clicked.connect(self.print_statement)
            print_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2563eb;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #1d4ed8;
                }
                QPushButton:pressed {
                    background-color: #1e40af;
                }
            """)
            
            button_layout.addWidget(print_btn)
            button_layout.addStretch()
            
            # Add to main layout
            self.layout().addLayout(button_layout)
            
        except Exception as e:
            print(f"Error adding print button: {e}")
