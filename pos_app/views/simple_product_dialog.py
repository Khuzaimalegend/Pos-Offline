try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QListWidget, QListWidgetItem, QCompleter
    )
    from PySide6.QtCore import Signal, Qt, QTimer, QStringListModel
    from PySide6.QtGui import QColor
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QListWidget, QListWidgetItem, QCompleter
    )
    from PyQt6.QtCore import pyqtSignal as Signal, Qt, QTimer, QStringListModel
    from PyQt6.QtGui import QColor
from pos_app.models.database import Product
from pos_app.views.suppliers import SupplierDialog
from pos_app.models.database import Supplier


class SimpleComboBox(QComboBox):
    """Simple QComboBox that works well with arrow navigation"""
    def keyPressEvent(self, event):
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # Don't handle Up/Down arrows - let parent dialog handle them for field navigation
        if event.key() in (Qt.Key_Up, Qt.Key_Down):
            event.ignore()
            return
        
        # Handle other keys normally
        super().keyPressEvent(event)


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
        
        low_btn = QPushButton("⚠️ Low Stock")
        low_btn.setToolTip("Show products at or below reorder level")
        low_btn.setProperty('accent', 'orange')
        low_btn.setMinimumHeight(44)
        low_btn.clicked.connect(self.show_low_stock_only)
        
        toolbar_layout.addWidget(add_btn)
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

        # Products Table (removed Actions column)
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "SKU", "Name", "Description", "Retail Price",
            "Wholesale Price", "Stock Level"
        ])
        
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
        
        layout.addWidget(self.table)

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
            filtered = [p for p in self._products_cache if text in (p.name or '').lower() or text in (p.sku or '').lower()]
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
                    description=dialog.desc_input.text(),
                    sku=dialog.sku_input.text(),
                    barcode=(dialog.barcode_input.text().strip() or None),
                    purchase_price=dialog.purchase_price_input.value(),
                    wholesale_price=dialog.wholesale_price_input.value(),
                    retail_price=dialog.retail_price_input.value(),
                    stock_level=dialog._parse_stock_value(dialog.stock_input.text()),
                    reorder_level=dialog.reorder_input.value(),
                    supplier_id=dialog.supplier_input.currentData() or 1,
                    unit="pcs",
                    shelf_location=""
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
                product.description = dialog.desc_input.text()
                product.sku = dialog.sku_input.text()
                product.barcode = dialog.barcode_input.text().strip() or None
                product.purchase_price = dialog.purchase_price_input.value()
                product.wholesale_price = dialog.wholesale_price_input.value()
                product.retail_price = dialog.retail_price_input.value()
                product.stock_level = dialog.stock_input.value()
                product.reorder_level = dialog.reorder_input.value()
                product.supplier_id = dialog.supplier_input.currentData()
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
        """Handle Up/Down arrow keys for field navigation - one field at a time"""
        try:
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QKeyEvent
        except ImportError:
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QKeyEvent
        
        if isinstance(event, QKeyEvent):
            # List of input fields in order
            fields = [
                self.name_input,
                self.desc_input,
                self.sku_input,
                self.barcode_input,
                self.purchase_price_input,
                self.wholesale_price_input,
                self.retail_price_input,
                self.stock_input,
                self.reorder_input,
                self.rack_input,
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
        
        # Handle Enter key to save product
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            # Check if any field has focus (including SearchableComboBox search inputs)
            for field in fields:
                if field.hasFocus():
                    self.save_product()
                    return
                # Check SearchableComboBox search input focus
                elif hasattr(field, 'search_input') and field.search_input.hasFocus():
                    self.save_product()
                    return
        
        return super().keyPressEvent(event)

    def setup_ui(self):
        self.setWindowTitle("Add Product" if not self.product else "Edit Product")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        self.desc_input = QLineEdit()
        self.sku_input = QLineEdit()
        self.barcode_input = QLineEdit()
        
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
        
        self.wholesale_price_input = NavigationDoubleSpinBox()
        self.wholesale_price_input.setMaximum(1000000)
        self.wholesale_price_input.setMinimum(0.00)
        self.wholesale_price_input.setDecimals(2)
        
        self.purchase_price_input = NavigationDoubleSpinBox()
        self.purchase_price_input.setMaximum(1000000)
        self.purchase_price_input.setMinimum(0.00)
        self.purchase_price_input.setDecimals(2)
        
        self.stock_input = QLineEdit()
        self.stock_input.setPlaceholderText("Current stock (e.g., 100+4 = 104)")
        
        self.reorder_input = NavigationSpinBox()
        self.reorder_input.setMaximum(10000)
        self.reorder_input.setMinimum(0)
        
        # Rack location input
        self.rack_input = QLineEdit()
        self.rack_input.setPlaceholderText("e.g., A1, B2, C3...")
        
        # Supplier searchable dropdown with "Add New" option
        self.supplier_input = SearchableComboBox(allow_add_new=True, on_add_new_callback=self._create_new_supplier)
        
        # Category and Subcategory dropdowns
        self.category_input = SimpleComboBox()
        self.subcategory_input = SimpleComboBox()
        
        # Populate categories and subcategories
        self._populate_categories()
        
        # Connect category change to update subcategories
        self.category_input.currentIndexChanged.connect(self._on_category_changed)
        
        # Populate fields list for navigation and barcode handling
        self.fields = [
            self.name_input,
            self.desc_input,
            self.sku_input,
            self.barcode_input,
            self.category_input,
            self.subcategory_input,
            self.purchase_price_input,
            self.wholesale_price_input,
            self.retail_price_input,
            self.stock_input,
            self.reorder_input,
            self.rack_input,
            self.supplier_input
        ]
        
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
        
        layout.addRow("Name*:", self.name_input)
        layout.addRow("Description:", self.desc_input)
        layout.addRow("SKU:", self.sku_input)  # Removed * to make it optional
        layout.addRow("Barcode:", barcode_widget)  # Moved barcode here, after SKU
        layout.addRow("Category:", self.category_input)
        layout.addRow("Subcategory:", self.subcategory_input)
        layout.addRow("Purchase Price*:", self.purchase_price_input)
        layout.addRow("Wholesale Price*:", self.wholesale_price_input)
        layout.addRow("Retail Price*:", self.retail_price_input)
        layout.addRow("Stock:", self.stock_input)
        layout.addRow("Reorder Level:", self.reorder_input)
        layout.addRow("Rack Location:", self.rack_input)
        layout.addRow("Supplier:", self.supplier_input)
        
        # Add validation info label
        info_label = QLabel("* Required fields\nRetail ≥ Wholesale ≥ Purchase Price")
        info_label.setStyleSheet("color: #94a3b8; font-size: 11px; margin-top: 5px;")
        layout.addRow(info_label)
        
        buttons_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addRow(buttons_layout)
    
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
        
        # Validate SKU (optional field)
        sku = self.sku_input.text().strip()
        if sku and len(sku) < 2:
            errors.append("• SKU must be at least 2 characters if provided")
        
        # SKU uniqueness check removed - multiple products can have same SKU
        
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
        
        # Validate stock
        stock = self._parse_stock_value(self.stock_input.text())
        reorder = self.reorder_input.value()
        
        if stock < 0:
            errors.append("• Stock level cannot be negative")
        if reorder < 0:
            errors.append("• Reorder level cannot be negative")
        
        if errors:
            QMessageBox.warning(
                self,
                "Validation Errors",
                "Please fix the following errors:\n\n" + "\n".join(errors)
            )
            return
        
        self.accept()
    
    def _populate_categories(self):
        """Populate category and subcategory dropdowns"""
        try:
            from pos_app.models.database import ProductCategory, ProductSubcategory
            
            # Get session from parent controller
            if self.parent_widget and hasattr(self.parent_widget, 'controller') and hasattr(self.parent_widget.controller, 'session'):
                session = self.parent_widget.controller.session
                
                # Get all categories
                categories = session.query(ProductCategory).all()
                
                # Add categories to dropdown
                self.category_input.addItem("Select Category", None)
                for category in categories:
                    self.category_input.addItem(category.name, category.id)
                
                # Store subcategories by category for quick access
                self._subcategories_by_category = {}
                for category in categories:
                    subcategories = session.query(ProductSubcategory).filter(
                        ProductSubcategory.category_id == category.id
                    ).all()
                    self._subcategories_by_category[category.id] = subcategories
            else:
                # Fallback: add some default categories
                self.category_input.addItem("Select Category", None)
                self.category_input.addItem("Electronics", 1)
                self.category_input.addItem("Clothing", 2)
                self.category_input.addItem("Food", 3)
                self.category_input.addItem("Other", 4)
                self._subcategories_by_category = {}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Fallback: add some default categories
            self.category_input.addItem("Select Category", None)
            self.category_input.addItem("Electronics", 1)
            self.category_input.addItem("Clothing", 2)
            self.category_input.addItem("Food", 3)
            self.category_input.addItem("Other", 4)
            self._subcategories_by_category = {}
    
    def _on_category_changed(self, index):
        """Handle category change to update subcategories"""
        self.subcategory_input.clear()
        self.subcategory_input.addItem("Select Subcategory", None)
        
        category_id = self.category_input.itemData(index)
        if category_id is None:
            return
        
        try:
            if category_id in self._subcategories_by_category:
                subcategories = self._subcategories_by_category[category_id]
                for subcategory in subcategories:
                    self.subcategory_input.addItem(subcategory.name, subcategory.id)
        except Exception:
            # Fallback: add some default subcategories
            if category_id == 1:  # Electronics
                self.subcategory_input.addItem("Phones", 101)
                self.subcategory_input.addItem("Laptops", 102)
                self.subcategory_input.addItem("Accessories", 103)
            elif category_id == 2:  # Clothing
                self.subcategory_input.addItem("Men", 201)
                self.subcategory_input.addItem("Women", 202)
                self.subcategory_input.addItem("Kids", 203)
            elif category_id == 3:  # Food
                self.subcategory_input.addItem("Beverages", 301)
                self.subcategory_input.addItem("Snacks", 302)
                self.subcategory_input.addItem("Groceries", 303)
            elif category_id == 4:  # Other
                self.subcategory_input.addItem("General", 401)

    def _create_new_supplier(self, supplier_name):
        """Create a new supplier and return its ID"""
        try:
            from pos_app.models.database import Supplier
            from pos_app.database.db_utils import get_db_session
            
            with get_db_session() as session:
                # Check if supplier already exists
                existing = session.query(Supplier).filter(Supplier.name == supplier_name).first()
                if existing:
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
                
                return new_supplier.id
        
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
        """Generate a random barcode and optionally print labels"""
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
        
        # Print barcode labels if enabled
        self._print_barcode_labels(full_barcode)
    
    def _print_barcode_labels(self, barcode_data):
        """Print barcode labels based on settings"""
        try:
            from pos_app.utils.barcode_printer import BarcodePrinterSettings
            
            # Load barcode settings
            settings = BarcodePrinterSettings()
            
            # Check if auto-print is enabled
            if not settings.get_setting('auto_print_on_generate', True):
                return
            
            # Get printer settings
            printer_name = settings.get_setting('printer_name', '')
            if not printer_name:
                return  # No printer configured
            
            # Get product name for label
            product_name = self.name_input.text().strip() or "PRODUCT"
            
            # Determine number of copies
            copies = settings.get_setting('default_copies', 1)
            if settings.get_setting('print_copies_from_stock', True):
                stock_level = self._parse_stock_value(self.stock_input.text())
                if stock_level > 0:
                    copies = min(stock_level, 100)  # Max 100 copies to prevent excessive printing
            
            # Create printer and print
            label_size = settings.get_setting('label_size', '2x1')
            dpi = settings.get_setting('dpi', '203')
            
            from pos_app.utils.barcode_printer import BarcodePrinter
            printer = BarcodePrinter(
                printer_name=printer_name,
                label_size=label_size,
                dpi=dpi
            )
            
            # Show printing progress
            try:
                from PySide6.QtWidgets import QProgressDialog
                from PySide6.QtCore import Qt
            except ImportError:
                from PyQt6.QtWidgets import QProgressDialog
                from PyQt6.QtCore import Qt
            
            progress = QProgressDialog(f"Printing {copies} barcode label(s)...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Printing Labels")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)
            
            try:
                success = printer.print_barcode(barcode_data, product_name, copies)
                
                if success:
                    progress.setValue(100)
                    # Show success message briefly
                    progress.setLabelText(f"Successfully printed {copies} label(s)!")
                    # Auto-close after 2 seconds
                    progress.setMaximum(1)
                    progress.setValue(1)
                else:
                    # Show error but don't block the user
                    progress.setLabelText("Printing failed. Check printer connection.")
                    progress.setMaximum(1)
                    progress.setValue(1)
                    
            finally:
                # Close progress dialog after a short delay
                try:
                    from PySide6.QtCore import QTimer
                except ImportError:
                    from PyQt6.QtCore import QTimer
                
                QTimer.singleShot(2000, progress.close)
                
        except Exception as e:
            # Don't let printing errors block barcode generation
            # Just log the error and continue
            import traceback
            traceback.print_exc()
            print(f"Barcode printing error: {e}")

    def load_product_data(self):
        if self.product:
            self.name_input.setText(self.product.name or "")
            self.desc_input.setText(self.product.description or "")
            self.sku_input.setText(self.product.sku or "")
            self.barcode_input.setText(self.product.barcode or "")
            self.purchase_price_input.setValue(self.product.purchase_price or 0.01)
            self.wholesale_price_input.setValue(self.product.wholesale_price or 0.01)
            self.retail_price_input.setValue(self.product.retail_price or 0.01)
            self.stock_input.setValue(self.product.stock_level or 0)
            self.reorder_input.setValue(self.product.reorder_level or 0)
            self.rack_input.setText(self.product.shelf_location or "")
            
            # Set supplier in searchable dropdown
            if self.product.supplier_id:
                self.supplier_input.set_selected_by_id(self.product.supplier_id)
    
    def save_product(self):
        """Save product - alias for validate_and_accept"""
        self.validate_and_accept()
    
    def _parse_stock_value(self, stock_text):
        """Parse stock value supporting + notation (e.g., '100+4' = 104)"""
        if not stock_text or not stock_text.strip():
            return 0
        
        stock_text = stock_text.strip()
        
        # Check if it contains + notation
        if '+' in stock_text:
            try:
                # Split by + and sum all parts
                parts = stock_text.split('+')
                total = 0
                for part in parts:
                    part = part.strip()
                    if part:
                        total += int(part)
                return total
            except ValueError:
                # If parsing fails, try to convert as-is
                try:
                    return int(stock_text)
                except ValueError:
                    return 0
        else:
            # No + notation, just convert to int
            try:
                return int(stock_text)
            except ValueError:
                return 0
    
    def keyPressEvent(self, event):
        """Handle key press events for navigation"""
        try:
            from PySide6.QtCore import Qt
        except ImportError:
            from PyQt6.QtCore import Qt
        
        # List of input fields in order
        fields = [
            self.name_input,
            self.desc_input,
            self.sku_input,
            self.barcode_input,
            self.category_input,
            self.subcategory_input,
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
        
        # For other keys, use default handling
        super().keyPressEvent(event)
