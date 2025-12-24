"""
Universal Barcode Search Widget
Provides barcode scanning and product search functionality for all modules
"""
try:
    from PySide6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel,
        QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
        QMessageBox, QFrame, QComboBox, QAbstractItemView
    )
    from PySide6.QtCore import Qt, Signal, QTimer
    from PySide6.QtGui import QFont, QKeySequence, QShortcut
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QPushButton, QLabel,
        QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox,
        QMessageBox, QFrame, QComboBox, QAbstractItemView
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal, QTimer
    from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from pos_app.models.database import Product
from pos_app.utils.logger import app_logger
from pos_app.utils.barcode_validator import validate_barcode_input, is_valid_barcode


class BarcodeSearchWidget(QWidget):
    """Universal barcode search widget for product selection"""
    
    # Signals
    product_selected = Signal(object)  # Emits Product object
    product_added = Signal(object, int)  # Emits Product object and quantity
    
    def __init__(self, session, parent=None, show_quantity=False, auto_add=False):
        super().__init__(parent)
        self.session = session
        self.show_quantity = show_quantity
        self.auto_add = auto_add
        self.is_search_mode = False  # False = barcode mode, True = search mode
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Search frame
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background: #1e293b;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        
        search_layout = QHBoxLayout(search_frame)
        search_layout.setContentsMargins(8, 8, 8, 8)
        search_layout.setSpacing(8)
        
        # Barcode/Search input
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #334155;
                border-radius: 6px;
                padding: 10px 12px;
                font-size: 14px;
                background: #0f172a;
                color: #f8fafc;
                font-weight: 500;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                background: #1e293b;
            }
        """)
        self.search_input.returnPressed.connect(self._on_search)
        
        # Mode toggle button
        self.mode_btn = QPushButton("🔍 Search")
        self.mode_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3b82f6, stop:1 #2563eb);
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 600;
                color: Qt.white;
                min-width: 80px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2563eb, stop:1 #1d4ed8);
            }
        """)
        self.mode_btn.clicked.connect(self.toggle_mode)
        self.mode_btn.setToolTip("Toggle between Barcode and Search mode (F2)")
        
        # Quantity input (optional)
        if self.show_quantity:
            qty_label = QLabel("Qty:")
            qty_label.setStyleSheet("color: #94a3b8; font-weight: 600;")
            self.quantity_input = QLineEdit("1")
            self.quantity_input.setMaximumWidth(60)
            self.quantity_input.setStyleSheet("""
                QLineEdit {
                    border: 2px solid #334155;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 14px;
                    background: #0f172a;
                    color: #f8fafc;
                    text-align: center;
                }
            """)
            search_layout.addWidget(qty_label)
            search_layout.addWidget(self.quantity_input)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.mode_btn)
        
        layout.addWidget(search_frame)
        
        # Keyboard shortcuts
        self.shortcut_f2 = QShortcut(QKeySequence("F2"), self)
        self.shortcut_f2.activated.connect(self.toggle_mode)
        
        # Auto-search timer for barcode scanners
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(300)  # 300ms delay
        self._search_timer.timeout.connect(self._on_search)
        self.search_input.textChanged.connect(self._on_text_changed)
        
        # Set initial mode UI
        self._set_mode_ui()
        
    def _set_mode_ui(self):
        """Update UI based on current mode"""
        if self.is_search_mode:
            self.search_input.setPlaceholderText("🔍 Search products by name, SKU, or barcode...")
            self.mode_btn.setText("📊 Barcode")
            self.mode_btn.setToolTip("Switch to Barcode mode")
        else:
            self.search_input.setPlaceholderText("📊 Scan or enter barcode/SKU...")
            self.mode_btn.setText("🔍 Search")
            self.mode_btn.setToolTip("Switch to Search mode")
            
    def toggle_mode(self):
        """Toggle between barcode and search mode"""
        self.is_search_mode = not self.is_search_mode
        self._set_mode_ui()
        self.search_input.clear()
        self.search_input.setFocus()
        
    def _on_text_changed(self, text):
        """Handle text changes for auto-search"""
        if not self.is_search_mode and len(text.strip()) >= 3:
            # Auto-search for barcodes after short delay
            self._search_timer.stop()
            self._search_timer.start()
            
    def _on_search(self):
        """Handle search/barcode lookup"""
        term = self.search_input.text().strip()
        if not term:
            return
            
        try:
            if not self.is_search_mode:
                # Barcode mode: validate and clean barcode first
                validation_result = validate_barcode_input(term)
                
                if validation_result['is_valid']:
                    # Use cleaned barcode for search
                    cleaned_barcode = validation_result['cleaned_barcode']
                    product = self._find_by_barcode(cleaned_barcode)
                    if product:
                        self._handle_product_found(product)
                        return
                else:
                    # Show validation error for invalid barcodes
                    QMessageBox.warning(
                        self,
                        "Invalid Barcode",
                        f"Invalid barcode format: {term}\n\n"
                        f"Suggestion: {validation_result['suggestion']}\n\n"
                        f"Switching to search mode for broader results."
                    )
                    # Switch to search mode for invalid barcodes
                    self.is_search_mode = True
                    self._set_mode_ui()
                    
                # Fallback to partial name search
                products = self._search_products(term, limit=5)
                if len(products) == 1:
                    self._handle_product_found(products[0])
                elif products:
                    self._show_search_dialog(products)
                else:
                    self._show_not_found(term)
            else:
                # Search mode: broader search
                products = self._search_products(term)
                if products:
                    self._show_search_dialog(products)
                else:
                    self._show_not_found(term)
                    
        except Exception as e:
            app_logger.exception("Barcode search failed")
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")
            
    def _find_by_barcode(self, term):
        """Find product by exact barcode or SKU match"""
        try:
            return self.session.query(Product).filter(
                (Product.barcode == term) | (Product.sku == term)
            ).first()
        except Exception as e:
            app_logger.exception("Barcode lookup failed")
            return None
            
    def _search_products(self, term, limit=50):
        """Search products by name, SKU, barcode, or description"""
        try:
            query = self.session.query(Product).filter(
                Product.is_active == True
            ).filter(
                (Product.name.ilike(f'%{term}%')) |
                (Product.sku.ilike(f'%{term}%')) |
                (Product.barcode.ilike(f'%{term}%')) |
                (Product.description.ilike(f'%{term}%'))
            ).order_by(Product.name)
            
            if limit:
                query = query.limit(limit)
                
            return query.all()
        except Exception as e:
            app_logger.exception("Product search failed")
            return []
            
    def _handle_product_found(self, product):
        """Handle when a single product is found"""
        if self.auto_add and self.show_quantity:
            # Auto-add to cart/list with quantity
            try:
                qty_text = self.quantity_input.text().strip()
                if not qty_text:
                    qty = 1
                else:
                    qty = int(qty_text)
                    if qty <= 0:
                        qty = 1
            except (ValueError, TypeError):
                qty = 1
                # Show brief error message
                print(f"⚠️ Invalid quantity entered, using 1 instead")
            self.product_added.emit(product, qty)
        else:
            # Just select the product
            self.product_selected.emit(product)
            
        self.search_input.clear()
        self.search_input.setFocus()
        
    def _show_search_dialog(self, products):
        """Show search results dialog"""
        dialog = ProductSearchDialog(products, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_product:
            self._handle_product_found(dialog.selected_product)
            
    def _show_not_found(self, term):
        """Show not found message"""
        QMessageBox.information(
            self, 
            "Product Not Found", 
            f"No product found matching '{term}'\n\n"
            "Try:\n"
            "• Checking the barcode/SKU\n"
            "• Using search mode (F2)\n"
            "• Searching by product name"
        )
        
    def focus_input(self):
        """Focus the search input"""
        self.search_input.setFocus()
        
    def clear_input(self):
        """Clear the search input"""
        self.search_input.clear()


class ProductSearchDialog(QDialog):
    """Dialog to show product search results"""
    
    def __init__(self, products, parent=None):
        super().__init__(parent)
        self.products = products
        self.selected_product = None
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Select Product")
        self.setMinimumSize(700, 400)
        self.setStyleSheet("""
            QDialog {
                background: #1e293b;
                color: #f8fafc;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"Found {len(self.products)} product(s)")
        header.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: #3b82f6;
            padding: 10px 0;
        """)
        layout.addWidget(header)
        
        # Products table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Name", "SKU", "Barcode", "Price", "Stock", "Supplier"
        ])
        
        # Style the table
        self.table.setStyleSheet("""
            QTableWidget {
                background: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                gridline-color: #334155;
                selection-background-color: #3b82f6;
            }
            QHeaderView::section {
                background: #1e293b;
                color: #94a3b8;
                padding: 10px;
                border: none;
                font-weight: 600;
                text-transform: uppercase;
                font-size: 11px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #334155;
            }
        """)
        
        # Configure table
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        # Populate table
        self.table.setRowCount(len(self.products))
        for row, product in enumerate(self.products):
            self.table.setItem(row, 0, QTableWidgetItem(product.name or ""))
            self.table.setItem(row, 1, QTableWidgetItem(product.sku or ""))
            self.table.setItem(row, 2, QTableWidgetItem(product.barcode or ""))
            self.table.setItem(row, 3, QTableWidgetItem(f"Rs {product.retail_price:,.2f}"))
            self.table.setItem(row, 4, QTableWidgetItem(str(product.stock_level or 0)))
            
            supplier_name = ""
            if product.supplier:
                supplier_name = product.supplier.name
            self.table.setItem(row, 5, QTableWidgetItem(supplier_name))
            
        # Double-click to select
        self.table.doubleClicked.connect(self._on_double_click)
        
        layout.addWidget(self.table)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.button(QDialogButtonBox.StandardButton.Ok).setText("Select Product")
        button_box.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancel")
        
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        
        layout.addWidget(button_box)
        
        # Select first row by default
        if self.products:
            self.table.selectRow(0)
            
    def _on_double_click(self, index):
        """Handle double-click on table row"""
        if index.isValid():
            self.selected_product = self.products[index.row()]
            self.accept()
            
    def _on_accept(self):
        """Handle OK button click"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            self.selected_product = self.products[current_row]
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a product.")


class QuickBarcodeWidget(QWidget):
    """Compact barcode widget for inline use"""
    
    product_selected = Signal(object)
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Barcode input
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan barcode or enter SKU...")
        self.barcode_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 13px;
                background: #0f172a;
                color: #f8fafc;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        self.barcode_input.returnPressed.connect(self._on_search)
        
        # Search button
        search_btn = QPushButton("🔍")
        search_btn.setMaximumWidth(30)
        search_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                border: none;
                border-radius: 4px;
                padding: 6px;
                color: Qt.white;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        search_btn.clicked.connect(self._on_search)
        
        layout.addWidget(self.barcode_input, 1)
        layout.addWidget(search_btn)
        
    def _on_search(self):
        """Handle barcode search"""
        term = self.barcode_input.text().strip()
        if not term:
            return
            
        try:
            # Try exact barcode/SKU match first
            product = self.session.query(Product).filter(
                (Product.barcode == term) | (Product.sku == term)
            ).first()
            
            if product:
                self.product_selected.emit(product)
                self.barcode_input.clear()
            else:
                QMessageBox.information(
                    self, 
                    "Not Found", 
                    f"No product found with barcode/SKU: {term}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {str(e)}")
            
    def focus_input(self):
        """Focus the barcode input"""
        self.barcode_input.setFocus()
        
    def clear_input(self):
        """Clear the barcode input"""
        self.barcode_input.clear()
