try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QComboBox, QDoubleSpinBox, QAbstractItemView
    )
    from PySide6.QtCore import Signal, Qt
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QComboBox, QDoubleSpinBox, QAbstractItemView
    )
    from PyQt6.QtCore import pyqtSignal as Signal, Qt
from pos_app.models.database import Customer, CustomerType


class CustomersWidget(QWidget):
    # quick actions
    action_receive_payment = Signal(int)  # customer_id
    action_export_statement = Signal(int)  # customer_id
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        # Ensure clean transaction state
        try:
            self.controller.session.rollback()
        except Exception as e:
            pass
        self.page_size = 12
        self.current_page = 0
        self._customers_cache = []
        self._filtered_customers = None
        self._last_sync_ts = None
        self.setup_ui()
        self.load_customers()
        self._init_sync_timer()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("👥 Customer Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        add_btn = QPushButton("✨ Add New Customer")
        add_btn.setProperty('accent', 'Qt.green')
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self.show_add_customer_dialog)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Action buttons (initially disabled)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 10)
        
        self.edit_customer_btn = QPushButton("✏️ Edit Customer")
        self.edit_customer_btn.setProperty('accent', 'Qt.blue')
        self.edit_customer_btn.setMinimumHeight(36)
        self.edit_customer_btn.setEnabled(False)
        self.edit_customer_btn.clicked.connect(self.edit_selected_customer)
        
        self.delete_customer_btn = QPushButton("🗑️ Delete Customer")
        self.delete_customer_btn.setProperty('accent', 'Qt.red')
        self.delete_customer_btn.setMinimumHeight(36)
        self.delete_customer_btn.setEnabled(False)
        self.delete_customer_btn.clicked.connect(self.delete_selected_customer)
        
        self.receive_payment_btn = QPushButton("💰 Receive Payment")
        self.receive_payment_btn.setProperty('accent', 'Qt.green')
        self.receive_payment_btn.setMinimumHeight(36)
        self.receive_payment_btn.setEnabled(False)
        self.receive_payment_btn.clicked.connect(self.receive_payment_selected)
        
        self.statement_btn = QPushButton("📄 Statement")
        self.statement_btn.setProperty('accent', 'orange')
        self.statement_btn.setMinimumHeight(36)
        self.statement_btn.setEnabled(False)
        self.statement_btn.clicked.connect(self.statement_selected)
        
        self.print_btn = QPushButton("🖨️ Print")
        self.print_btn.setProperty('accent', 'Qt.blue')
        self.print_btn.setMinimumHeight(36)
        self.print_btn.setEnabled(True)
        self.print_btn.clicked.connect(self.print_selected_customer)
        
        actions_layout.addWidget(self.edit_customer_btn)
        actions_layout.addWidget(self.delete_customer_btn)
        actions_layout.addWidget(self.receive_payment_btn)
        actions_layout.addWidget(self.statement_btn)
        actions_layout.addWidget(self.print_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Search + pagination
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search customers...')
        self.search_input.textChanged.connect(self.apply_filter)
        search_layout.addWidget(self.search_input)

        self.prev_btn = QPushButton("Prev")
        self.next_btn = QPushButton("Next")
        self.page_label = QLabel("Page 1")
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        search_layout.addStretch()
        search_layout.addWidget(self.prev_btn)
        search_layout.addWidget(self.page_label)
        search_layout.addWidget(self.next_btn)
        layout.addLayout(search_layout)

        # Customer Table (removed Actions column)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "Type", "Contact", "Email",
            "Credit Limit", "Balance"
        ])
        
        # Table selection
        try:
            self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        except Exception:
            pass
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.selected_customer_id = None
        try:
            from PySide6.QtWidgets import QHeaderView
        except ImportError:
            from PyQt6.QtWidgets import QHeaderView
        
        try:
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.horizontalHeader().setStretchLastSection(True)
            # Remove Actions column sizing
            self.table.verticalHeader().setVisible(False)
            self.table.setWordWrap(True)
        except Exception:
            pass
        try:
            from PySide6.QtCore import Qt
            self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        except Exception:
            pass
        layout.addWidget(self.table)

    def show_add_customer_dialog(self):
        dialog = CustomerDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if not dialog.name_input.text().strip():
                QMessageBox.warning(self, "Validation", "Customer name is required.")
                return
            try:
                self.controller.add_customer(
                    name=dialog.name_input.text().strip(),
                    type=dialog.type_input.currentText().upper(),  # Use string directly
                    contact=dialog.contact_input.text().strip(),
                    email=dialog.email_input.text().strip(),
                    address=dialog.address_input.text().strip(),
                    credit_limit=dialog.credit_limit_input.value()
                )
                QMessageBox.information(self, "Success", "Customer added successfully!")
                self.load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def showEvent(self, event):
        try:
            self.load_customers()
        except Exception:
            pass
        super().showEvent(event)

    def load_customers(self):
        try:
            # Prefer controller method; fallback to direct session query for robustness
            if hasattr(self.controller, 'list_customers'):
                customers = self.controller.list_customers()
            else:
                try:
                    from pos_app.models.database import Customer
                    customers = self.controller.session.query(Customer).all()
                except Exception as qe:
                    print(f"Error querying customers: {qe}")
                    try:
                        self.controller.session.rollback()
                    except Exception as e:
                        pass
                    customers = []
            # cache and show first page
            self._customers_cache = customers
            self.current_page = 0
            self._filtered_customers = None
            self._update_page()
        except Exception as e:
            print(f"Error loading customers: {e}")
            try:
                self.controller.session.rollback()
            except Exception as e:
                pass
            QMessageBox.critical(self, "Error", str(e))

    def apply_filter(self, text):
        try:
            text = (text or "").strip().lower()
            if not hasattr(self, '_customers_cache'):
                return
            filtered = [c for c in self._customers_cache if text in (c.name or '').lower() or text in (c.contact or '').lower()]
            self._filtered_customers = filtered
            self.current_page = 0
            self._update_page()
        except Exception:
            return

    def _update_page(self):
        # Use filtered list only when it is not None; otherwise use full cache
        items = self._customers_cache if (self._filtered_customers is None) else (self._filtered_customers or [])
        start = self.current_page * self.page_size
        page_items = items[start:start + self.page_size]
        self.table.setRowCount(len(page_items))
        for i, c in enumerate(page_items):
            self.table.setItem(i, 0, QTableWidgetItem(c.name or ""))
            self.table.setItem(i, 1, QTableWidgetItem(str(c.type) if c.type else ""))
            self.table.setItem(i, 2, QTableWidgetItem(c.contact or ""))
            self.table.setItem(i, 3, QTableWidgetItem(c.email or ""))
            self.table.setItem(i, 4, QTableWidgetItem(f"{c.credit_limit:.2f}" if c.credit_limit is not None else "0.00"))
            # Balance/outstanding
            try:
                bal = getattr(c, 'current_credit', 0.0) or 0.0
                self.table.setItem(i, 5, QTableWidgetItem(f"{bal:.2f}"))
            except Exception:
                self.table.setItem(i, 5, QTableWidgetItem("0.00"))
            # Store customer ID for selection handling
            item = self.table.item(i, 0)
            if item:
                item.setData(Qt.UserRole, c.id)
            try:
                self.table.setRowHeight(i, 36)
            except Exception:
                pass
        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page+1} / {total_pages}")
    
    def _init_sync_timer(self):
        """Poll sync_state and refresh customers when data changes on other machines."""
        try:
            from PySide6.QtCore import QTimer
        except ImportError:
            from PyQt6.QtCore import QTimer
        
        try:
            self._sync_timer = QTimer(self)
            self._sync_timer.setInterval(5000)  # 5 seconds
            self._sync_timer.timeout.connect(self._check_for_remote_changes)
            self._sync_timer.start()
        except Exception:
            self._sync_timer = None

    def _check_for_remote_changes(self):
        try:
            from pos_app.models.database import get_sync_timestamp
            ts = get_sync_timestamp(self.controller.session, 'customers')
            if ts is None:
                return
            if self._last_sync_ts is None or ts > self._last_sync_ts:
                self._last_sync_ts = ts
                self.load_customers()
        except Exception:
            pass
        
        try:
            total_pages = max(1, (len(self._customers_cache) + self.page_size - 1) // self.page_size)
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled((self.current_page+1) < total_pages)
        except Exception:
            pass

    def on_selection_changed(self):
        """Enable/disable action buttons based on selection"""
        try:
            selected_rows = self.table.selectionModel().selectedRows()
            if selected_rows:
                row = selected_rows[0].row()
                # Get customer ID from the table item
                item = self.table.item(row, 0)
                if item:
                    self.selected_customer_id = item.data(Qt.UserRole)
                    self.edit_customer_btn.setEnabled(True)
                    self.delete_customer_btn.setEnabled(True)
                    self.receive_payment_btn.setEnabled(True)
                    self.statement_btn.setEnabled(True)
                    self.print_btn.setEnabled(True)
                else:
                    self.selected_customer_id = None
                    self.edit_customer_btn.setEnabled(False)
                    self.delete_customer_btn.setEnabled(False)
                    self.receive_payment_btn.setEnabled(False)
                    self.statement_btn.setEnabled(False)
                    self.print_btn.setEnabled(False)
            else:
                self.selected_customer_id = None
                self.edit_customer_btn.setEnabled(False)
                self.delete_customer_btn.setEnabled(False)
                self.receive_payment_btn.setEnabled(False)
                self.statement_btn.setEnabled(False)
                self.print_btn.setEnabled(False)
        except Exception as e:
            print(f"Error in on_selection_changed: {e}")
            # Disable all buttons on error
            try:
                self.edit_customer_btn.setEnabled(False)
                self.delete_customer_btn.setEnabled(False)
                self.receive_payment_btn.setEnabled(False)
                self.statement_btn.setEnabled(False)
                self.print_btn.setEnabled(False)
            except Exception:
                pass

    def edit_selected_customer(self):
        if self.selected_customer_id:
            self._edit_customer(self.selected_customer_id)

    def delete_selected_customer(self):
        if self.selected_customer_id:
            self._delete_customer(self.selected_customer_id)

    def receive_payment_selected(self):
        if self.selected_customer_id:
            self._receive_payment(self.selected_customer_id)

    def statement_selected(self):
        if self.selected_customer_id:
            self._statement(self.selected_customer_id)

    def _delete_customer(self, customer_id):
        res = QMessageBox.question(self, "Confirm", "Delete this customer?", QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            try:
                self.controller.delete_customer(customer_id)
                QMessageBox.information(self, "Deleted", "Customer deleted")
                self.load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _edit_customer(self, customer_id):
        try:
            from pos_app.models.database import Customer
            cust = self.controller.session.get(Customer, customer_id)
            if not cust:
                QMessageBox.warning(self, "Error", "Customer not found")
                return
            dialog = EditCustomerDialog(self, cust)
            if dialog.exec() == QDialog.Accepted:
                self.controller.update_customer(
                    customer_id,
                    name=dialog.name_input.text().strip(),
                    type=dialog.type_input.currentText().upper(),  # Use string directly
                    contact=dialog.contact_input.text().strip(),
                    email=dialog.email_input.text().strip(),
                    address=dialog.address_input.text().strip(),
                    credit_limit=dialog.credit_limit_input.value()
                )
                QMessageBox.information(self, "Success", "Customer updated")
                self.load_customers()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()

    def _next_page(self):
        items = self._customers_cache if (self._filtered_customers is None) else (self._filtered_customers or [])
        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        if (self.current_page+1) < total_pages:
            self.current_page += 1
            self._update_page()

    def _receive_payment(self, customer_id: int):
        # Emit signal for MainWindow to open CustomerPayments page preselected
        try:
            self.action_receive_payment.emit(int(customer_id))
        except Exception:
            pass

    def _statement(self, customer_id: int):
        # Emit signal for MainWindow to export statement
        try:
            self.action_export_statement.emit(int(customer_id))
        except Exception:
            pass
    
    def print_selected_customer(self):
        """Print all customers in table format"""
        try:
            # Show print dialog
            dialog = CustomerPrintDialog(self, None)
            if dialog.exec() == QDialog.Accepted:
                # Get selected printer and print
                printer_name = dialog.get_selected_printer()
                self._do_print_all_customers(printer_name)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print customers: {str(e)}")
    
    def _do_print_all_customers(self, printer_name):
        """Print all customers in table format without dialogs"""
        try:
            from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
            from PySide6.QtGui import QPageSize, QPainter, QFont, QPageLayout
            from PySide6.QtCore import Qt, QMarginsF
        except ImportError:
            from PyQt6.QtPrintSupport import QPrinter, QPrinterInfo
            from PyQt6.QtGui import QPageSize, QPainter, QFont, QPageLayout
            from PyQt6.QtCore import Qt, QMarginsF
        
        try:
            print("DEBUG: Initializing all customers print...")
            
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
            
            # Set legal page size and portrait orientation
            try:
                printer.setPageSize(QPageSize(QPageSize.Legal))
                # Use QPageLayout.Orientation for proper orientation setting
                printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                printer.setResolution(300)
                # Set minimal margins to use full page
                printer.setPageMargins(QMarginsF(2, 2, 2, 2), QPageLayout.Unit.Millimeter)
            except Exception as e:
                print(f"ERROR setting page size: {e}")
                try:
                    # Fallback to A4 if Legal fails
                    printer.setPageSize(QPageSize(QPageSize.A4))
                    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
                    printer.setPageMargins(QMarginsF(2, 2, 2, 2), QPageLayout.Unit.Millimeter)
                except:
                    pass
            
            # Set printer name if specified
            if printer_name and printer_name != "Default":
                printer.setPrinterName(printer_name)
            else:
                # Try to get first available printer
                try:
                    printers = QPrinterInfo.availablePrinters()
                    print(f"DEBUG: Found {len(printers)} printers")
                    
                    if printers:
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
            
            print("DEBUG: Starting all customers print...")
            
            # Create painter and draw content
            painter = QPainter(printer)
            if not painter.isActive():
                print("ERROR: Painter failed to start")
                QMessageBox.critical(self, "Print Error", "Failed to initialize printer. Please check your printer connection.")
                return
                
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Get page dimensions directly from painter device
            width = painter.device().width()
            height = painter.device().height()
            
            print(f"DEBUG: Page dimensions: {width}x{height}")
            print(f"DEBUG: Printer resolution: {printer.resolution()}")
            
            # Calculate DPI scaling factor
            dpi = printer.resolution()
            scale = dpi / 72.0  # 72 DPI is the base
            
            # Use extremely small font sizes (6x smaller than before)
            store_font = QFont("Arial", int(2 * scale), QFont.Bold)
            title_font = QFont("Arial", int(2 * scale), QFont.Bold)
            header_font = QFont("Arial", int(1 * scale), QFont.Bold)
            normal_font = QFont("Arial", int(1 * scale))
            
            # Minimal margins to maximize space
            margin = int(width * 0.005)
            left_margin = margin
            right_margin = width - margin
            y_position = margin
            
            # Store Name
            painter.setFont(store_font)
            store_name = "Sarhad General Store"
            store_width = painter.fontMetrics().horizontalAdvance(store_name)
            painter.drawText(width // 2 - store_width // 2, y_position, store_name)
            y_position += int(5 * scale)
            
            # Title
            painter.setFont(title_font)
            title_text = "CUSTOMER LIST"
            title_width = painter.fontMetrics().horizontalAdvance(title_text)
            painter.drawText(width // 2 - title_width // 2, y_position, title_text)
            y_position += int(6 * scale)
            
            # Table headers - New structure: Invoice ID, Name, Previous Balance, Last Paid, New Balance, Now Paid
            painter.setFont(header_font)
            headers = ["Invoice ID", "Name", "Previous Balance", "Last Paid", "New Balance", "Now Paid"]
            
            # Calculate column positions with proportional widths
            usable_width = right_margin - left_margin
            # Invoice ID: 12%, Name: 25%, Previous Balance: 18%, Last Paid: 15%, New Balance: 15%, Now Paid: 15%
            col_widths = [
                usable_width * 0.12,  # Invoice ID
                usable_width * 0.25,  # Name
                usable_width * 0.18,  # Previous Balance
                usable_width * 0.15,  # Last Paid
                usable_width * 0.15,  # New Balance
                usable_width * 0.15   # Now Paid
            ]
            
            x_positions = [left_margin]
            for i in range(len(col_widths) - 1):
                x_positions.append(x_positions[-1] + col_widths[i])
            
            print(f"DEBUG: Column positions: {x_positions}")
            print(f"DEBUG: Column widths: {col_widths}")
            
            # Draw headers with grid lines
            for i, header in enumerate(headers):
                painter.drawText(int(x_positions[i]), y_position, header)
                # Draw vertical grid lines
                if i < len(headers) - 1:
                    painter.drawLine(int(x_positions[i+1]), y_position - int(2 * scale), int(x_positions[i+1]), y_position + int(4 * scale))
            y_position += int(3 * scale)
            
            # Draw horizontal line under headers
            painter.drawLine(int(left_margin), y_position, int(right_margin), y_position)
            y_position += int(2 * scale)
            
            # Table data with grid lines
            painter.setFont(normal_font)
            row_height = int(3 * scale)
            header_footer_space = int(margin * 2 + 50 * scale)
            max_rows_per_page = (height - header_footer_space) // row_height
            current_row = 0
            
            print(f"DEBUG: Table has {self.table.rowCount()} rows")
            print(f"DEBUG: Max rows per page: {max_rows_per_page}")
            
            for row in range(self.table.rowCount()):
                # Check if we need a new page
                if current_row >= max_rows_per_page:
                    print(f"DEBUG: Starting new page at row {row}")
                    printer.newPage()
                    y_position = margin
                    current_row = 0
                    
                    # Repeat headers on new page
                    painter.setFont(header_font)
                    for i, header in enumerate(headers):
                        painter.drawText(int(x_positions[i]), y_position, header)
                    y_position += 25
                    painter.drawLine(int(left_margin), y_position, int(right_margin), y_position)
                    y_position += 20
                    painter.setFont(normal_font)
                
                # Get customer data
                try:
                    customer_id = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
                    customer_name = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
                    customer_balance = self.table.item(row, 4).text() if self.table.item(row, 4) else "0"
                    
                    print(f"DEBUG: Row {row}: ID={customer_id}, Name={customer_name}, Balance={customer_balance}")
                except Exception as e:
                    print(f"ERROR reading row {row}: {e}")
                    continue
                
                # Draw customer data with proper positioning and truncation
                # Column 1: Invoice ID (customer ID)
                invoice_id_text = customer_id[:10]
                painter.drawText(int(x_positions[0]), y_position, invoice_id_text)
                
                # Column 2: Name - truncate to fit
                max_name_width = col_widths[1] - 5
                truncated_name = customer_name
                while painter.fontMetrics().horizontalAdvance(truncated_name) > max_name_width and len(truncated_name) > 3:
                    truncated_name = truncated_name[:-1]
                painter.drawText(int(x_positions[1]), y_position, truncated_name)
                
                # Column 3: Previous Balance (current balance from table)
                if customer_balance.strip():
                    painter.drawText(int(x_positions[2]), y_position, customer_balance)
                else:
                    painter.drawText(int(x_positions[2]), y_position, "0")
                
                # Column 4: Last Paid (empty for manual entry)
                painter.drawText(int(x_positions[3]), y_position, "_____")
                
                # Column 5: New Balance (empty for manual entry)
                painter.drawText(int(x_positions[4]), y_position, "_____")
                
                # Column 6: Now Paid (empty for manual entry)
                painter.drawText(int(x_positions[5]), y_position, "_____")
                
                # Draw horizontal grid line after each row
                painter.drawLine(int(left_margin), y_position + int(1 * scale), int(right_margin), y_position + int(1 * scale))
                
                # Draw vertical grid lines for each column
                for i in range(1, len(headers)):
                    painter.drawLine(int(x_positions[i]), y_position - int(2 * scale), int(x_positions[i]), y_position + int(1 * scale))
                
                y_position += row_height
                current_row += 1
                
            print(f"DEBUG: Printed {current_row} rows total")
            
            # Footer
            painter.setFont(normal_font)
            from datetime import datetime
            footer_text = f"Printed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Customers: {self.table.rowCount()}"
            painter.drawText(width // 2 - painter.fontMetrics().horizontalAdvance(footer_text) // 2, height - 40, footer_text)
            
            painter.end()
            print("DEBUG: All customers print completed successfully")
            QMessageBox.information(self, "Print Complete", f"Printed {self.table.rowCount()} customers successfully!")
            
        except Exception as e:
            print(f"ERROR in _do_print_all_customers: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Print Error", f"Failed to print customers: {str(e)}")


class CustomerPrintDialog(QDialog):
    def __init__(self, parent=None, customers=None):
        super().__init__(parent)
        self.setWindowTitle("Print Customer List")
        self.setModal(True)
        self.resize(400, 200)
        self.customers = customers
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select Printer")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Printer selection
        self.printer_combo = QComboBox()
        try:
            from PySide6.QtPrintSupport import QPrinterInfo
        except ImportError:
            from PyQt6.QtPrintSupport import QPrinterInfo
            
        printers = QPrinterInfo.availablePrinters()
        self.printer_combo.addItem("Default Printer")
        for printer in printers:
            self.printer_combo.addItem(printer.printerName())
        
        layout.addWidget(self.printer_combo)
        
        # Buttons
        button_layout = QHBoxLayout()
        print_btn = QPushButton("Print")
        print_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(print_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
    
    def get_selected_printer(self):
        index = self.printer_combo.currentIndex()
        if index == 0:
            return "Default"
        else:
            return self.printer_combo.currentText()


class CustomerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Customer")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["Retail", "Wholesale"])
        self.contact_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()
        self.credit_limit_input = QDoubleSpinBox()
        self.credit_limit_input.setMaximum(10000000.00)
        self.credit_limit_input.setDecimals(2)

        layout.addRow("Name:", self.name_input)
        layout.addRow("Type:", self.type_input)
        layout.addRow("Contact:", self.contact_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Address:", self.address_input)
        layout.addRow("Credit Limit:", self.credit_limit_input)

        buttons = QHBoxLayout()
        ok_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)


class EditCustomerDialog(CustomerDialog):
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Customer")
        self.customer = customer
        if customer:
            self.name_input.setText(customer.name or "")
            try:
                customer_type = str(customer.type).title() if customer.type else "Retail"
                self.type_input.setCurrentText(customer_type)
            except Exception:
                pass
            self.contact_input.setText(customer.contact or "")
            self.email_input.setText(customer.email or "")
            self.address_input.setText(customer.address or "")
            self.credit_limit_input.setValue(customer.credit_limit or 0.0)


class CustomerPrintDialog(QDialog):
    """Dialog for selecting printer and print options"""
    def __init__(self, parent=None, customer=None):
        super().__init__(parent)
        self.setWindowTitle("Print Customers")
        self.customer = customer
        self.selected_printer = "Default"
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        # Title
        info_label = QLabel("Print All Customers Report")
        info_label.setStyleSheet("font-weight: bold; color: #60a5fa; font-size: 12px;")
        layout.addRow(info_label)
        
        # Printer selection
        self.printer_combo = QComboBox()
        self.printer_combo.addItem("Default Printer", "Default")
        
        # Try to get available printers
        try:
            from PySide6.QtPrintSupport import QPrinterInfo
        except ImportError:
            from PyQt6.QtPrintSupport import QPrinterInfo
        
        try:
            printers = QPrinterInfo.availablePrinters()
            for printer in printers:
                printer_name = printer.printerName()
                self.printer_combo.addItem(printer_name, printer_name)
        except Exception as e:
            print(f"Could not load printers: {e}")
        
        layout.addRow("Select Printer:", self.printer_combo)
        
        # Paper size info
        paper_info = QLabel("Paper Size: A4 (Landscape)")
        paper_info.setStyleSheet("color: #94a3b8; font-size: 10px;")
        layout.addRow(paper_info)
        
        # Print content info
        content_label = QLabel("Will print table with: Name, Phone, Email, Type, Credit Limit, Balance, Payment (blank for manual entry)")
        content_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        content_label.setWordWrap(True)
        layout.addRow(content_label)
        
        # Buttons
        buttons = QHBoxLayout()
        ok_button = QPushButton("🖨️ Print")
        ok_button.setProperty('accent', 'Qt.green')
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)
    
    def get_selected_printer(self):
        """Get the selected printer name"""
        return self.printer_combo.currentData()
