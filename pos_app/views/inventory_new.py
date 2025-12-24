try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QListWidget, QListWidgetItem, QCompleter, QGroupBox, QScrollArea, QTextEdit, QCheckBox
    )
    from PySide6.QtCore import Signal, Qt, QTimer, QStringListModel
    from PySide6.QtGui import QColor
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QListWidget, QListWidgetItem, QCompleter, QGroupBox, QScrollArea, QTextEdit, QCheckBox
    )
    from PyQt6.QtCore import pyqtSignal as Signal, Qt, QTimer, QStringListModel
    from PyQt6.QtGui import QColor

try:
    from pos_app.models.database import Product
    from pos_app.views.suppliers import SupplierDialog
    from pos_app.models.database import Supplier
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    _this_file = Path(__file__).resolve()
    _project_root = _this_file.parents[2]
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))
    from pos_app.models.database import Product
    from pos_app.views.suppliers import SupplierDialog
    from pos_app.models.database import Supplier


class NavigationSpinBox(QSpinBox):
    """QSpinBox that doesn't intercept Up/Down arrow keys for dialog navigation"""
    def keyPressEvent(self, event):
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Don't handle Up/Down arrows - let parent dialog handle them
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            # Don't call parent keyPressEvent - just ignore the event
            # This prevents the spin box from handling the arrow key
            event.ignore()
        else:
            super().keyPressEvent(event)


class NavigationDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox that doesn't intercept Up/Down arrow keys for dialog navigation"""
    def keyPressEvent(self, event):
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Don't handle Up/Down arrows - let parent dialog handle them
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            # Don't call parent keyPressEvent - just ignore the event
            # This prevents the spin box from handling the arrow key
            event.ignore()
        else:
            super().keyPressEvent(event)


class SearchableComboBox(QWidget):
    """A searchable/autocomplete dropdown for selecting items"""
    
    def __init__(self, parent=None, allow_add_new=False, on_add_new_callback=None):
        super().__init__(parent)
        self.items = []  # List of (display_name, id) tuples
        self.allow_add_new = allow_add_new
        self.on_add_new_callback = on_add_new_callback
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search...")
        self.search_input.textChanged.connect(self.on_search_text_changed)
        
        # Override keyPressEvent for search input
        original_keyPressEvent = self.search_input.keyPressEvent
        def search_keyPressEvent(event):
            try:
                from PySide6.QtCore import Qt
            except ImportError:
                from PyQt6.QtCore import Qt
            
            print(f"[DEBUG] SearchInput keyPressEvent: key={event.key}")
            
            if event.key() == Qt.Key.Key_Down:
                if self.suggestions_list.count() > 0 and self.suggestions_list.isVisible():
                    print(f"[DEBUG] SearchInput: Moving focus to suggestions list")
                    self.suggestions_list.setFocus()
                    self.suggestions_list.setCurrentRow(0)
                    return
                else:
                    print(f"[DEBUG] SearchInput: No suggestions, letting parent handle")
                    original_keyPressEvent(event)
                    return
            
            # Let original handler process other keys
            original_keyPressEvent(event)
        
        self.search_input.keyPressEvent = search_keyPressEvent
        layout.addWidget(self.search_input)
        
        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.itemClicked.connect(self.on_suggestion_selected)
        
        # Override keyPressEvent for suggestions list
        original_suggestions_keyPressEvent = self.suggestions_list.keyPressEvent
        def suggestions_keyPressEvent(event):
            try:
                from PySide6.QtCore import Qt
            except ImportError:
                from PyQt6.QtCore import Qt
            
            print(f"[DEBUG] SuggestionsList keyPressEvent: key={event.key}")
            
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                current_item = self.suggestions_list.currentItem()
                if current_item:
                    print(f"[DEBUG] SuggestionsList: Selecting {current_item.text()}")
                    self.on_suggestion_selected(current_item)
                return
            
            elif event.key() == Qt.Key.Key_Escape:
                print(f"[DEBUG] SuggestionsList: Returning to search")
                self.search_input.setFocus()
                self.search_input.selectAll()
                return
            
            elif event.key() == Qt.Key.Key_Up:
                current_row = self.suggestions_list.currentRow()
                if current_row > 0:
                    self.suggestions_list.setCurrentRow(current_row - 1)
                    return
                else:
                    print(f"[DEBUG] SuggestionsList: At top, letting parent handle")
                    original_suggestions_keyPressEvent(event)
                    return
            
            elif event.key() == Qt.Key.Key_Down:
                current_row = self.suggestions_list.currentRow()
                if current_row < self.suggestions_list.count() - 1:
                    self.suggestions_list.setCurrentRow(current_row + 1)
                    return
                else:
                    print(f"[DEBUG] SuggestionsList: At bottom, letting parent handle")
                    original_suggestions_keyPressEvent(event)
                    return
            
            # Let original handler process other keys
            original_suggestions_keyPressEvent(event)
        
        self.suggestions_list.keyPressEvent = suggestions_keyPressEvent
        layout.addWidget(self.suggestions_list)
    
    def set_items(self, items):
        """Set available items. items should be list of (display_name, id) tuples"""
        self.items = items
        self.update_suggestions()
    
    def on_search_text_changed(self):
        """Update suggestions as user types"""
        print(f"[DEBUG] Search text changed: '{self.search_input.text()}'")
        self.update_suggestions()
        print(f"[DEBUG] After update_suggestions - count: {self.suggestions_list.count()}, visible: {self.suggestions_list.isVisible()}")
    
    def update_suggestions(self):
        """Filter and display suggestions based on search text"""
        search_text = self.search_input.text().lower()
        self.suggestions_list.clear()
        
        for display_name, item_id in self.items:
            if search_text == "" or search_text in display_name.lower():
                item = QListWidgetItem(display_name)
                item.setData(Qt.UserRole, item_id)
                self.suggestions_list.addItem(item)
        
        # Add "Add New" option if enabled and search text is not empty
        if self.allow_add_new and search_text:
            add_new_item = QListWidgetItem(f"➕ Add new: '{search_text}'")
            add_new_item.setData(Qt.UserRole, "__ADD_NEW__")
            add_new_item.setForeground(QColor("#3b82f6"))
            self.suggestions_list.addItem(add_new_item)
        
        # Auto-select first item if there are suggestions
        if self.suggestions_list.count() > 0:
            self.suggestions_list.setCurrentRow(0)
    
    def keyPressEvent(self, event):
        """Handle key press events - only for internal navigation, let parent handle field navigation"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Only handle keys when this widget or its children have focus
        if not (self.hasFocus() or self.search_input.hasFocus() or self.suggestions_list.hasFocus()):
            super().keyPressEvent(event)
            return
        
        if self.search_input.hasFocus():
            if event.key() == Qt.Key_Down:
                # Only handle if suggestions are visible and have items
                if self.suggestions_list.count() > 0 and self.suggestions_list.isVisible():
                    self.suggestions_list.setFocus()
                    self.suggestions_list.setCurrentRow(0)
                    return
                # Don't handle - let parent deal with navigation
                event.ignore()
                return
            elif event.key() == Qt.Key_Up:
                # Only handle if suggestions are visible and have items
                if self.suggestions_list.count() > 0 and self.suggestions_list.isVisible():
                    self.suggestions_list.setFocus()
                    self.suggestions_list.setCurrentRow(self.suggestions_list.count() - 1)
                    return
                # Don't handle - let parent deal with navigation
                event.ignore()
                return
            elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Select current suggestion
                if self.suggestions_list.count() > 0:
                    current_item = self.suggestions_list.currentItem()
                    if current_item:
                        self.on_suggestion_selected(current_item)
                return
            # Don't handle Tab/Backtab - let parent handle navigation
            elif event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
        
        elif self.suggestions_list.hasFocus():
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                # Select the current item
                current_item = self.suggestions_list.currentItem()
                if current_item:
                    self.on_suggestion_selected(current_item)
                return
            elif event.key() == Qt.Key_Up:
                # Move up in suggestions list
                current_row = self.suggestions_list.currentRow()
                if current_row > 0:
                    self.suggestions_list.setCurrentRow(current_row - 1)
                    return
                # At top - don't handle, let parent deal with navigation
                event.ignore()
                return
            elif event.key() == Qt.Key_Down:
                # Move down in suggestions list
                current_row = self.suggestions_list.currentRow()
                if current_row < self.suggestions_list.count() - 1:
                    self.suggestions_list.setCurrentRow(current_row + 1)
                    return
                # At bottom - don't handle, let parent deal with navigation
                event.ignore()
                return
            # Don't handle Tab/Backtab - let parent handle navigation
            elif event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return
            elif event.key() == Qt.Key_Escape:
                # Return focus to search input
                self.search_input.setFocus()
                self.search_input.selectAll()
                return
        
        # For other keys, use default handling
        super().keyPressEvent(event)
    
    def on_suggestion_selected(self, item):
        """Handle suggestion selection"""
        item_id = item.data(Qt.UserRole)
        
        # Check if this is the "Add New" option
        if item_id == "__ADD_NEW__":
            # Extract the new name from the item text
            text = item.text()
            new_name = text.replace("➕ Add new: '", "").replace("'", "")
            
            # Call the callback if provided
            if self.on_add_new_callback:
                new_id = self.on_add_new_callback(new_name)
                if new_id:
                    # Add the new item to the list
                    self.items.append((new_name, new_id))
                    self.search_input.setText(new_name)
                    self.suggestions_list.clear()
                    # Keep focus in the search input after adding new supplier
                    self.search_input.setFocus()
                    self.search_input.selectAll()
            return
        
        self.search_input.setText(item.text())
        self.suggestions_list.clear()
        # Keep focus in the search input after selection
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def get_selected_id(self):
        """Get the ID of the currently selected item"""
        text = self.search_input.text()
        for display_name, item_id in self.items:
            if display_name == text:
                return item_id
        return None
    
    def currentData(self):
        """Alias for get_selected_id() for QComboBox compatibility"""
        return self.get_selected_id()
    
    def setFocus(self, reason=None):
        """Override setFocus to focus on the search input"""
        if reason is not None:
            self.search_input.setFocus(reason)
        else:
            self.search_input.setFocus()
        self.search_input.selectAll()
    
    def currentText(self):
        """Get the current text for QComboBox compatibility"""
        return self.search_input.text()
    
    def set_selected_by_id(self, item_id):
        """Set the selected item by ID"""
        for display_name, id_val in self.items:
            if id_val == item_id:
                self.search_input.setText(display_name)
                return
    
    def clear(self):
        """Clear the search field"""
        self.search_input.clear()
    
    def keyPressEvent(self, event):
        """Handle key press events for navigation"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Let parent handle Tab/Backtab for dialog navigation
        if event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            event.ignore()
            return
        
        # For other keys, use default handling
        super().keyPressEvent(event)

def safe_get_current_data(combo_widget):
    """Safely get current data from any combo box type (QComboBox or SearchableComboBox)"""
    try:
        # Try QComboBox method first
        return combo_widget.currentData()
    except AttributeError:
        try:
            # Try SearchableComboBox method
            return combo_widget.get_selected_id()
        except AttributeError:
            # Fallback: try to get data from current item
            try:
                current_item = combo_widget.currentItem() if hasattr(combo_widget, 'currentItem') else None
                if current_item:
                    return current_item.data(Qt.UserRole)
            except:
                pass

    return None

