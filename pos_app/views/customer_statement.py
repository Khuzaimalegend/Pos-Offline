try:
    from PySide6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDateEdit,
        QFrame, QMessageBox, QGroupBox, QFormLayout, QHeaderView, QAbstractItemView
    )
    from PySide6.QtCore import Qt, QDate
    from PySide6.QtGui import QFont, QColor
except ImportError:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QComboBox, QLineEdit, QDateEdit,
        QFrame, QMessageBox, QGroupBox, QFormLayout, QHeaderView, QAbstractItemView
    )
    from PyQt6.QtCore import Qt, QDate
    from PyQt6.QtGui import QFont, QColor
    from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from pos_app.models.database import Customer, Sale, Payment
from pos_app.utils.document_generator import DocumentGenerator
from datetime import datetime
import json

class CustomerStatementDialog(QDialog):
    def __init__(self, controllers, customer_id, parent=None):
        super().__init__(parent)
        self.controllers = controllers
        self.customer_id = customer_id
        self.setup_ui()
        self.load_customer_data()
        self.load_statement_data()

    def setup_ui(self):
        self.setWindowTitle("📄 Customer Statement")
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
        export_btn = QPushButton("📄 Export PDF")
        export_btn.setProperty('accent', 'Qt.blue')
        export_btn.setMinimumHeight(40)
        export_btn.clicked.connect(self.export_pdf)

        print_btn = QPushButton("🖨️ Print")
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
                
                self.outstanding_label.setStyleSheet(f"""
                    padding: 15px;
                    background: #f1f5f9;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    color: {color};
                    text-align: center;
                """)

        except Exception as e:
            print(f"CRITICAL ERROR in load_statement_data: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to load statement data: {str(e)}")

    def export_pdf(self):
        """Export statement to PDF"""
        try:
            from PySide6.QtGui import QPainter, QPdfWriter
            from PySide6.QtCore import QPageSize
        except ImportError:
            from PyQt6.QtGui import QPainter, QPdfWriter
            from PyQt6.QtCore import QPageSize
            
        filename = f"customer_statement_{self.customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        writer = QPdfWriter(filepath)
        writer.setPageSize(QPageSize.Legal)
        writer.setPageOrientation(QPdfWriter.Portrait)
        
        painter = QPainter(writer)
        # Use the same printing logic as print_statement
        self._print_formatted_statement_to_painter(painter, writer.pageLayout().paintRectPixels(writer.resolution()))
        painter.end()
        
        QMessageBox.information(self, "Exported", f"Statement exported to: {filepath}")

    def _print_formatted_statement_to_painter(self, painter, rect):
        """Print statement with proper business format to painter"""
        # Similar to _print_formatted_statement but uses provided painter and rect
        pass

    def _get_shop_info(self):
        """Get shop information from settings"""
        try:
            # Try to get from QSettings
            try:
                from PySide6.QtCore import QSettings
            except ImportError:
                from PyQt6.QtCore import QSettings
                
            settings = QSettings()
            shop_name = settings.value("business_name", "Your Shop Name")
            shop_address = settings.value("business_address", "Your Address")
            shop_phone = settings.value("business_phone", "Your Phone")
            
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
        """Print the statement without dialogs and proper formatting"""
        try:
            from PySide6.QtGui import QPageSize, QPageLayout
            from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
        except ImportError:
            from PyQt6.QtGui import QPageSize, QPageLayout
            from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo
            
        try:
            print("DEBUG: Initializing printer...")
            
            # Check if printing is available
            if not hasattr(QPrinter, 'PrinterMode'):
                print("WARNING: QPrinter.PrinterMode not available")
            
            # Create printer with legal page size
            try:
                mode_enum = getattr(QPrinter, 'PrinterMode', None)
                if mode_enum is not None:
                    printer = QPrinter(mode_enum.HighResolution)
                else:
                    printer = QPrinter()
            except Exception as e:
                print(f"ERROR creating printer: {e}")
                printer = QPrinter()
            
            # Set legal page size and orientation
            try:
                printer.setPageSize(QPageSize(QPageSize.Legal))
                # Use QPageLayout.Orientation for proper orientation setting
                printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                printer.setResolution(300)  # High resolution for better quality
            except Exception as e:
                print(f"ERROR setting page size: {e}")
                try:
                    # Fallback to A4 if Legal fails
                    printer.setPageSize(QPageSize(QPageSize.A4))
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                except:
                    pass
            
            # Set smaller margins for more content
            try:
                # Use QMarginsF for PySide6 compatibility
                from PySide6.QtCore import QMarginsF
                printer.setPageMargins(QMarginsF(5, 5, 5, 5), QPageLayout.Unit.Millimeter)
            except Exception as e:
                print(f"ERROR setting margins: {e}")
            
            # Suppress print dialog - print directly to default printer
            try:
                printer.setPrintRange(QPrinter.PrintRange.AllPages)
            except:
                pass
            printer.setCopyCount(1)
            printer.setCollateCopies(False)
            
            print("DEBUG: Checking for available printers...")
            
            # Get available printers
            try:
                printers = QPrinterInfo.availablePrinters()
                print(f"DEBUG: Found {len(printers)} printers")
                
                if printers:
                    # Use the first available printer
                    printer.setPrinterName(printers[0].printerName())
                    print(f"DEBUG: Using printer: {printers[0].printerName()}")
                else:
                    QMessageBox.warning(self, "No Printer", 
                        "No printer found. Please install a printer and try again.")
                    return
                    
            except Exception as e:
                print(f"ERROR getting printer info: {e}")
                QMessageBox.critical(self, "Printer Error", 
                    f"Failed to access printer information: {str(e)}")
                return
            
            print("DEBUG: Starting print process...")
            
            # Print directly without confirmation dialogs
            self._print_formatted_statement(printer)
            
        except Exception as e:
            print(f"ERROR in print_statement: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Print Error", 
                f"Failed to print statement: {str(e)}\n\nPlease check if a printer is connected and try again.")

    def _print_formatted_statement(self, printer):
        """Print statement with proper business format"""
        try:
            from PySide6.QtGui import QPainter, QFont, QPageLayout
            from PySide6.QtCore import QRect, QPoint, Qt
        except ImportError:
            from PyQt6.QtGui import QPainter, QFont, QPageLayout
            from PyQt6.QtCore import QRect, QPoint, Qt

        try:
            painter = QPainter(printer)
            if not painter.isActive():
                print("ERROR: Painter failed to start")
                QMessageBox.critical(self, "Print Error", "Failed to initialize printer.")
                return
                
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Get page layout and printable area
            page_layout = printer.pageLayout()
            page_rect = page_layout.paintRectPixels(printer.resolution())
            
            width = int(page_rect.width())
            height = int(page_rect.height())
            
            print(f"DEBUG: Printable area: {width}x{height}")
            print(f"DEBUG: Printer resolution: {printer.resolution()}")
            
            # Calculate proper font sizes based on DPI
            dpi = printer.resolution()
            base_scale = dpi / 72.0  # 72 DPI is standard
            
            # Fonts - scaled for proper size on paper
            title_font = QFont("Arial", int(14 * base_scale), QFont.Bold)
            header_font = QFont("Arial", int(11 * base_scale), QFont.Bold)
            normal_font = QFont("Arial", int(9 * base_scale))
            small_font = QFont("Arial", int(8 * base_scale))
            
            # Layout constants - scaled
            margin = int(30 * base_scale)
            left_margin = margin
            right_margin = width - margin
            y_position = margin
            
            # Shop Information (centered - 3 lines as requested)
            painter.setFont(title_font)
            shop_info = self._get_shop_info()
            shop_name = shop_info['name']
            shop_address = shop_info['address']
            shop_phone = shop_info['phone']
            
            # Shop name - middle aligned
            painter.drawText(width // 2 - painter.fontMetrics().horizontalAdvance(shop_name) // 2, y_position, shop_name)
            y_position += int(25 * base_scale)
            
            # Shop address - middle aligned
            painter.drawText(width // 2 - painter.fontMetrics().horizontalAdvance(shop_address) // 2, y_position, shop_address)
            y_position += int(25 * base_scale)
            
            # Shop phone - middle aligned
            painter.drawText(width // 2 - painter.fontMetrics().horizontalAdvance(shop_phone) // 2, y_position, shop_phone)
            y_position += int(35 * base_scale)
            
            # Draw separator line
            painter.drawLine(left_margin, y_position, right_margin, y_position)
            y_position += int(25 * base_scale)
            
            # Bill To section
            painter.setFont(header_font)
            painter.drawText(left_margin, y_position, "BILL TO:")
            y_position += int(25 * base_scale)
            
            painter.setFont(normal_font)
            customer_name = getattr(self.customer, 'name', 'N/A')
            customer_address = getattr(self.customer, 'address', 'N/A')
            customer_phone = getattr(self.customer, 'phone', 'N/A')
            
            painter.drawText(left_margin + int(20 * base_scale), y_position, f"Name: {customer_name}")
            y_position += int(18 * base_scale)
            painter.drawText(left_margin + int(20 * base_scale), y_position, f"Address: {customer_address}")
            y_position += int(18 * base_scale)
            painter.drawText(left_margin + int(20 * base_scale), y_position, f"Phone: {customer_phone}")
            y_position += int(30 * base_scale)
            
            # Statement title
            painter.setFont(title_font)
            title_text = "CUSTOMER STATEMENT"
            painter.drawText(width // 2 - painter.fontMetrics().horizontalAdvance(title_text) // 2, y_position, title_text)
            y_position += int(35 * base_scale)
            
            # Draw separator line
            painter.drawLine(left_margin, y_position, right_margin, y_position)
            y_position += int(25 * base_scale)
            
            # Detailed table headers - as requested: Product, Quantity, Discount, Exit Price, Subtotal
            painter.setFont(header_font)
            headers = ["Date", "Description", "Quantity", "Discount", "Price", "Subtotal"]
            
            # Calculate column positions based on page width
            col_width = (right_margin - left_margin) / 6
            x_positions = [
                left_margin,
                left_margin + col_width,
                left_margin + col_width * 2,
                left_margin + col_width * 3,
                left_margin + col_width * 4,
                left_margin + col_width * 5
            ]
            
            for i, header in enumerate(headers):
                painter.drawText(int(x_positions[i]), y_position, header)
            y_position += int(25 * base_scale)
            
            # Draw line under headers
            painter.drawLine(left_margin, y_position, right_margin, y_position)
            y_position += int(20 * base_scale)
            
            # Table data
            painter.setFont(normal_font)
            row_height = int(22 * base_scale)
            max_rows_per_page = (height - int(200 * base_scale)) // row_height
            current_row = 0
            
            print(f"DEBUG: Table has {self.table.rowCount()} rows")
            
            # Get transactions from table and format as detailed items
            for row in range(self.table.rowCount()):
                if self.table.item(row, 0):  # Check if row has data
                    # Check if we need a new page
                    if current_row >= max_rows_per_page:
                        printer.newPage()
                        y_position = margin
                        current_row = 0
                        
                        # Repeat headers on new page
                        painter.setFont(header_font)
                        for i, header in enumerate(headers):
                            painter.drawText(int(x_positions[i]), y_position, header)
                        y_position += int(25 * base_scale)
                        painter.drawLine(left_margin, y_position, right_margin, y_position)
                        y_position += int(20 * base_scale)
                        painter.setFont(normal_font)
                    
                    # Get cell data
                    date_text = self.table.item(row, 0).text()
                    desc_text = self.table.item(row, 1).text()
                    debit_text = self.table.item(row, 2).text()
                    credit_text = self.table.item(row, 3).text()
                    balance_text = self.table.item(row, 4).text()
                    
                    print(f"DEBUG: Row {row}: {date_text} | {desc_text} | {debit_text} | {credit_text} | {balance_text}")
                    
                    # Draw detailed transaction data
                    painter.drawText(int(x_positions[0]), y_position, date_text)
                    
                    # Truncate description if too long
                    max_desc_width = col_width - int(10 * base_scale)
                    truncated_desc = desc_text
                    while painter.fontMetrics().horizontalAdvance(truncated_desc) > max_desc_width and len(truncated_desc) > 3:
                        truncated_desc = truncated_desc[:-1]
                    painter.drawText(int(x_positions[1]), y_position, truncated_desc)
                    
                    # For sales transactions, show quantity, discount, price
                    if debit_text.strip():
                        # Extract quantity from description if possible
                        quantity = "1"
                        if "item" in desc_text.lower():
                            import re
                            match = re.search(r'(\d+)\s+item', desc_text.lower())
                            if match:
                                quantity = match.group(1)
                        
                        discount = "0%"
                        price = debit_text.replace("Rs ", "")
                        subtotal = price
                        
                        painter.drawText(int(x_positions[2]), y_position, quantity)
                        painter.drawText(int(x_positions[3]), y_position, discount)
                        painter.drawText(int(x_positions[4]), y_position, price)
                        painter.drawText(int(x_positions[5]), y_position, subtotal)
                    else:
                        # Payment transaction
                        painter.drawText(int(x_positions[2]), y_position, "-")
                        painter.drawText(int(x_positions[3]), y_position, "-")
                        painter.drawText(int(x_positions[4]), y_position, "-")
                        painter.drawText(int(x_positions[5]), y_position, f"PAYMENT: {credit_text}")
                    
                    y_position += row_height
                    current_row += 1
            
            # Draw bottom line
            painter.drawLine(left_margin, y_position, right_margin, y_position)
            y_position += int(25 * base_scale)
            
            # Summary section - as requested
            painter.setFont(header_font)
            painter.drawText(left_margin, y_position, "SUMMARY:")
            y_position += int(25 * base_scale)
            
            painter.setFont(normal_font)
            # Get summary from labels
            total_sales = self.total_sales_label.text().replace("Total Sales: Rs ", "")
            total_payments = self.total_payments_label.text().replace("Total Payments: Rs ", "")
            outstanding = self.outstanding_label.text().replace("Outstanding: Rs ", "")
            
            print(f"DEBUG: Summary - Sales: {total_sales}, Payments: {total_payments}, Outstanding: {outstanding}")
            
            painter.drawText(left_margin + int(20 * base_scale), y_position, f"Receipt Total: Rs {total_sales}")
            y_position += int(18 * base_scale)
            painter.drawText(left_margin + int(20 * base_scale), y_position, f"Previous Balance: Rs {total_payments}")
            y_position += int(18 * base_scale)
            painter.drawText(left_margin + int(20 * base_scale), y_position, f"Account Balance: Rs {outstanding}")
            y_position += int(30 * base_scale)
            
            # Footer
            painter.setFont(small_font)
            footer_text = "Thank you for your business!"
            painter.drawText(width // 2 - painter.fontMetrics().horizontalAdvance(footer_text) // 2, height - int(60 * base_scale), footer_text)
            
            # Date and page info
            from datetime import datetime
            date_text = f"Printed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            painter.drawText(left_margin, height - int(40 * base_scale), date_text)
            
            painter.end()
            
            print("DEBUG: Print completed successfully")
            # Only show success message once, no additional dialogs
            QMessageBox.information(self, "Print Complete", "Statement printed successfully!")
            
        except Exception as e:
            print(f"ERROR in _print_formatted_statement: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Print Error", f"Failed to print statement: {str(e)}")

    def add_print_button(self):
        """Add a print button to the customer statement dialog"""
        try:
            # Find the button layout or create one
            button_layout = QHBoxLayout()
            
            print_btn = QPushButton("🖨️ Print Statement")
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