class InventoryWidget(QWidget):
    product_added = Signal()
    product_selected = Signal(object)  # Signal for when a product is selected
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected_product_id = None
        self._last_sync_ts = None
        
        # Connect the signal for testing
        self.product_selected.connect(self.on_product_selected_test)
        
        self.setup_ui()
        self.load_products()
        self._init_sync_timer()
    
    def on_product_selected_test(self, product):
        """Test method to verify signal is received"""
        print(f"[TEST] SUCCESS: Product selection signal received for: {product.name}")

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with action buttons
        header_layout = QHBoxLayout()
        header = QLabel("📦 Inventory Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        # Action buttons (initially disabled)
        self.edit_product_btn = QPushButton("✏️ Edit Product")
        self.edit_product_btn.setProperty('accent', 'Qt.blue')
        self.edit_product_btn.setMinimumHeight(36)
        self.edit_product_btn.setEnabled(False)
        self.edit_product_btn.clicked.connect(self.edit_selected_product)
        
        self.delete_product_btn = QPushButton("🗑️ Delete Product")
        self.delete_product_btn.setProperty('accent', 'Qt.red')
        self.delete_product_btn.setMinimumHeight(36)
        self.delete_product_btn.setEnabled(False)
        self.delete_product_btn.clicked.connect(self.delete_selected_product)
        
        header_layout.addWidget(self.edit_product_btn)
        header_layout.addWidget(self.delete_product_btn)
        layout.addLayout(header_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        add_btn = QPushButton("✨ Add New Product")
        add_btn.setProperty('accent', 'Qt.green')
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self.show_add_product_dialog)

        manage_cats_btn = QPushButton("🗂️ Categories")
        manage_cats_btn.setToolTip("Manage Categories and Subcategories")
        manage_cats_btn.setMinimumHeight(44)
        manage_cats_btn.clicked.connect(self.show_category_manager)
        
        low_btn = QPushButton("⚠️ Low Stock")
        low_btn.setToolTip("Show products at or below reorder level")
        low_btn.setProperty('accent', 'orange')
        low_btn.setMinimumHeight(44)
        low_btn.clicked.connect(self.show_low_stock_only)
        
        toolbar_layout.addWidget(add_btn)
        toolbar_layout.addWidget(manage_cats_btn)
        toolbar_layout.addWidget(low_btn)
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Search bar + pagination
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search products...')
        self.search_input.textChanged.connect(self.apply_filter)
        search_layout.addWidget(self.search_input)

        # Pagination
        self.page_size = 12
        self.current_page = 0
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

        # Products Table with professional styling
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "🏷️ SKU", "📦 Name", "📝 Description", "💰 Retail Price",
            "💵 Wholesale Price", "📊 Stock Level"
        ])
        
        # Apply professional table styling
        try:
            from pos_app.utils.table_styling import TableStyler
            TableStyler.setup_product_table(self.table)
        except Exception:
            # Fallback basic styling
            self.table.setAlternatingRowColors(True)
            self.table.setSortingEnabled(True)
        
        # Table selection
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.table.doubleClicked.connect(self.show_product_info_dialog)
        # Also add single-click for testing
        self.table.itemClicked.connect(self.show_product_info_dialog)
        
        try:
            from PySide6.QtWidgets import QHeaderView
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.verticalHeader().setVisible(False)
            self.table.setWordWrap(True)
        except Exception:
            pass

    def on_selection_changed(self):
        """Enable/disable action buttons based on selection"""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # Get product ID from the current page items
            items = getattr(self, '_current_page_items', [])
            if 0 <= row < len(items):
                self.selected_product_id = items[row].id
                self.edit_product_btn.setEnabled(True)
                self.delete_product_btn.setEnabled(True)
            else:
                self.selected_product_id = None
                self.edit_product_btn.setEnabled(False)
                self.delete_product_btn.setEnabled(False)
        else:
            self.selected_product_id = None
            self.edit_product_btn.setEnabled(False)
            self.delete_product_btn.setEnabled(False)

    def show_product_info_dialog(self):
        """Show product info dialog with OK button to select the product"""
        print(f"[DEBUG] show_product_info_dialog called")
        selected_rows = self.table.selectionModel().selectedRows()
        print(f"[DEBUG] Selected rows: {len(selected_rows)}")
        
        if not selected_rows:
            print("[DEBUG] No rows selected, returning")
            return
        
        row = selected_rows[0].row()
        print(f"[DEBUG] Selected row index: {row}")
        
        items = getattr(self, '_current_page_items', [])
        print(f"[DEBUG] Current page items: {len(items)}")
        
        if 0 <= row < len(items):
            product = items[row]
            print(f"[DEBUG] Selected product: {product.name} (ID: {product.id})")
            
            # Create info dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Product Information")
            dialog.setMinimumSize(400, 300)
            
            # Add keyPressEvent for Enter key
            def dialog_keyPressEvent(event):
                try:
                    from PySide6.QtCore import Qt
                except ImportError:
                    from PyQt6.QtCore import Qt
                if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    dialog.accept()
                elif event.key() == Qt.Key_Escape:
                    dialog.reject()
                else:
                    super(dialog, type(dialog)).keyPressEvent(event)
            
            dialog.keyPressEvent = dialog_keyPressEvent
            
            layout = QVBoxLayout(dialog)
            
            # Product info
            info_text = f"""
            <h3>{product.name}</h3>
            <p><b>SKU:</b> {product.sku or 'N/A'}</p>
            <p><b>Description:</b> {product.description or 'N/A'}</p>
            <p><b>Retail Price:</b> Rs {product.retail_price or 0:.2f}</p>
            <p><b>Wholesale Price:</b> Rs {product.wholesale_price or 0:.2f}</p>
            <p><b>Purchase Price:</b> Rs {product.purchase_price or 0:.2f}</p>
            <p><b>Stock Level:</b> {product.stock_level or 0}</p>
            <p><b>Reorder Level:</b> {product.reorder_level or 0}</p>
            <p><b>Supplier:</b> {product.supplier.name if product.supplier else 'N/A'}</p>
            <p><b>Barcode:</b> {product.barcode or 'N/A'}</p>
            """
            
            info_label = QLabel(info_text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)
            
            # Buttons
            button_layout = QHBoxLayout()
            ok_btn = QPushButton("OK")
            cancel_btn = QPushButton("Cancel")
            
            ok_btn.clicked.connect(lambda: dialog.accept())
            cancel_btn.clicked.connect(lambda: dialog.reject())
            
            button_layout.addStretch()
            button_layout.addWidget(ok_btn)
            button_layout.addWidget(cancel_btn)
            
            layout.addLayout(button_layout)
            
            # Show dialog
            result = dialog.exec()
            print(f"[DEBUG] Dialog result: {result}")
            
            if result == QDialog.Accepted:
                # User clicked OK or pressed Enter - select this product
                print(f"[DEBUG] User accepted - selecting product {product.name}")
                self.selected_product_id = product.id
                print(f"[DEBUG] Set selected_product_id to: {self.selected_product_id}")
                self.edit_product_btn.setEnabled(True)
                self.delete_product_btn.setEnabled(True)
                print(f"[DEBUG] Enabled edit/delete buttons")
                
                # Highlight the selected row
                self.table.selectRow(row)
                print(f"[DEBUG] Highlighted row {row}")
                
                # Emit signal that product was selected
                print(f"[DEBUG] Emitting product_selected signal for: {product.name}")
                self.product_selected.emit(product)
                print(f"[DEBUG] Signal emitted successfully")
                
                # Show selection confirmation
                QMessageBox.information(self, "Product Selected", 
                                     f"Product '{product.name}' has been selected!\n\nYou can now edit or delete this product.")
            else:
                # User clicked Cancel or pressed Escape
                print(f"[DEBUG] User cancelled selection for: {product.name}")
        else:
            print(f"[DEBUG] Row {row} is out of range (0-{len(items)-1})")
    
    def edit_selected_product(self):
        if self.selected_product_id:
            self._edit_product(self.selected_product_id)

    def delete_selected_product(self):
        if self.selected_product_id:
            self._delete_product(self.selected_product_id)

    def load_products(self):
        from pos_app.models.database import Product
        products = self.controller.get_all_products() if hasattr(self.controller, 'get_all_products') else self.controller.session.query(Product).all()
        # Cache for pagination/filtering
        self._products_cache = products
        self.current_page = 0
        self._update_page()
        # Update local sync timestamp snapshot
        try:
            from pos_app.models.database import get_sync_timestamp
            ts = get_sync_timestamp(self.controller.session, 'products')
            self._last_sync_ts = ts
        except Exception:
            pass

    def _init_sync_timer(self):
        """Poll sync_state table and auto-refresh when products/stock change."""
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
            ts = get_sync_timestamp(self.controller.session, 'products')
            if ts is None:
                return
            if self._last_sync_ts is None or ts > self._last_sync_ts:
                self._last_sync_ts = ts
                self.load_products()
        except Exception:
            pass

    def _update_page(self):
        items = getattr(self, '_filtered_products', self._products_cache)
        start = self.current_page * self.page_size
        page_items = items[start:start + self.page_size]
        self._current_page_items = page_items  # Store for selection handling
        
        self.table.setRowCount(len(page_items))
        for i, product in enumerate(page_items):
            try:
                from pos_app.utils.table_styling import TableStyler
                
                # Create styled items
                self.table.setItem(i, 0, TableStyler.create_item(product.sku or ""))
                self.table.setItem(i, 1, TableStyler.create_item(product.name or ""))
                self.table.setItem(i, 2, TableStyler.create_item(product.description or ""))
                self.table.setItem(i, 3, TableStyler.create_item(product.retail_price, is_currency=True))
                self.table.setItem(i, 4, TableStyler.create_item(product.wholesale_price, is_currency=True))
                
                # Stock level with color coding
                stock_text = str(product.stock_level) if product.stock_level is not None else "0"
                stock_item = TableStyler.create_item(stock_text, is_numeric=True)
                
                # Color code stock levels
                if product.stock_level is not None:
                    if product.stock_level <= 5:
                        stock_item.setBackground(QColor('#fee2e2'))  # Light red
                    elif product.stock_level <= 10:
                        stock_item.setBackground(QColor('#fef3c7'))  # Light yellow
                
                self.table.setItem(i, 5, stock_item)
                
            except Exception:
                # Fallback to basic items
                self.table.setItem(i, 0, QTableWidgetItem(product.sku or ""))
                self.table.setItem(i, 1, QTableWidgetItem(product.name or ""))
                self.table.setItem(i, 2, QTableWidgetItem(product.description or ""))
                self.table.setItem(i, 3, QTableWidgetItem(f"Rs {product.retail_price:.2f}" if product.retail_price else ""))
                self.table.setItem(i, 4, QTableWidgetItem(f"Rs {product.wholesale_price:.2f}" if product.wholesale_price else ""))
                self.table.setItem(i, 5, QTableWidgetItem(str(product.stock_level) if product.stock_level is not None else ""))
            
        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page+1} / {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled((self.current_page+1) < total_pages)

    def apply_filter(self, text):
        try:
            text = (text or "").strip().lower()
            if not hasattr(self, '_products_cache'):
                return
            filtered = [p for p in self._products_cache if text in (p.name or '').lower() or text in (p.barcode or '').lower()]
            self._filtered_products = filtered
            self.current_page = 0
            self._update_page()
        except Exception:
            pass

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()

    def _next_page(self):
        items = getattr(self, '_filtered_products', self._products_cache)
        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        if (self.current_page + 1) < total_pages:
            self.current_page += 1
            self._update_page()

    def show_add_product_dialog(self):
        dialog = ProductDialog(self)
        if dialog.exec() == QDialog.Accepted:
            try:
                self.controller.add_product(
                    name=dialog.name_input.text(),
                    description=None,
                    sku=dialog.sku_input.text(),
                    barcode=(dialog.barcode_input.text().strip() or None),
                    purchase_price=dialog.purchase_price_input.value(),
                    wholesale_price=dialog.wholesale_price_input.value(),
                    retail_price=dialog.retail_price_input.value(),
                    stock_level=dialog.stock_input.value(),
                    reorder_level=dialog.reorder_input.value(),
                    supplier_id=safe_get_current_data(dialog.supplier_input) or 1,
                    unit=(dialog.unit_input.currentText() if hasattr(dialog, 'unit_input') else "pcs"),
                    shelf_location=(dialog.shelf_location_input.text().strip() if hasattr(dialog, 'shelf_location_input') else ""),
                    warehouse_location=(dialog.warehouse_location_input.text().strip() if hasattr(dialog, 'warehouse_location_input') else None),
                    product_category_id=(dialog.category_input.currentData() if hasattr(dialog, 'category_input') else None),
                    product_subcategory_id=(dialog.subcategory_input.currentData() if hasattr(dialog, 'subcategory_input') else None),
                    packaging_type_id=(dialog.packaging_type_input.currentData() if hasattr(dialog, 'packaging_type_input') else None),
                    category=(dialog.category_input.currentText() or '').strip() or None,
                    subcategory=(dialog.subcategory_input.currentText() or '').strip() or None,
                    brand=(dialog.brand_input.currentText().strip() or None) if hasattr(dialog, 'brand_input') else None,
                    colors=(dialog.colors_input.currentText().strip() or None) if hasattr(dialog, 'colors_input') else None,
                    model=(dialog.model_input.text().strip() or None) if hasattr(dialog, 'model_input') else None,
                    size=(dialog.size_input.text().strip() or None) if hasattr(dialog, 'size_input') else None,
                    dimensions=(dialog.dimensions_input.text().strip() or None) if hasattr(dialog, 'dimensions_input') else None,
                    tax_rate=(dialog.tax_rate_input.value() if hasattr(dialog, 'tax_rate_input') else None),
                    discount_percentage=(dialog.discount_percentage_input.value() if hasattr(dialog, 'discount_percentage_input') else None),
                    notes=((dialog.notes_input.toPlainText() if hasattr(dialog.notes_input, 'toPlainText') else dialog.notes_input.text()).strip() or None) if hasattr(dialog, 'notes_input') else None,
                    is_active=(bool(dialog.is_active_checkbox.isChecked()) if hasattr(dialog, 'is_active_checkbox') else None),
                    product_type=(dialog.product_type_input.currentText() if hasattr(dialog, 'product_type_input') else None),
                    low_stock_alert=(bool(dialog.low_stock_alert_checkbox.isChecked()) if hasattr(dialog, 'low_stock_alert_checkbox') else None),
                    warranty=(dialog.warranty_input.text().strip() or None) if hasattr(dialog, 'warranty_input') else None,
                    weight=(dialog.weight_input.value() if hasattr(dialog, 'weight_input') else None),
                    expiry_date=(
                        dialog.expiry_input.date().toString('yyyy-MM-dd')
                        if (getattr(dialog, 'has_expiry_checkbox', None) is not None and dialog.has_expiry_checkbox.isChecked())
                        else None
                    )
                )
                # Mark products/stock changed for LAN clients
                try:
                    from pos_app.models.database import mark_sync_changed
                    mark_sync_changed(self.controller.session, 'products')
                    mark_sync_changed(self.controller.session, 'stock')
                    self.controller.session.commit()
                except Exception:
                    try:
                        self.controller.session.commit()
                    except Exception:
                        pass
                self.load_products()
                self.product_added.emit()
            except Exception as e:
                from utils.logger import app_logger
                app_logger.exception("Failed to add product from Inventory view")
                QMessageBox.critical(self, "Error", str(e))

    def show_low_stock_only(self):
        try:
            products = getattr(self, '_products_cache', [])
            lows = []
            for p in products:
                try:
                    lvl = (p.stock_level or 0)
                    thr = (p.reorder_level or 0)
                    if lvl <= thr:
                        lows.append(p)
                except Exception:
                    pass
            self._filtered_products = lows
            self.current_page = 0
            self._update_page()
        except Exception:
            pass

    def _edit_product(self, product_id):
        try:
            product = self.controller.session.get(Product, product_id)
            if not product:
                QMessageBox.warning(self, "Error", "Product not found")
                return
            dialog = ProductDialog(self, product)
            if dialog.exec() == QDialog.Accepted:
                product.name = dialog.name_input.text()
                product.sku = dialog.sku_input.text()
                product.barcode = dialog.barcode_input.text().strip() or None
                product.purchase_price = dialog.purchase_price_input.value()
                product.wholesale_price = dialog.wholesale_price_input.value()
                product.retail_price = dialog.retail_price_input.value()
                product.stock_level = dialog.stock_input.value()
                product.reorder_level = dialog.reorder_input.value()
                product.supplier_id = safe_get_current_data(dialog.supplier_input)

                try:
                    product.product_category_id = dialog.category_input.currentData()
                except Exception:
                    product.product_category_id = None
                try:
                    product.product_subcategory_id = dialog.subcategory_input.currentData()
                except Exception:
                    product.product_subcategory_id = None

                # Packaging type (optional)
                try:
                    cols = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
                except Exception:
                    cols = set()
                if ('packaging_type_id' in cols or hasattr(product, 'packaging_type_id')) and hasattr(dialog, 'packaging_type_input'):
                    try:
                        product.packaging_type_id = dialog.packaging_type_input.currentData()
                    except Exception:
                        try:
                            product.packaging_type_id = None
                        except Exception:
                            pass

                # Optional fields: brand/colors (schema-safe)
                try:
                    cols = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
                except Exception:
                    cols = set()
                if ('brand' in cols or hasattr(product, 'brand')) and hasattr(dialog, 'brand_input'):
                    try:
                        product.brand = (dialog.brand_input.currentText() or '').strip() or None
                    except Exception:
                        try:
                            product.brand = None
                        except Exception:
                            pass
                if ('colors' in cols or hasattr(product, 'colors')) and hasattr(dialog, 'colors_input'):
                    try:
                        product.colors = (dialog.colors_input.currentText() or '').strip() or None
                    except Exception:
                        try:
                            product.colors = None
                        except Exception:
                            pass

                # New fields (schema-safe)
                try:
                    cols = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
                except Exception:
                    cols = set()
                if ('product_type' in cols or hasattr(product, 'product_type')) and hasattr(dialog, 'product_type_input'):
                    try:
                        product.product_type = (dialog.product_type_input.currentText() or '').strip() or None
                    except Exception:
                        pass
                if ('unit' in cols or hasattr(product, 'unit')) and hasattr(dialog, 'unit_input'):
                    try:
                        product.unit = (dialog.unit_input.currentText() or '').strip() or None
                    except Exception:
                        pass
                if ('low_stock_alert' in cols or hasattr(product, 'low_stock_alert')) and hasattr(dialog, 'low_stock_alert_checkbox'):
                    try:
                        product.low_stock_alert = bool(dialog.low_stock_alert_checkbox.isChecked())
                    except Exception:
                        pass
                if ('warranty' in cols or hasattr(product, 'warranty')) and hasattr(dialog, 'warranty_input'):
                    try:
                        product.warranty = (dialog.warranty_input.text() or '').strip() or None
                    except Exception:
                        pass
                if ('weight' in cols or hasattr(product, 'weight')) and hasattr(dialog, 'weight_input'):
                    try:
                        product.weight = float(dialog.weight_input.value())
                    except Exception:
                        pass

                # Extended fields (schema-safe)
                if ('model' in cols or hasattr(product, 'model')) and hasattr(dialog, 'model_input'):
                    try:
                        product.model = (dialog.model_input.text() or '').strip() or None
                    except Exception:
                        pass
                if ('size' in cols or hasattr(product, 'size')) and hasattr(dialog, 'size_input'):
                    try:
                        product.size = (dialog.size_input.text() or '').strip() or None
                    except Exception:
                        pass
                if ('dimensions' in cols or hasattr(product, 'dimensions')) and hasattr(dialog, 'dimensions_input'):
                    try:
                        product.dimensions = (dialog.dimensions_input.text() or '').strip() or None
                    except Exception:
                        pass
                if ('shelf_location' in cols or hasattr(product, 'shelf_location')) and hasattr(dialog, 'shelf_location_input'):
                    try:
                        product.shelf_location = (dialog.shelf_location_input.text() or '').strip() or None
                    except Exception:
                        pass
                if ('warehouse_location' in cols or hasattr(product, 'warehouse_location')) and hasattr(dialog, 'warehouse_location_input'):
                    try:
                        product.warehouse_location = (dialog.warehouse_location_input.text() or '').strip() or None
                    except Exception:
                        pass
                if ('tax_rate' in cols or hasattr(product, 'tax_rate')) and hasattr(dialog, 'tax_rate_input'):
                    try:
                        product.tax_rate = float(dialog.tax_rate_input.value())
                    except Exception:
                        pass
                if ('discount_percentage' in cols or hasattr(product, 'discount_percentage')) and hasattr(dialog, 'discount_percentage_input'):
                    try:
                        product.discount_percentage = float(dialog.discount_percentage_input.value())
                    except Exception:
                        pass
                if ('notes' in cols or hasattr(product, 'notes')) and hasattr(dialog, 'notes_input'):
                    try:
                        product.notes = (dialog.notes_input.toPlainText() if hasattr(dialog.notes_input, 'toPlainText') else dialog.notes_input.text()).strip() or None
                    except Exception:
                        pass
                if ('is_active' in cols or hasattr(product, 'is_active')) and hasattr(dialog, 'is_active_checkbox'):
                    try:
                        product.is_active = bool(dialog.is_active_checkbox.isChecked())
                    except Exception:
                        pass

                try:
                    cols = set(getattr(getattr(Product, '__table__', None), 'columns', {}).keys())
                except Exception:
                    cols = set()
                if 'category' in cols or hasattr(product, 'category'):
                    try:
                        product.category = (dialog.category_input.currentText() or '').strip() or None
                    except Exception:
                        try:
                            product.category = None
                        except Exception:
                            pass
                if 'subcategory' in cols or hasattr(product, 'subcategory'):
                    try:
                        product.subcategory = (dialog.subcategory_input.currentText() or '').strip() or None
                    except Exception:
                        try:
                            product.subcategory = None
                        except Exception:
                            pass

                try:
                    if getattr(dialog, 'has_expiry_checkbox', None) is not None and dialog.has_expiry_checkbox.isChecked():
                        product.expiry_date = dialog.expiry_input.date().toString('yyyy-MM-dd')
                    else:
                        product.expiry_date = None
                except Exception:
                    product.expiry_date = None
                # Commit and broadcast sync change
                self.controller.session.commit()
                try:
                    from pos_app.models.database import mark_sync_changed
                    mark_sync_changed(self.controller.session, 'products')
                    mark_sync_changed(self.controller.session, 'stock')
                    self.controller.session.commit()
                except Exception:
                    try:
                        self.controller.session.commit()
                    except Exception:
                        pass
                self.load_products()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def show_category_manager(self):
        try:
            session = getattr(getattr(self, 'controller', None), 'session', None)
            if session is None:
                return
        except Exception:
            return

        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox, QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QPushButton, QMessageBox, QInputDialog

        try:
            from sqlalchemy import text
        except Exception:
            text = None

        try:
            from pos_app.models.database import ProductCategory, ProductSubcategory
        except Exception:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Manage Categories")
        dlg.setMinimumWidth(520)

        root = QVBoxLayout(dlg)
        title = QLabel("Product Categories & Subcategories")
        title.setStyleSheet("font-size: 16px; font-weight: 700;")
        root.addWidget(title)

        lists_row = QHBoxLayout()

        cat_col = QVBoxLayout()
        cat_col.addWidget(QLabel("Categories"))
        categories_list = QListWidget()
        cat_col.addWidget(categories_list)

        sub_col = QVBoxLayout()
        sub_col.addWidget(QLabel("Subcategories"))
        subcategories_list = QListWidget()
        sub_col.addWidget(subcategories_list)

        lists_row.addLayout(cat_col, 1)
        lists_row.addLayout(sub_col, 1)
        root.addLayout(lists_row)

        btns = QHBoxLayout()
        add_cat_btn = QPushButton("+ Category")
        del_cat_btn = QPushButton("Delete Category")
        add_sub_btn = QPushButton("+ Subcategory")
        del_sub_btn = QPushButton("Delete Subcategory")
        close_btn = QPushButton("Close")
        btns.addWidget(add_cat_btn)
        btns.addWidget(del_cat_btn)
        btns.addStretch()
        btns.addWidget(add_sub_btn)
        btns.addWidget(del_sub_btn)
        btns.addStretch()
        btns.addWidget(close_btn)
        root.addLayout(btns)

        def _item_id(it):
            try:
                return it.data(32) if it is not None else None
            except Exception:
                return None

        def load_subs_for_selected():
            try:
                subcategories_list.clear()
            except Exception:
                return
            cat_id = _item_id(categories_list.currentItem())
            if not cat_id:
                return
            try:
                subs = session.query(ProductSubcategory).filter(ProductSubcategory.category_id == int(cat_id)).order_by(ProductSubcategory.name.asc()).all()
            except Exception:
                subs = []
            for s in subs or []:
                try:
                    subcategories_list.addItem(f"{s.name}")
                    subcategories_list.item(subcategories_list.count() - 1).setData(32, getattr(s, 'id', None))
                except Exception:
                    pass

        def load_lists(select_cat_id=None):
            try:
                categories_list.clear()
                subcategories_list.clear()
            except Exception:
                return
            try:
                cats = session.query(ProductCategory).order_by(ProductCategory.name.asc()).all()
            except Exception:
                cats = []
            for c in cats or []:
                try:
                    categories_list.addItem(f"{c.name}")
                    categories_list.item(categories_list.count() - 1).setData(32, getattr(c, 'id', None))
                except Exception:
                    pass
            try:
                if categories_list.count() > 0:
                    idx = 0
                    if select_cat_id is not None:
                        for i in range(categories_list.count()):
                            if _item_id(categories_list.item(i)) == select_cat_id:
                                idx = i
                                break
                    categories_list.setCurrentRow(idx)
            except Exception:
                pass

        def add_category():
            name, ok = QInputDialog.getText(dlg, "Add Category", "Category name:")
            if not ok:
                return
            name = (name or '').strip()
            if not name:
                return
            try:
                existing = session.query(ProductCategory).filter(ProductCategory.name.ilike(name)).first()
                if existing is None:
                    obj = ProductCategory(name=name)
                    session.add(obj)
                    session.commit()
                else:
                    obj = existing
            except Exception:
                try:
                    session.rollback()
                except Exception:
                    pass
                return
            load_lists(select_cat_id=getattr(obj, 'id', None))

        def add_subcategory():
            cat_id = _item_id(categories_list.currentItem())
            if not cat_id:
                QMessageBox.warning(dlg, "Subcategory", "Select a category first.")
                return
            name, ok = QInputDialog.getText(dlg, "Add Subcategory", "Subcategory name:")
            if not ok:
                return
            name = (name or '').strip()
            if not name:
                return
            try:
                existing = session.query(ProductSubcategory).filter(
                    ProductSubcategory.category_id == int(cat_id),
                    ProductSubcategory.name.ilike(name)
                ).first()
                if existing is None:
                    obj = ProductSubcategory(category_id=int(cat_id), name=name)
                    session.add(obj)
                    session.commit()
                else:
                    obj = existing
            except Exception:
                try:
                    session.rollback()
                except Exception:
                    pass
                return
            load_lists(select_cat_id=int(cat_id))
            try:
                for i in range(subcategories_list.count()):
                    if _item_id(subcategories_list.item(i)) == getattr(obj, 'id', None):
                        subcategories_list.setCurrentRow(i)
                        break
            except Exception:
                pass

        def delete_category():
            cat_id = _item_id(categories_list.currentItem())
            if not cat_id:
                return
            used = 0
            if text is not None:
                try:
                    used = session.execute(text("SELECT COUNT(1) FROM products WHERE product_category_id = :cid"), {'cid': int(cat_id)}).scalar() or 0
                except Exception:
                    used = 0
            if used:
                QMessageBox.warning(dlg, "Category", "Category is in use by products and cannot be deleted.")
                return
            try:
                session.query(ProductSubcategory).filter(ProductSubcategory.category_id == int(cat_id)).delete(synchronize_session=False)
                session.query(ProductCategory).filter(ProductCategory.id == int(cat_id)).delete(synchronize_session=False)
                session.commit()
            except Exception:
                try:
                    session.rollback()
                except Exception:
                    pass
                return
            load_lists()

        def delete_subcategory():
            sub_id = _item_id(subcategories_list.currentItem())
            if not sub_id:
                return
            used = 0
            if text is not None:
                try:
                    used = session.execute(text("SELECT COUNT(1) FROM products WHERE product_subcategory_id = :sid"), {'sid': int(sub_id)}).scalar() or 0
                except Exception:
                    used = 0
            if used:
                QMessageBox.warning(dlg, "Subcategory", "Subcategory is in use by products and cannot be deleted.")
                return
            try:
                session.query(ProductSubcategory).filter(ProductSubcategory.id == int(sub_id)).delete(synchronize_session=False)
                session.commit()
            except Exception:
                try:
                    session.rollback()
                except Exception:
                    pass
                return
            load_subs_for_selected()

        close_btn.clicked.connect(dlg.accept)
        add_cat_btn.clicked.connect(add_category)
        add_sub_btn.clicked.connect(add_subcategory)
        del_cat_btn.clicked.connect(delete_category)
        del_sub_btn.clicked.connect(delete_subcategory)
        categories_list.currentItemChanged.connect(lambda *_: load_subs_for_selected())

        load_lists()
        dlg.exec()

        try:
            self.load_products()
        except Exception:
            pass

    def _delete_product(self, product_id):
        try:
            product = self.controller.session.get(Product, product_id)
            if not product:
                QMessageBox.warning(self, "Error", "Product not found")
                return
            
            # Check for foreign key dependencies
            from pos_app.models.database import SaleItem, PurchaseItem
            
            # Check if product is used in any sales
            sale_items = self.controller.session.query(SaleItem).filter(
                SaleItem.product_id == product_id
            ).count()
            
            # Check if product is used in any purchases
            purchase_items = self.controller.session.query(PurchaseItem).filter(
                PurchaseItem.product_id == product_id
            ).count()
            
            if sale_items > 0 or purchase_items > 0:
                QMessageBox.warning(
                    self,
                    "Cannot Delete Product",
                    f"Cannot delete '{product.name}' because it is referenced in:\n\n"
                    f"• {sale_items} sale transaction(s)\n"
                    f"• {purchase_items} purchase transaction(s)\n\n"
                    f"You can mark it as inactive instead of deleting it."
                )
                return
            
            res = QMessageBox.question(self, "Confirm Delete", 
                                     f"Are you sure you want to delete '{product.name}'?\n\n"
                                     f"This action cannot be undone.",
                                     QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                # Delete related stock movements first
                from pos_app.models.database import StockMovement
                self.controller.session.query(StockMovement).filter(
                    StockMovement.product_id == product_id
                ).delete()
                
                # Now delete the product
                self.controller.session.delete(product)
                self.controller.session.commit()
                # Broadcast sync change so all clients refresh inventory
                try:
                    from pos_app.models.database import mark_sync_changed
                    mark_sync_changed(self.controller.session, 'products')
                    mark_sync_changed(self.controller.session, 'stock')
                    self.controller.session.commit()
                except Exception:
                    try:
                        self.controller.session.commit()
                    except Exception:
                        pass
                QMessageBox.information(self, "Success", f"Product '{product.name}' deleted successfully")
                self.load_products()
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to delete product:\n\n{str(e)}")


class ProductDialog(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.product = product
        self._last_navigation_time = 0  # Prevent rapid navigation
        self.setup_ui()
        if product:
            self.load_product_data()
    
    def keyPressEvent(self, event):
        """Handle key press events for navigation and Enter key functionality"""
        try:
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QKeyEvent
        except ImportError:
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QKeyEvent
        
        # Handle Enter key for brand, color, size, and supplier fields
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Check if brand field has focus and has text
            if self.brand_input.hasFocus() and self.brand_input.currentText().strip():
                self._add_brand_with_enter()
                return
            
            # Check if color field has focus and has text
            if self.colors_input.hasFocus() and self.colors_input.currentText().strip():
                self._add_color_with_enter()
                return
            
            # Check if size field has focus and has text
            if self.size_input.hasFocus() and self.size_input.text().strip():
                self._add_size_with_enter()
                return
            
            # Check if supplier field has focus and has text
            if self.supplier_input.hasFocus():
                if hasattr(self.supplier_input, 'search_input') and self.supplier_input.search_input.hasFocus():
                    if self.supplier_input.search_input.text().strip():
                        self._add_supplier_with_enter()
                        return
                elif self.supplier_input.currentText().strip():
                    self._add_supplier_with_enter()
                    return
        
        if isinstance(event, QKeyEvent):
            # List of input fields in order (removed desc_input)
            fields = [
                self.name_input,
                self.sku_input,
                self.barcode_input,
                self.purchase_price_input,
                self.wholesale_price_input,
                self.retail_price_input,
                self.stock_input,
                self.reorder_input,
                self.supplier_input
            ]
            
            # Check if navigation keys were pressed
            if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Tab, Qt.Key_Backtab):
                # Prevent rapid navigation - only allow one field move per 200ms
                import time
                current_time = time.time() * 1000  # Convert to milliseconds
                if current_time - self._last_navigation_time < 200:
                    return  # Block rapid navigation
                self._last_navigation_time = current_time
                
                # Find current field - check both direct focus and child focus
                current_field = None
                for i, field in enumerate(fields):
                    # Check if field has focus
                    if field.hasFocus():
                        current_field = i
                        break
                    # For SearchableComboBox, check if its search_input has focus
                    elif hasattr(field, 'search_input') and field.search_input.hasFocus():
                        current_field = i
                        break
                
                if current_field is not None:
                    if event.key() == Qt.Key_Up:
                        # Move to previous field
                        if current_field > 0:
                            prev_field = fields[current_field - 1]
                            prev_field.setFocus()
                            # For text fields, select all text
                            if hasattr(prev_field, 'selectAll'):
                                prev_field.selectAll()
                            return
                    elif event.key() == Qt.Key_Down:
                        # Move to next field
                        if current_field < len(fields) - 1:
                            next_field = fields[current_field + 1]
                            next_field.setFocus()
                            # For text fields, select all text
                            if hasattr(next_field, 'selectAll'):
                                next_field.selectAll()
                            return
                    elif event.key() == Qt.Key_Tab:
                        # Move to next field (or wrap to first)
                        next_index = (current_field + 1) % len(fields)
                        next_field = fields[next_index]
                        next_field.setFocus()
                        # For text fields, select all text
                        if hasattr(next_field, 'selectAll'):
                            next_field.selectAll()
                            return
                    elif event.key() == Qt.Key_Backtab:
                        # Move to previous field (or wrap to last)
                        prev_index = (current_field - 1) % len(fields)
                        prev_field = fields[prev_index]
                        prev_field.setFocus()
                        # For text fields, select all text
                        if hasattr(prev_field, 'selectAll'):
                            prev_field.selectAll()
                            return
        
        # Handle Enter key to save product (only for non-special fields)
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Check if any standard field has focus (excluding brand, color, size, supplier)
            standard_fields = [self.name_input, self.sku_input, self.barcode_input, 
                             self.purchase_price_input, self.wholesale_price_input, 
                             self.retail_price_input, self.stock_input, self.reorder_input]
            
            for field in standard_fields:
                if field.hasFocus():
                    self.validate_and_accept()
                    return
                # Check SearchableComboBox search input focus
                elif hasattr(field, 'search_input') and field.search_input.hasFocus():
                    self.validate_and_accept()
                    return
        
        return super().keyPressEvent(event)

    def setup_ui(self):
        self.setWindowTitle("Add Product" if not self.product else "Edit Product")
        
        # Apply professional theme sizing
        try:
            from pos_app.utils.ui_theme import UITheme
            width, height = UITheme.get_large_dialog_size()
            self.setMinimumWidth(width)
            self.setMinimumHeight(height)
            # Apply dialog-specific styling
            self.setStyleSheet(UITheme.get_dialog_stylesheet())
        except Exception:
            self.setMinimumWidth(900)
            self.setMinimumHeight(700)
        
        main_layout = QVBoxLayout(self)
        
        # Professional spacing
        try:
            from pos_app.utils.ui_theme import UITheme
            main_layout.setContentsMargins(
                UITheme.SPACING['xl'], 
                UITheme.SPACING['xl'], 
                UITheme.SPACING['xl'], 
                UITheme.SPACING['xl']
            )
            main_layout.setSpacing(UITheme.SPACING['lg'])
        except Exception:
            main_layout.setContentsMargins(20, 20, 20, 20)
            main_layout.setSpacing(16)

        # Professional scroll area
        scroll = QScrollArea()
        try:
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
        except Exception:
            try:
                scroll.setFrameShape(QFrame.Shape.NoFrame)
            except Exception:
                pass
        main_layout.addWidget(scroll, 1)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        
        # Professional container spacing
        try:
            from pos_app.utils.ui_theme import UITheme
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(UITheme.SPACING['xl'])
        except Exception:
            root.setContentsMargins(0, 0, 0, 0)
            root.setSpacing(24)
        root.setSpacing(10)
        
        self.name_input = QLineEdit()
        self.category_input = QComboBox()
        self.subcategory_input = QComboBox()
        self.brand_input = QComboBox()
        try:
            self.brand_input.setEditable(True)
            self.brand_input.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass
        self.product_type_input = QComboBox()
        try:
            self.product_type_input.addItems(["SIMPLE", "VARIANT"])
            # Connect the change handler to show/hide fields
            self.product_type_input.currentTextChanged.connect(self.on_product_type_changed)
        except Exception:
            pass
        
        # Description field removed as requested
        
        self.sku_input = QLineEdit()
        self.barcode_input = QLineEdit()

        self.unit_input = QComboBox()
        try:
            self.unit_input.setEditable(True)
        except Exception:
            pass
        try:
            self.unit_input.addItems(["pcs", "kg", "g", "l", "ml", "box", "pack", "dozen"])
        except Exception:
            pass
        
        # Add unit quantity field
        self.unit_quantity_input = QSpinBox()
        try:
            self.unit_quantity_input.setRange(1, 999999)
            self.unit_quantity_input.setValue(1)
            self.unit_quantity_input.setSuffix(" units")
            # Disable mouse wheel to prevent accidental changes
            self.unit_quantity_input.wheelEvent = lambda event: None
        except Exception:
            pass

        self.colors_input = QComboBox()
        try:
            self.colors_input.setEditable(True)
            self.colors_input.setInsertPolicy(QComboBox.NoInsert)
        except Exception:
            pass

        self.model_input = QLineEdit()
        self.size_input = QLineEdit()
        self.dimensions_input = QLineEdit()
        self.shelf_location_input = QLineEdit()
        self.warehouse_location_input = QLineEdit()

        self.tax_rate_input = NavigationDoubleSpinBox()
        try:
            self.tax_rate_input.setRange(0.0, 100.0)
            self.tax_rate_input.setDecimals(2)
            # Disable mouse wheel to prevent accidental changes
            self.tax_rate_input.wheelEvent = lambda event: None
        except Exception:
            pass

        self.discount_percentage_input = NavigationDoubleSpinBox()
        try:
            self.discount_percentage_input.setRange(0.0, 100.0)
            self.discount_percentage_input.setDecimals(2)
            # Disable mouse wheel to prevent accidental changes
            self.discount_percentage_input.wheelEvent = lambda event: None
        except Exception:
            pass

        self.notes_input = QTextEdit()
        try:
            self.notes_input.setMaximumHeight(70)
        except Exception:
            pass

        self.is_active_checkbox = QCheckBox("Active")
        try:
            self.is_active_checkbox.setChecked(True)
        except Exception:
            pass
        
        # Prevent barcode scanner Enter key from triggering generate button
        self.barcode_input.returnPressed.connect(self._on_barcode_enter)
        
        # Barcode input with generator button
        barcode_layout = QHBoxLayout()
        barcode_layout.setContentsMargins(0, 0, 0, 0)
        barcode_layout.addWidget(self.barcode_input, 1)
        barcode_gen_btn = QPushButton("🔢 Generate")
        barcode_gen_btn.setMaximumWidth(100)
        barcode_gen_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        barcode_gen_btn.clicked.connect(self._generate_barcode)
        # Prevent barcode scanner Enter key from triggering generate button
        barcode_gen_btn.setAutoDefault(False)
        barcode_gen_btn.setDefault(False)
        barcode_layout.addWidget(barcode_gen_btn)
        barcode_widget = QWidget()
        barcode_widget.setLayout(barcode_layout)
        
        self.retail_price_input = NavigationDoubleSpinBox()
        self.retail_price_input.setMaximum(1000000)
        self.retail_price_input.setMinimum(0.00)
        self.retail_price_input.setDecimals(2)
        # Disable mouse wheel to prevent accidental changes
        self.retail_price_input.wheelEvent = lambda event: None
        
        self.wholesale_price_input = NavigationDoubleSpinBox()
        self.wholesale_price_input.setMaximum(1000000)
        self.wholesale_price_input.setMinimum(0.00)
        self.wholesale_price_input.setDecimals(2)
        # Disable mouse wheel to prevent accidental changes
        self.wholesale_price_input.wheelEvent = lambda event: None
        
        self.purchase_price_input = NavigationDoubleSpinBox()
        self.purchase_price_input.setMaximum(1000000)
        self.purchase_price_input.setMinimum(0.00)
        self.purchase_price_input.setDecimals(2)
        # Disable mouse wheel to prevent accidental changes
        self.purchase_price_input.wheelEvent = lambda event: None
        
        # Use QLineEdit for stock to support expressions like "12+2"
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Enter stock quantity or expression (e.g., 12+2)")
        self.stock_input.setText("0")
        # Add validator to allow numbers and + operator
        from PySide6.QtGui import QRegularExpressionValidator
        from PySide6.QtCore import QRegularExpression
        stock_validator = QRegularExpressionValidator(QRegularExpression(r"^\d+(\+\d+)*$"))
        self.stock_input.setValidator(stock_validator)
        
        self.reorder_input = NavigationSpinBox()
        self.reorder_input.setMaximum(10000)
        self.reorder_input.setMinimum(0)
        # Disable mouse wheel to prevent accidental changes
        self.reorder_input.wheelEvent = lambda event: None
        
        # Inventory extras
        self.low_stock_alert_checkbox = QCheckBox("Low Stock Alert")
        try:
            self.low_stock_alert_checkbox.setChecked(True)
        except Exception:
            pass

        # Supplier & Packaging
        self.supplier_input = SearchableComboBox(allow_add_new=True, on_add_new_callback=self._create_new_supplier)
        self.packaging_type_input = QComboBox()
        self.weight_input = NavigationDoubleSpinBox()
        try:
            self.weight_input.setMaximum(1000000)
            self.weight_input.setMinimum(0.0)
            self.weight_input.setDecimals(3)
        except Exception:
            pass
        try:
            self.category_input.setEditable(False)
            self.subcategory_input.setEditable(False)
            self.packaging_type_input.setEditable(False)
        except Exception:
            pass
        self.category_input.setMinimumHeight(32)
        self.subcategory_input.setMinimumHeight(32)
        self.packaging_type_input.setMinimumHeight(32)

        self.add_category_btn = QPushButton("+ Add")
        self.add_subcategory_btn = QPushButton("+ Add")
        self.add_packaging_btn = QPushButton("+ Add")
        # Add buttons for Brand, Color, Size, and Suppliers
        self.add_brand_btn = QPushButton("+ Add")
        self.add_color_btn = QPushButton("+ Add")
        self.add_size_btn = QPushButton("+ Add")
        self.add_supplier_btn = QPushButton("+ Add")
        try:
            self.add_category_btn.setAutoDefault(False)
            self.add_category_btn.setDefault(False)
            self.add_subcategory_btn.setAutoDefault(False)
            self.add_subcategory_btn.setDefault(False)
            self.add_packaging_btn.setAutoDefault(False)
            self.add_packaging_btn.setDefault(False)
            # Set auto default for new buttons
            self.add_brand_btn.setAutoDefault(False)
            self.add_brand_btn.setDefault(False)
            self.add_color_btn.setAutoDefault(False)
            self.add_color_btn.setDefault(False)
            self.add_size_btn.setAutoDefault(False)
            self.add_size_btn.setDefault(False)
            self.add_supplier_btn.setAutoDefault(False)
            self.add_supplier_btn.setDefault(False)
        except Exception:
            pass
        self.add_category_btn.setMaximumWidth(70)
        self.add_subcategory_btn.setMaximumWidth(70)
        self.add_packaging_btn.setMaximumWidth(70)
        # Set max width for new buttons
        self.add_brand_btn.setMaximumWidth(70)
        self.add_color_btn.setMaximumWidth(70)
        self.add_size_btn.setMaximumWidth(70)
        self.add_supplier_btn.setMaximumWidth(70)
        self.add_category_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        self.add_subcategory_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        self.add_packaging_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        # Set styles for new buttons
        self.add_brand_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        self.add_color_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        self.add_size_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        self.add_supplier_btn.setStyleSheet("padding: 6px 10px; font-weight: 700;")
        
        try:
            from PySide6.QtWidgets import QDateEdit
        except ImportError:
            from PyQt6.QtWidgets import QDateEdit
        try:
            from PySide6.QtCore import QDate
        except ImportError:
            from PyQt6.QtCore import QDate

        self.has_expiry_checkbox = QCheckBox("Has expiry")
        try:
            self.has_expiry_checkbox.setChecked(False)
        except Exception:
            pass

        self.expiry_input = QDateEdit()
        try:
            self.expiry_input.setCalendarPopup(True)
        except Exception:
            pass
        try:
            self.expiry_input.setDisplayFormat("yyyy-MM-dd")
        except Exception:
            pass
        # Optional field: default to today but disabled unless checked
        try:
            self.expiry_input.setDate(QDate.currentDate())
        except Exception:
            pass
        try:
            self.expiry_input.setEnabled(False)
        except Exception:
            pass
        try:
            self.has_expiry_checkbox.toggled.connect(self.expiry_input.setEnabled)
        except Exception:
            pass
        
        # Populate fields list for navigation and barcode handling
        self.warranty_input = QLineEdit()

        self.fields = [
            self.name_input,
            self.category_input,
            self.subcategory_input,
            self.brand_input,
            self.product_type_input,
            self.sku_input,
            self.barcode_input,
            self.unit_input,
            self.colors_input,
            self.model_input,
            self.size_input,
            self.dimensions_input,
            self.shelf_location_input,
            self.warehouse_location_input,
            self.tax_rate_input,
            self.discount_percentage_input,
            self.purchase_price_input,
            self.wholesale_price_input,
            self.retail_price_input,
            self.stock_input,
            self.reorder_input,
            self.low_stock_alert_checkbox,
            self.supplier_input,
            self.packaging_type_input,
            self.weight_input,
            self.has_expiry_checkbox,
            self.expiry_input,
            self.warranty_input,
            self.notes_input,
            self.is_active_checkbox,
        ]

        self._categories_cache = []
        self._subcategories_cache = []
        self._packaging_types_cache = []
        self._brands_cache = []
        self._colors_cache = []
        self._load_categories_and_subcategories()
        self._load_packaging_types()
        self._load_brands()
        self._load_colors()
        try:
            self.category_input.currentIndexChanged.connect(self._on_category_changed)
        except Exception:
            pass
        try:
            self.add_category_btn.clicked.connect(self._add_new_category)
            self.add_subcategory_btn.clicked.connect(self._add_new_subcategory)
            self.add_packaging_btn.clicked.connect(self._add_new_packaging_type)
            # Add click handlers for new buttons
            self.add_brand_btn.clicked.connect(self._add_new_brand)
            self.add_color_btn.clicked.connect(self._add_new_color)
            self.add_size_btn.clicked.connect(self._add_new_size)
            self.add_supplier_btn.clicked.connect(self._add_new_supplier)
        except Exception:
            pass
        
        try:
            from pos_app.models.database import Supplier
            suppliers = []
            
            # Get session from parent controller
            if self.parent_widget and hasattr(self.parent_widget, 'controller') and hasattr(self.parent_widget.controller, 'session'):
                session = self.parent_widget.controller.session
                suppliers = session.query(Supplier).filter(Supplier.is_active == True).all()
            
            # Add suppliers to searchable dropdown
            if suppliers:
                supplier_items = [(s.name, s.id) for s in suppliers]
                self.supplier_input.set_items(supplier_items)
            else:
                self.supplier_input.set_items([])
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.supplier_input.set_items([])
        
        # SECTION 1: Basic Information
        sec1 = QGroupBox("📝 Basic Information")
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_form_layout(s1)
        except Exception:
            s1 = QFormLayout(sec1)
        cat_row = QWidget()
        cat_row_layout = QHBoxLayout(cat_row)
        cat_row_layout.setContentsMargins(0, 0, 0, 0)
        cat_row_layout.setSpacing(8)
        cat_row_layout.addWidget(self.category_input, 1)
        cat_row_layout.addWidget(self.add_category_btn, 0)
        sub_row = QWidget()
        sub_row_layout = QHBoxLayout(sub_row)
        sub_row_layout.setContentsMargins(0, 0, 0, 0)
        sub_row_layout.setSpacing(8)
        sub_row_layout.addWidget(self.subcategory_input, 1)
        sub_row_layout.addWidget(self.add_subcategory_btn, 0)
        s1.addRow("Product Name *", self.name_input)
        s1.addRow("Category", cat_row)
        s1.addRow("Subcategory", sub_row)
        
        # Add Brand field with Add button
        brand_row = QWidget()
        brand_row_layout = QHBoxLayout(brand_row)
        brand_row_layout.setContentsMargins(0, 0, 0, 0)
        brand_row_layout.setSpacing(8)
        brand_row_layout.addWidget(self.brand_input, 1)
        brand_row_layout.addWidget(self.add_brand_btn, 0)
        s1.addRow("Brand", brand_row)
        
        s1.addRow("Product Type", self.product_type_input)
        root.addWidget(sec1)

        # SECTION 2: Identification
        sec2 = QGroupBox("🏷️ Product Identification")
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_form_layout(s2)
        except Exception:
            s2 = QFormLayout(sec2)
        s2.addRow("SKU", self.sku_input)
        s2.addRow("Barcode", barcode_widget)
        # Add Unit of Measure with quantity field
        unit_row = QWidget()
        unit_row_layout = QHBoxLayout(unit_row)
        unit_row_layout.setContentsMargins(0, 0, 0, 0)
        unit_row_layout.setSpacing(8)
        unit_row_layout.addWidget(self.unit_input, 2)
        unit_row_layout.addWidget(QLabel("Qty:"), 0)
        unit_row_layout.addWidget(self.unit_quantity_input, 1)
        s2.addRow("Unit of Measure", unit_row)
        
        # Add Colors field with Add button
        colors_row = QWidget()
        colors_row_layout = QHBoxLayout(colors_row)
        colors_row_layout.setContentsMargins(0, 0, 0, 0)
        colors_row_layout.setSpacing(8)
        colors_row_layout.addWidget(self.colors_input, 1)
        colors_row_layout.addWidget(self.add_color_btn, 0)
        s2.addRow("Colors / Variants", colors_row)
        
        s2.addRow("Model", self.model_input)
        
        # Add Size field with Add button
        size_row = QWidget()
        size_row_layout = QHBoxLayout(size_row)
        size_row_layout.setContentsMargins(0, 0, 0, 0)
        size_row_layout.setSpacing(8)
        size_row_layout.addWidget(self.size_input, 1)
        size_row_layout.addWidget(self.add_size_btn, 0)
        s2.addRow("Size", size_row)
        
        s2.addRow("Dimensions", self.dimensions_input)
        
        # Add Packaging field with Add button
        pack_row = QWidget()
        pack_row_layout = QHBoxLayout(pack_row)
        pack_row_layout.setContentsMargins(0, 0, 0, 0)
        pack_row_layout.setSpacing(8)
        pack_row_layout.addWidget(self.packaging_type_input, 1)
        pack_row_layout.addWidget(self.add_packaging_btn, 0)
        s2.addRow("Packaging", pack_row)
        
        s2.addRow("Weight", self.weight_input)
        root.addWidget(sec2)

        # SECTION 3: Pricing
        sec3 = QGroupBox("💰 Pricing Information")
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_form_layout(s3)
        except Exception:
            s3 = QFormLayout(sec3)
        s3.addRow("Purchase Price *", self.purchase_price_input)
        s3.addRow("Wholesale Price *", self.wholesale_price_input)
        s3.addRow("Retail Price *", self.retail_price_input)
        root.addWidget(sec3)

        # SECTION 4: Inventory
        sec4 = QGroupBox("📦 Inventory Management")
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_form_layout(s4)
        except Exception:
            s4 = QFormLayout(sec4)
        s4.addRow("Stock *", self.stock_input)
        s4.addRow("Reorder Level", self.reorder_input)
        s4.addRow("", self.low_stock_alert_checkbox)
        root.addWidget(sec4)

        # SECTION 5: Supplier
        sec5 = QGroupBox("📋 Supplier Information")
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_form_layout(s5)
        except Exception:
            s5 = QFormLayout(sec5)
        
        # Add Supplier field with Add button
        supplier_row = QWidget()
        supplier_row_layout = QHBoxLayout(supplier_row)
        supplier_row_layout.setContentsMargins(0, 0, 0, 0)
        supplier_row_layout.setSpacing(8)
        supplier_row_layout.addWidget(self.supplier_input, 1)
        supplier_row_layout.addWidget(self.add_supplier_btn, 0)
        
        s5.addRow("Supplier *", supplier_row)
        root.addWidget(sec5)

        # SECTION 6: Warranty & Expiry
        sec6 = QGroupBox("⏰ Warranty & Expiry")
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_form_layout(s6)
        except Exception:
            s6 = QFormLayout(sec6)
        expiry_row = QWidget()
        expiry_row_layout = QHBoxLayout(expiry_row)
        expiry_row_layout.setContentsMargins(0, 0, 0, 0)
        expiry_row_layout.setSpacing(8)
        expiry_row_layout.addWidget(self.has_expiry_checkbox, 0)
        expiry_row_layout.addWidget(self.expiry_input, 1)
        s6.addRow("Expiry", expiry_row)
        s6.addRow("Warranty", self.warranty_input)
        s6.addRow("Shelf Location", self.shelf_location_input)
        s6.addRow("Warehouse Location", self.warehouse_location_input)
        s6.addRow("Tax Rate (%)", self.tax_rate_input)
        s6.addRow("Discount (%)", self.discount_percentage_input)
        s6.addRow("Notes", self.notes_input)
        s6.addRow("", self.is_active_checkbox)
        root.addWidget(sec6)

        root.addStretch()
        
        # Removed validation info label for more vertical space
        
        # Professional dialog buttons
        buttons_layout = QHBoxLayout()
        try:
            from pos_app.utils.ui_theme import UITheme
            buttons_layout.setContentsMargins(0, UITheme.SPACING['lg'], 0, 0)
            buttons_layout.setSpacing(UITheme.SPACING['md'])
        except Exception:
            buttons_layout.setContentsMargins(0, 16, 0, 0)
            buttons_layout.setSpacing(12)
        
        save_btn = QPushButton("💾 Save Product")
        cancel_btn = QPushButton("❌ Cancel")
        
        # Apply professional button styling
        try:
            from pos_app.utils.ui_theme import UITheme
            UITheme.style_button(save_btn, 'success')
            UITheme.style_button(cancel_btn, 'secondary')
        except Exception:
            pass
        
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        main_layout.addLayout(buttons_layout)
        
        # Initialize product type field visibility
        # Default to SIMPLE and hide variant fields
        if hasattr(self, 'product_type_input'):
            current_type = self.product_type_input.currentText()
            if not current_type:
                self.product_type_input.setCurrentText("SIMPLE")
                current_type = "SIMPLE"
            self.on_product_type_changed(current_type)

    def on_product_type_changed(self, product_type):
        """Handle product type change to show/hide fields based on Simple vs Variant"""
        try:
            is_simple = product_type.upper() == "SIMPLE"
            
            # Find the Product Identification group box
            sec2 = None
            parent = self.unit_input.parent()
            while parent is not None:
                if isinstance(parent, QGroupBox) and "Product Identification" in parent.title():
                    sec2 = parent
                    break
                parent = parent.parent()
            
            if sec2:
                layout = sec2.layout()
                if isinstance(layout, QFormLayout):
                    # For QFormLayout, we need to hide entire rows
                    # Row indices: 0=SKU, 1=Barcode, 2=Unit, 3=Colors, 4=Model, 5=Size, 6=Dimensions, 7=Packaging, 8=Weight
                    
                    # Hide these rows for SIMPLE products, show for VARIANT products
                    rows_to_hide_for_simple = [2, 3, 4, 5, 6, 7]  # Unit, Colors, Model, Size, Dimensions, Packaging
                    
                    for row_index in rows_to_hide_for_simple:
                        try:
                            # Hide label
                            label_item = layout.itemAt(row_index, QFormLayout.LabelRole)
                            if label_item and label_item.widget():
                                label_item.widget().setVisible(not is_simple)
                            
                            # Hide field
                            field_item = layout.itemAt(row_index, QFormLayout.FieldRole)
                            if field_item and field_item.widget():
                                field_item.widget().setVisible(not is_simple)
                        except Exception as e:
                            print(f"Error hiding row {row_index}: {e}")
                
                else:
                    # Fallback for other layout types
                    variant_fields = [
                        self.unit_input, self.unit_quantity_input,
                        self.colors_input, self.model_input, 
                        self.size_input, self.dimensions_input, self.packaging_type_input
                    ]
                    for field in variant_fields:
                        field.setVisible(not is_simple)
            
        except Exception as e:
            print(f"Error handling product type change: {e}")

    def _get_session(self):
        try:
            if self.parent_widget and hasattr(self.parent_widget, 'controller') and hasattr(self.parent_widget.controller, 'session'):
                return self.parent_widget.controller.session
        except Exception:
            pass
        return None

    def _load_categories_and_subcategories(self):
        try:
            session = self._get_session()
            if session is None:
                try:
                    self.category_input.clear()
                    self.subcategory_input.clear()
                    self.category_input.addItem("(None)", None)
                    self.subcategory_input.addItem("(None)", None)
                except Exception:
                    pass
                return

            from pos_app.models.database import ProductCategory, ProductSubcategory

            cats = session.query(ProductCategory).order_by(ProductCategory.name.asc()).all()
            subs = session.query(ProductSubcategory).order_by(ProductSubcategory.name.asc()).all()
            self._categories_cache = cats or []
            self._subcategories_cache = subs or []

            try:
                self.category_input.blockSignals(True)
            except Exception:
                pass
            try:
                self.category_input.clear()
                self.category_input.addItem("(None)", None)
                for c in self._categories_cache:
                    self.category_input.addItem(getattr(c, 'name', '') or '', getattr(c, 'id', None))
            except Exception:
                pass
            try:
                self.category_input.blockSignals(False)
            except Exception:
                pass

            self._on_category_changed()
        except Exception:
            try:
                self.category_input.clear()
                self.subcategory_input.clear()
                self.category_input.addItem("(None)", None)
                self.subcategory_input.addItem("(None)", None)
            except Exception:
                pass

    def _on_category_changed(self, *args):
        try:
            try:
                cat_id = self.category_input.currentData()
            except Exception:
                cat_id = None

            try:
                if cat_id is not None:
                    cat_id = int(cat_id)
            except Exception:
                cat_id = None

            try:
                self.subcategory_input.blockSignals(True)
            except Exception:
                pass

            try:
                self.subcategory_input.clear()
                self.subcategory_input.addItem("(None)", None)
                for sc in (self._subcategories_cache or []):
                    try:
                        if cat_id is None:
                            continue
                        if int(getattr(sc, 'category_id', 0) or 0) == int(cat_id):
                            self.subcategory_input.addItem(getattr(sc, 'name', '') or '', getattr(sc, 'id', None))
                    except Exception:
                        continue
            except Exception:
                pass

            try:
                self.subcategory_input.blockSignals(False)
            except Exception:
                pass

            # If previously selected subcategory is not in this category anymore, reset to (None)
            try:
                cur_sub = self.subcategory_input.currentData()
            except Exception:
                cur_sub = None
            if cur_sub is not None:
                found = False
                try:
                    for i in range(self.subcategory_input.count()):
                        if self.subcategory_input.itemData(i) == cur_sub:
                            found = True
                            break
                except Exception:
                    found = True
                if not found:
                    try:
                        self.subcategory_input.setCurrentIndex(0)
                    except Exception:
                        pass
        except Exception:
            pass

    def _add_new_category(self):
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog

        session = self._get_session()
        if session is None:
            return

        name, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        try:
            from pos_app.models.database import ProductCategory
            existing = session.query(ProductCategory).filter(ProductCategory.name.ilike(name)).first()
            if existing is None:
                obj = ProductCategory(name=name)
                session.add(obj)
                session.commit()
            else:
                obj = existing
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
            return

        self._load_categories_and_subcategories()
        try:
            # Select newly created
            for i in range(self.category_input.count()):
                if self.category_input.itemData(i) == getattr(obj, 'id', None):
                    self.category_input.setCurrentIndex(i)
                    break
        except Exception:
            pass

    def _add_new_subcategory(self):
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog

        session = self._get_session()
        if session is None:
            return

        try:
            cat_id = self.category_input.currentData()
        except Exception:
            cat_id = None
        if not cat_id:
            return

        name, ok = QInputDialog.getText(self, "Add Subcategory", "Subcategory name:")
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        try:
            from pos_app.models.database import ProductSubcategory
            existing = session.query(ProductSubcategory).filter(
                ProductSubcategory.category_id == int(cat_id),
                ProductSubcategory.name.ilike(name)
            ).first()
            if existing is None:
                obj = ProductSubcategory(category_id=int(cat_id), name=name)
                session.add(obj)
                session.commit()
            else:
                obj = existing
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
            return

        self._load_categories_and_subcategories()
        try:
            # Ensure category selected and then select newly created subcategory
            self._on_category_changed()
            for i in range(self.subcategory_input.count()):
                if self.subcategory_input.itemData(i) == getattr(obj, 'id', None):
                    self.subcategory_input.setCurrentIndex(i)
                    break
        except Exception:
            pass
    
    def _load_packaging_types(self):
        try:
            session = self._get_session()
            if session is None:
                try:
                    self.packaging_type_input.clear()
                    self.packaging_type_input.addItem("(None)", None)
                except Exception:
                    pass
                return

            from pos_app.models.database import ProductPackagingType
            types = session.query(ProductPackagingType).order_by(ProductPackagingType.name.asc()).all()
            self._packaging_types_cache = types or []

            try:
                self.packaging_type_input.blockSignals(True)
            except Exception:
                pass
            try:
                self.packaging_type_input.clear()
                self.packaging_type_input.addItem("(None)", None)
                for t in (self._packaging_types_cache or []):
                    self.packaging_type_input.addItem(getattr(t, 'name', '') or '', getattr(t, 'id', None))
            except Exception:
                pass
            try:
                self.packaging_type_input.blockSignals(False)
            except Exception:
                pass

            # Restore selection when editing
            try:
                if self.product is not None:
                    pid = getattr(self.product, 'packaging_type_id', None)
                else:
                    pid = None
            except Exception:
                pid = None
            try:
                if pid is not None:
                    for i in range(self.packaging_type_input.count()):
                        if self.packaging_type_input.itemData(i) == pid:
                            self.packaging_type_input.setCurrentIndex(i)
                            break
            except Exception:
                pass
        except Exception:
            try:
                self.packaging_type_input.clear()
                self.packaging_type_input.addItem("(None)", None)
            except Exception:
                pass

    def _add_new_packaging_type(self):
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog

        session = self._get_session()
        if session is None:
            return

        name, ok = QInputDialog.getText(self, "Add Packaging Type", "Packaging type name:")
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        try:
            from pos_app.models.database import ProductPackagingType
            existing = session.query(ProductPackagingType).filter(ProductPackagingType.name.ilike(name)).first()
            if existing is None:
                obj = ProductPackagingType(name=name)
                session.add(obj)
                session.commit()
            else:
                obj = existing
        except Exception:
            try:
                session.rollback()
            except Exception:
                pass
            return

        self._load_packaging_types()
        try:
            for i in range(self.packaging_type_input.count()):
                if self.packaging_type_input.itemData(i) == getattr(obj, 'id', None):
                    self.packaging_type_input.setCurrentIndex(i)
                    break
        except Exception:
            pass

    def _load_brands(self):
        """Load unique brand values from existing products"""
        try:
            session = self._get_session()
            if session is None:
                return

            from pos_app.models.database import Product
            brands = session.query(Product.brand).distinct().filter(Product.brand.isnot(None), Product.brand != '').order_by(Product.brand.asc()).all()
            self._brands_cache = [b[0] for b in brands if b[0]]

            self.brand_input.clear()
            self.brand_input.addItem("")  # Empty option
            for brand in self._brands_cache:
                self.brand_input.addItem(brand)
            
            # Enable autocomplete
            try:
                from PySide6.QtWidgets import QCompleter
                from PySide6.QtCore import Qt
            except ImportError:
                from PyQt6.QtWidgets import QCompleter
                from PyQt6.QtCore import Qt
            
            completer = QCompleter(self._brands_cache)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.brand_input.setCompleter(completer)
        except Exception:
            pass

    def _load_colors(self):
        """Load unique color values from existing products"""
        try:
            session = self._get_session()
            if session is None:
                return

            from pos_app.models.database import Product
            colors = session.query(Product.colors).distinct().filter(Product.colors.isnot(None), Product.colors != '').order_by(Product.colors.asc()).all()
            self._colors_cache = [c[0] for c in colors if c[0]]

            self.colors_input.clear()
            self.colors_input.addItem("")  # Empty option
            for color in self._colors_cache:
                self.colors_input.addItem(color)
            
            # Enable autocomplete
            try:
                from PySide6.QtWidgets import QCompleter
                from PySide6.QtCore import Qt
            except ImportError:
                from PyQt6.QtWidgets import QCompleter
                from PyQt6.QtCore import Qt
            
            completer = QCompleter(self._colors_cache)
            completer.setCaseSensitivity(Qt.CaseInsensitive)
            completer.setFilterMode(Qt.MatchContains)
            self.colors_input.setCompleter(completer)
        except Exception:
            pass

    def _add_new_size(self):
        """Add new size to the size input"""
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Add Size", "Size value:")
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        # Add to cache and combo box
        if name not in self._sizes_cache:
            self._sizes_cache.append(name)
            self.size_input.setText(name)
    
    def _add_size_with_enter(self):
        """Add size using Enter key without dialog"""
        try:
            current_text = self.size_input.text().strip()
            if not current_text:
                return
            
            # Add to cache if not exists
            if current_text not in self._sizes_cache:
                self._sizes_cache.append(current_text)
            
            # Move to next field
            self.dimensions_input.setFocus()
        except Exception:
            pass

    def _add_brand_with_enter(self):
        """Add brand using Enter key without dialog"""
        try:
            current_text = self.brand_input.currentText().strip()
            if not current_text:
                return
            
            # Add to cache and combo box if not exists
            if current_text not in self._brands_cache:
                self._brands_cache.append(current_text)
                self.brand_input.addItem(current_text)
            
            # Move to next field
            self.product_type_input.setFocus()
        except Exception:
            pass

    def _add_new_color(self):
        """Add new color to the color combo box"""
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Add Color", "Color name:")
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        # Add to cache and combo box
        if name not in self._colors_cache:
            self._colors_cache.append(name)
            self.colors_input.addItem(name)
            self.colors_input.setCurrentText(name)
    
    def _add_color_with_enter(self):
        """Add color using Enter key without dialog"""
        try:
            current_text = self.colors_input.currentText().strip()
            if not current_text:
                return
            
            # Add to cache and combo box if not exists
            if current_text not in self._colors_cache:
                self._colors_cache.append(current_text)
                self.colors_input.addItem(current_text)
            
            # Move to next field
            self.model_input.setFocus()
        except Exception:
            pass

    def _add_new_size(self):
        """Add new size to the size input"""
        try:
            from PySide6.QtWidgets import QInputDialog
        except ImportError:
            from PyQt6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(self, "Add Size", "Size value:")
        if not ok:
            return
        name = (name or "").strip()
        if not name:
            return

        # Set the size input
        self.size_input.setText(name)

    def _add_new_supplier(self):
        """Add new supplier using the existing supplier dialog"""
        try:
            from pos_app.views.suppliers import SupplierDialog
            dialog = SupplierDialog(self)
            if dialog.exec() == QDialog.Accepted:
                # Reload suppliers to get the new one
                self._load_suppliers()
                # Try to select the newly added supplier
                if hasattr(dialog, 'supplier') and dialog.supplier:
                    for i in range(self.supplier_input.count()):
                        if self.supplier_input.itemData(i) == dialog.supplier.id:
                            self.supplier_input.setCurrentIndex(i)
                            break
        except Exception as e:
            print(f"Error adding supplier: {e}")
    
    def _add_supplier_with_enter(self):
        """Add supplier using Enter key without dialog"""
        try:
            current_text = self.supplier_input.currentText().strip()
            if not current_text:
                return
            
            # Create new supplier directly
            self._create_new_supplier(current_text)
            
            # Move to next field
            self.purchase_price_input.setFocus()
        except Exception:
            pass

    def validate_and_accept(self):
        """Validate all inputs before accepting"""
        # Use a binding-agnostic QMessageBox import so PyQt6 works even
        # when PySide6 is not installed.
        try:
            from PySide6.QtWidgets import QMessageBox
        except ImportError:
            from PyQt6.QtWidgets import QMessageBox
        
        errors = []
        
        # Validate name
        name = self.name_input.text().strip()
        if not name:
            errors.append("• Product name is required")
        elif len(name) < 2:
            errors.append("• Product name must be at least 2 characters")
        
        # Category is now optional (not required)
        # SKU is now optional and can be duplicated
        # No validation needed for SKU or Category
        
        # Check for duplicate barcode
        barcode = self.barcode_input.text().strip()
        if barcode and hasattr(self.parent(), 'controller'):
            try:
                from pos_app.models.database import Product
                existing = self.parent().controller.session.query(Product).filter(
                    Product.barcode == barcode
                ).first()
                if existing and (not self.product or existing.id != self.product.id):
                    errors.append(f"• Barcode '{barcode}' is already used by another product")
            except Exception:
                pass
        
        # Validate prices
        purchase_price = self.purchase_price_input.value()
        wholesale_price = self.wholesale_price_input.value()
        retail_price = self.retail_price_input.value()
        
        if purchase_price <= 0:
            errors.append("• Purchase price must be greater than zero")
        if wholesale_price <= 0:
            errors.append("• Wholesale price must be greater than zero")
        if retail_price <= 0:
            errors.append("• Retail price must be greater than zero")
        
        # Validate price hierarchy
        if purchase_price > 0 and wholesale_price > 0 and purchase_price > wholesale_price:
            errors.append(f"• Purchase price (Rs {purchase_price:,.2f}) cannot be greater than wholesale price (Rs {wholesale_price:,.2f})\n  You will make a LOSS!")
        
        if wholesale_price > 0 and retail_price > 0 and wholesale_price > retail_price:
            errors.append(f"• Wholesale price (Rs {wholesale_price:,.2f}) cannot be greater than retail price (Rs {retail_price:,.2f})")
        
        if purchase_price > 0 and retail_price > 0 and purchase_price > retail_price:
            errors.append(f"• Purchase price (Rs {purchase_price:,.2f}) cannot be greater than retail price (Rs {retail_price:,.2f})\n  You will make a LOSS!")
        
        # Validate stock - handle expressions like "12+2"
        stock_text = self.stock_input.text().strip()
        try:
            if '+' in stock_text:
                stock = int(eval(stock_text, {"__builtins__": {}}, {}))
            else:
                stock = int(stock_text) if stock_text else 0
        except:
            stock = 0
        
        reorder = self.reorder_input.value()
        
        if stock < 0:
            errors.append("• Stock level cannot be negative")
        if reorder < 0:
            errors.append("• Reorder level cannot be negative")

        # Supplier required
        try:
            if safe_get_current_data(self.supplier_input) in (None, 0, "", "None"):
                errors.append("• Supplier is required")
        except Exception:
            errors.append("• Supplier is required")
        
        # Validate expiry date (optional)
        try:
            from PySide6.QtCore import QDate
        except ImportError:
            try:
                from PyQt6.QtCore import QDate
            except Exception:
                QDate = None
        try:
            min_d = None
            try:
                min_d = self.expiry_input.minimumDate()
            except Exception:
                min_d = None
            if min_d is not None and QDate is not None:
                cur_d = None
                try:
                    cur_d = self.expiry_input.date()
                except Exception:
                    cur_d = None
                # If user picked a date earlier than our sentinel, treat as empty
                if cur_d is not None and cur_d < min_d:
                    pass
        except Exception:
            pass
        
        if errors:
            QMessageBox.warning(
                self,
                "Validation Errors",
                "Please fix the following errors:\n\n" + "\n".join(errors)
            )
            return
        
        self.accept()
    
    def _load_suppliers(self):
        """Reload suppliers in the supplier dropdown"""
        try:
            from pos_app.models.database import Supplier
            suppliers = []
            
            # Get session from parent controller
            if self.parent_widget and hasattr(self.parent_widget, 'controller') and hasattr(self.parent_widget.controller, 'session'):
                session = self.parent_widget.controller.session
                suppliers = session.query(Supplier).filter(Supplier.is_active == True).all()
            
            # Update supplier dropdown
            if suppliers:
                supplier_items = [(s.name, s.id) for s in suppliers]
                self.supplier_input.set_items(supplier_items)
            else:
                self.supplier_input.set_items([])
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.supplier_input.set_items([])
    
    def _create_new_supplier(self, supplier_name):
        """Create a new supplier and return its ID"""
        try:
            from pos_app.models.database import Supplier
            from pos_app.database.db_utils import get_db_session
            
            with get_db_session() as session:
                # Check if supplier already exists
                existing = session.query(Supplier).filter(Supplier.name == supplier_name).first()
                if existing:
                    # Reload suppliers to ensure dropdown is up to date
                    self._load_suppliers()
                    return existing.id
                
                # Create new supplier
                new_supplier = Supplier(
                    name=supplier_name,
                    contact="",
                    email="",
                    address="",
                    city="",
                    state="",
                    postal_code="",
                    country="",
                    tax_number="",
                    payment_terms="",
                    notes=f"Created from product entry",
                    is_active=True
                )
                session.add(new_supplier)
                session.commit()
                
                new_id = new_supplier.id
                
                # Reload suppliers to show the newly added one
                self._load_suppliers()
                
                return new_id
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return None
    
    def _on_barcode_enter(self):
        """Handle Enter key in barcode input - move to next field instead of generating barcode"""
        # Find current field index
        current_widget = self.focusWidget()
        if current_widget == self.barcode_input and hasattr(self, 'fields'):
            current_idx = self.fields.index(current_widget) if current_widget in self.fields else -1
            if current_idx >= 0 and current_idx < len(self.fields) - 1:
                # Move to next field
                next_field = self.fields[current_idx + 1]
                next_field.setFocus()
                if hasattr(next_field, 'selectAll'):
                    next_field.selectAll()
    
    def _generate_barcode(self):
        """Generate a random barcode"""
        import random
        import time
        
        # Generate a 12-digit barcode (EAN-12 format)
        # First digit is check digit (we'll use 0)
        # Next 10 digits are random
        # Last digit is check digit
        
        barcode = str(int(time.time() * 1000) % 1000000000).zfill(10)
        
        # Calculate check digit using EAN-13 algorithm
        digits = [int(d) for d in barcode]
        odd_sum = sum(digits[i] for i in range(0, len(digits), 2))
        even_sum = sum(digits[i] for i in range(1, len(digits), 2))
        total = odd_sum + even_sum * 3
        check_digit = (10 - (total % 10)) % 10
        
        full_barcode = barcode + str(check_digit)
        self.barcode_input.setText(full_barcode)

    def load_product_data(self):
        if not self.product:
            return
        self.name_input.setText(self.product.name or "")
        try:
            brand_val = getattr(self.product, 'brand', '') or ''
            if brand_val:
                self.brand_input.setCurrentText(brand_val)
        except Exception:
            pass
        try:
            colors_val = getattr(self.product, 'colors', '') or ''
            if colors_val:
                self.colors_input.setCurrentText(colors_val)
        except Exception:
            pass
        try:
            self.model_input.setText((getattr(self.product, 'model', '') or ''))
        except Exception:
            pass
        try:
            self.size_input.setText((getattr(self.product, 'size', '') or ''))
        except Exception:
            pass
        try:
            self.dimensions_input.setText((getattr(self.product, 'dimensions', '') or ''))
        except Exception:
            pass
        try:
            self.shelf_location_input.setText((getattr(self.product, 'shelf_location', '') or ''))
        except Exception:
            pass
        try:
            self.warehouse_location_input.setText((getattr(self.product, 'warehouse_location', '') or ''))
        except Exception:
            pass
        try:
            tr = getattr(self.product, 'tax_rate', None)
            if tr is not None:
                self.tax_rate_input.setValue(float(tr))
        except Exception:
            pass
        try:
            dp = getattr(self.product, 'discount_percentage', None)
            if dp is not None:
                self.discount_percentage_input.setValue(float(dp))
        except Exception:
            pass
        try:
            self.notes_input.setPlainText((getattr(self.product, 'notes', '') or ''))
        except Exception:
            try:
                self.notes_input.setText((getattr(self.product, 'notes', '') or ''))
            except Exception:
                pass
        try:
            ia = getattr(self.product, 'is_active', None)
            if ia is not None:
                self.is_active_checkbox.setChecked(bool(ia))
        except Exception:
            pass
        try:
            pt = (getattr(self.product, 'product_type', None) or '').strip().upper()
            if pt:
                idx = self.product_type_input.findText(pt)
                if idx >= 0:
                    self.product_type_input.setCurrentIndex(idx)
                    # Trigger the product type change handler to show/hide fields
                    self.on_product_type_changed(pt)
        except Exception:
            pass
        try:
            u = (getattr(self.product, 'unit', None) or '').strip()
            if u:
                idx = self.unit_input.findText(u)
                if idx >= 0:
                    self.unit_input.setCurrentIndex(idx)
                else:
                    try:
                        self.unit_input.setCurrentText(u)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            w = getattr(self.product, 'weight', None)
            if w is not None:
                self.weight_input.setValue(float(w))
        except Exception:
            pass
        try:
            self.warranty_input.setText((getattr(self.product, 'warranty', '') or ''))
        except Exception:
            pass
        try:
            lsa = getattr(self.product, 'low_stock_alert', None)
            if lsa is not None:
                self.low_stock_alert_checkbox.setChecked(bool(lsa))
        except Exception:
            pass
        self.sku_input.setText(self.product.sku or "")
        self.barcode_input.setText(self.product.barcode or "")
        self.purchase_price_input.setValue(self.product.purchase_price or 0.01)
        self.wholesale_price_input.setValue(self.product.wholesale_price or 0.01)
        self.retail_price_input.setValue(self.product.retail_price or 0.01)
        self.stock_input.setText(str(int(self.product.stock_level or 0)))
        self.reorder_input.setValue(self.product.reorder_level or 0)

        # Packaging type selection
        try:
            ptype_id = getattr(self.product, 'packaging_type_id', None)
        except Exception:
            ptype_id = None
        try:
            if ptype_id is not None:
                for i in range(self.packaging_type_input.count()):
                    if self.packaging_type_input.itemData(i) == ptype_id:
                        self.packaging_type_input.setCurrentIndex(i)
                        break
        except Exception:
            pass

        # Category/Subcategory dropdown selection (new FK fields with legacy fallback)
        try:
            cat_id = getattr(self.product, 'product_category_id', None)
        except Exception:
            cat_id = None
        try:
            sub_id = getattr(self.product, 'product_subcategory_id', None)
        except Exception:
            sub_id = None

        # Prefer selecting by FK ids
        try:
            if cat_id is not None:
                for i in range(self.category_input.count()):
                    if self.category_input.itemData(i) == cat_id:
                        self.category_input.setCurrentIndex(i)
                        break
        except Exception:
            pass

        # Populate subcategories for selected category then select subcategory
        try:
            self._on_category_changed()
        except Exception:
            pass
        try:
            if sub_id is not None:
                for i in range(self.subcategory_input.count()):
                    if self.subcategory_input.itemData(i) == sub_id:
                        self.subcategory_input.setCurrentIndex(i)
                        break
        except Exception:
            pass

        # Fallback: match legacy text values
        try:
            legacy_cat = (getattr(self.product, 'category', '') or '').strip()
            if legacy_cat and (cat_id is None):
                for i in range(self.category_input.count()):
                    if (self.category_input.itemText(i) or '').strip().lower() == legacy_cat.lower():
                        self.category_input.setCurrentIndex(i)
                        self._on_category_changed()
                        break
        except Exception:
            pass
        try:
            legacy_sub = (getattr(self.product, 'subcategory', '') or '').strip()
            if legacy_sub and (sub_id is None):
                for i in range(self.subcategory_input.count()):
                    if (self.subcategory_input.itemText(i) or '').strip().lower() == legacy_sub.lower():
                        self.subcategory_input.setCurrentIndex(i)
                        break
        except Exception:
            pass

        # Expiry (stored as YYYY-MM-DD string, optional)
        try:
            from PySide6.QtCore import QDate
        except ImportError:
            from PyQt6.QtCore import QDate
        try:
            exp = (getattr(self.product, 'expiry_date', '') or '').strip()
            if exp:
                d = QDate.fromString(exp, "yyyy-MM-dd")
                if d.isValid():
                    try:
                        self.has_expiry_checkbox.setChecked(True)
                    except Exception:
                        pass
                    try:
                        self.expiry_input.setEnabled(True)
                    except Exception:
                        pass
                    self.expiry_input.setDate(d)
            else:
                try:
                    self.has_expiry_checkbox.setChecked(False)
                except Exception:
                    pass
                try:
                    self.expiry_input.setEnabled(False)
                except Exception:
                    pass
                try:
                    self.expiry_input.setDate(QDate.currentDate())
                except Exception:
                    pass
        except Exception:
            pass

        # Supplier selection
        try:
            if getattr(self.product, 'supplier_id', None):
                self.supplier_input.set_selected_by_id(self.product.supplier_id)
        except Exception:
            pass
        
        # Initialize product type field visibility
        # For new products, default to SIMPLE and hide variant fields
        if not self.product:
            self.product_type_input.setCurrentText("SIMPLE")
            self.on_product_type_changed("SIMPLE")
    
    def keyPressEvent(self, event):
        """Handle key press events for navigation and Enter key functionality"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Handle Enter key for brand, color, size, and supplier fields
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Check if brand field has focus and has text
            if self.brand_input.hasFocus() and self.brand_input.currentText().strip():
                self._add_brand_with_enter()
                return
            
            # Check if color field has focus and has text
            if self.colors_input.hasFocus() and self.colors_input.currentText().strip():
                self._add_color_with_enter()
                return
            
            # Check if size field has focus and has text
            if self.size_input.hasFocus() and self.size_input.text().strip():
                self._add_size_with_enter()
                return
            
            # Check if supplier field has focus and has text
            if self.supplier_input.hasFocus():
                if hasattr(self.supplier_input, 'search_input') and self.supplier_input.search_input.hasFocus():
                    if self.supplier_input.search_input.text().strip():
                        self._add_supplier_with_enter()
                        return
                elif self.supplier_input.currentText().strip():
                    self._add_supplier_with_enter()
                    return
        
        # List of input fields in order
        fields = [
            self.name_input,
            self.sku_input,
            self.barcode_input,
            self.purchase_price_input,
            self.wholesale_price_input,
            self.retail_price_input,
            self.stock_input,
            self.reorder_input,
            self.supplier_input
        ]
        
        # Check if navigation keys were pressed
        if event.key() in (Qt.Key_Up, Qt.Key_Down, Qt.Key_Tab, Qt.Key_Backtab):
            # Prevent rapid navigation - only allow one field move per 200ms
            import time
            current_time = time.time() * 1000  # Convert to milliseconds
            if current_time - self._last_navigation_time < 200:
                return  # Block rapid navigation
            self._last_navigation_time = current_time
            
            # Find current field - check both direct focus and child focus
            current_field = None
            for i, field in enumerate(fields):
                # Check if field has focus
                if field.hasFocus():
                    current_field = i
                    break
                # For SearchableComboBox, check if its search_input has focus
                elif hasattr(field, 'search_input') and field.search_input.hasFocus():
                    current_field = i
                    break
            
            if current_field is not None:
                if event.key() == Qt.Key_Up:
                    # Move to previous field
                    if current_field > 0:
                        prev_field = fields[current_field - 1]
                        prev_field.setFocus()
                        # For text fields, select all text
                        if hasattr(prev_field, 'selectAll'):
                            prev_field.selectAll()
                        return
                elif event.key() == Qt.Key_Down:
                    # Move to next field
                    if current_field < len(fields) - 1:
                        next_field = fields[current_field + 1]
                        next_field.setFocus()
                        # For text fields, select all text
                        if hasattr(next_field, 'selectAll'):
                            next_field.selectAll()
                        return
                elif event.key() == Qt.Key_Tab:
                    # Move to next field (or wrap to first)
                    next_index = (current_field + 1) % len(fields)
                    next_field = fields[next_index]
                    next_field.setFocus()
                    # For text fields, select all text
                    if hasattr(next_field, 'selectAll'):
                        next_field.selectAll()
                    return
                elif event.key() == Qt.Key_Backtab:
                    # Move to previous field (or wrap to last)
                    prev_index = (current_field - 1) % len(fields)
                    prev_field = fields[prev_index]
                    prev_field.setFocus()
                    # For text fields, select all text
                    if hasattr(prev_field, 'selectAll'):
                        prev_field.selectAll()
                    return
        
        # For Enter key on standard fields, only move to next field (never close dialog)
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Find current field
            current_field = None
            for i, field in enumerate(fields):
                # Check if field has focus
                if field.hasFocus():
                    current_field = i
                    break
                # For SearchableComboBox, check if its search_input has focus
                elif hasattr(field, 'search_input') and field.search_input.hasFocus():
                    current_field = i
                    break
            
            if current_field is not None:
                # Always move to next field (wrap around if at last field)
                next_index = (current_field + 1) % len(fields)
                next_field = fields[next_index]
                next_field.setFocus()
                if hasattr(next_field, 'selectAll'):
                    next_field.selectAll()
                return
            else:
                # If no field has focus, move to first field
                if fields:
                    fields[0].setFocus()
                    if hasattr(fields[0], 'selectAll'):
                        fields[0].selectAll()
                return
        
        # For other keys, use default handling
        super().keyPressEvent(event)
