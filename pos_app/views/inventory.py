try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QDialogButtonBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
        QAbstractItemView
    )
    from PySide6.QtCore import Signal, Qt, QTimer
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QSpinBox, QDoubleSpinBox, QComboBox,
        QDialogButtonBox, QRadioButton, QButtonGroup, QScrollArea, QFrame,
        QAbstractItemView
    )
    from PyQt6.QtCore import pyqtSignal as Signal, Qt, QTimer
from pos_app.models.database import Product, Supplier, InventoryLocation
from pos_app.views.suppliers import SupplierDialog

class InventoryWidget(QWidget):
    product_added = Signal()
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.selected_product_id = None
        self._last_sync_ts = None
        self.setup_ui()
        self.load_products()
        self._init_sync_timer()

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
        
        # Barcode search widget for quick product lookup
        from pos_app.widgets.barcode_search import BarcodeSearchWidget
        self.barcode_widget = BarcodeSearchWidget(
            session=self.controller.session,
            parent=self,
            show_quantity=False,
            auto_add=False
        )
        self.barcode_widget.product_selected.connect(self._on_product_scanned)
        layout.addWidget(self.barcode_widget)

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
        
        self.show_all_btn = QPushButton("📦 Show All")
        self.show_all_btn.setToolTip("Show all products")
        self.show_all_btn.setProperty('accent', 'Qt.blue')
        self.show_all_btn.setMinimumHeight(44)
        self.show_all_btn.clicked.connect(self.show_all_products)
        self.show_all_btn.setVisible(False)  # Initially hidden
        
        toolbar_layout.addWidget(add_btn)
        toolbar_layout.addWidget(manage_cats_btn)
        toolbar_layout.addWidget(low_btn)
        toolbar_layout.addWidget(self.show_all_btn)  # Add Show All button to toolbar
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

        # Products Table with purchase price
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Name", "Barcode", "Description", "Purchase Price",
            "Retail Price", "Wholesale Price", "Stock Level", "Location"
        ])
        
        # Set column widths
        self.table.setColumnWidth(0, 200)  # Name
        self.table.setColumnWidth(1, 120)  # Barcode
        self.table.setColumnWidth(2, 250)  # Description
        self.table.setColumnWidth(3, 120)  # Purchase Price
        self.table.setColumnWidth(4, 120)  # Retail Price
        self.table.setColumnWidth(5, 140)  # Wholesale Price
        self.table.setColumnWidth(6, 120)  # Stock Level
        self.table.setColumnWidth(7, 100)  # Location
        
        # Table selection
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        try:
            from PySide6.QtWidgets import QHeaderView
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            # Show vertical header (row numbers) and set proper width
            self.table.verticalHeader().setVisible(True)
            self.table.verticalHeader().setDefaultSectionSize(32)  # Set row height
            self.table.verticalHeader().setMinimumWidth(50)  # Set minimum width for row numbers
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

    def edit_selected_product(self):
        if self.selected_product_id:
            self._edit_product(self.selected_product_id)

    def delete_selected_product(self):
        if self.selected_product_id:
            self._delete_product(self.selected_product_id)
    
    def _edit_product(self, product_id):
        """Open ProductDialog to edit an existing product and update stock/prices."""
        try:
            product = self.controller.session.get(Product, product_id)
            if not product:
                QMessageBox.warning(self, "Error", "Product not found")
                return

            # Get product dialog type from settings
            from PySide6.QtCore import QSettings
            settings = QSettings()
            product_dialog_type = settings.value("product_dialog_type", "Detailed")
            
            if product_dialog_type == "Simple":
                # Use simple product dialog for editing
                from pos_app.views.simple_product_dialog import ProductDialog
                dialog = ProductDialog(self, product)
                if dialog.exec() == QDialog.Accepted:
                    # Get product data from simple dialog
                    product_data = dialog.get_product_data()
                    # Update product with new data
                    for key, value in product_data.items():
                        if hasattr(product, key):
                            setattr(product, key, value)
                    self.controller.session.commit()
                    self.load_products()
                    QMessageBox.information(self, "Success", "Product updated successfully!")
                return
            
            # Use detailed product dialog (default)
            from pos_app.views.inventory_new import ProductDialog, safe_get_current_data
            dialog = ProductDialog(self, product)
            if dialog.exec() == QDialog.Accepted:
                # Apply edits
                product.name = dialog.name_input.text()
                # Description field was removed from ProductDialog
                product.description = None
                product.sku = dialog.sku_input.text()
                product.barcode = dialog.barcode_input.text().strip() or None
                product.purchase_price = dialog.purchase_price_input.value()
                product.wholesale_price = dialog.wholesale_price_input.value()
                product.retail_price = dialog.retail_price_input.value()
                
                # Handle stock with + operator support (e.g., "12+2" becomes 14)
                stock_text = dialog.stock_input.text().strip()
                try:
                    if '+' in stock_text:
                        # Evaluate the expression (e.g., "12+2" = 14)
                        stock_value = int(eval(stock_text, {"__builtins__": {}}, {}))
                    else:
                        stock_value = int(stock_text) if stock_text else 0
                except:
                    stock_value = 0
                product.stock_level = stock_value
                
                product.reorder_level = dialog.reorder_input.value()
                product.supplier_id = safe_get_current_data(dialog.supplier_input)
                
                # Handle new fields
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

                # Legacy text fields (keep for older screens/reports)
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
                    exp_str = None
                    try:
                        has_exp = bool(getattr(dialog, 'has_expiry_checkbox', None) and dialog.has_expiry_checkbox.isChecked())
                    except Exception:
                        has_exp = False
                    if has_exp:
                        try:
                            d = dialog.expiry_input.date()
                            exp_str = d.toString('yyyy-MM-dd')
                        except Exception:
                            exp_str = None
                    product.expiry_date = exp_str or None
                except Exception:
                    product.expiry_date = None

                # Commit and broadcast inventory sync
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
            import traceback
            print(f"[ERROR] Edit product failed: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to edit product:\n\n{str(e)}")

    def _delete_product(self, product_id):
        """Safely delete a product if it is not referenced in sales or purchases."""
        try:
            product = self.controller.session.get(Product, product_id)
            if not product:
                QMessageBox.warning(self, "Error", "Product not found")
                return

            # Check for foreign key dependencies
            from pos_app.models.database import SaleItem, PurchaseItem, StockMovement

            sale_items = self.controller.session.query(SaleItem).filter(
                SaleItem.product_id == product_id
            ).count()

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

            res = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Are you sure you want to delete '{product.name}'?\n\n"
                f"This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
            )
            if res != QMessageBox.Yes:
                return

            # Delete related stock movements first
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
            try:
                self.controller.session.rollback()
            except Exception:
                pass
            QMessageBox.critical(self, "Error", f"Failed to delete product:\n\n{str(e)}")
    
    def show_add_product_dialog(self):
        """Open appropriate product dialog based on settings (simple or detailed)"""
        try:
            # Get product dialog type from settings
            from PySide6.QtCore import QSettings
            settings = QSettings("POSApp", "Settings")
            product_dialog_type = settings.value("product_dialog_type", "Detailed")
            
            if product_dialog_type == "Simple":
                # Use simple product dialog
                from pos_app.views.simple_product_dialog import ProductDialog
                dialog = ProductDialog(self)
                if dialog.exec() == QDialog.Accepted:
                    # Get product data from simple dialog
                    product_data = dialog.get_product_data()
                    self.controller.add_product(**product_data)
            else:
                # Use detailed product dialog (default)
                from pos_app.views.inventory_new import ProductDialog, safe_get_current_data
                dialog = ProductDialog(self)
                if dialog.exec() == QDialog.Accepted:
                    # Handle stock with + operator support (e.g., "12+2" becomes 14)
                    stock_text = dialog.stock_input.text().strip()
                    try:
                        if '+' in stock_text:
                            # Evaluate the expression (e.g., "12+2" = 14)
                            stock_value = int(eval(stock_text, {"__builtins__": {}}, {}))
                        else:
                            stock_value = int(stock_text) if stock_text else 0
                    except:
                        stock_value = 0
                    
                    # Create product via controller
                    self.controller.add_product(
                        name=dialog.name_input.text(),
                        description=None,
                        sku=dialog.sku_input.text(),
                        barcode=(dialog.barcode_input.text().strip() or None),
                        purchase_price=dialog.purchase_price_input.value(),
                        wholesale_price=dialog.wholesale_price_input.value(),
                        retail_price=dialog.retail_price_input.value(),
                        stock_level=stock_value,
                        reorder_level=dialog.reorder_input.value(),
                        supplier_id=(safe_get_current_data(dialog.supplier_input) or None),
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
                        expiry_date=(dialog.expiry_input.date().toString('yyyy-MM-dd') if hasattr(dialog, 'expiry_input') and dialog.has_expiry_checkbox.isChecked() else None),
                    )
            
            # Refresh product list
            self.load_products()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add product: {str(e)}")

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
            load_subs_for_selected()

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
    
    def _on_product_scanned(self, product):
        """Handle product scanned from barcode widget"""
        try:
            # Select the product in the table
            for row in range(self.table.rowCount()):
                sku_item = self.table.item(row, 0)
                if sku_item and hasattr(product, 'sku') and sku_item.text() == (product.sku or ""):
                    self.table.selectRow(row)
                    self.selected_product_id = product.id
                    self.edit_product_btn.setEnabled(True)
                    self.delete_product_btn.setEnabled(True)
                    
                    # Show product details
                    QMessageBox.information(
                        self,
                        "Product Found",
                        f"<b>{product.name}</b><br><br>"
                        f"SKU: {product.sku or 'N/A'}<br>"
                        f"Barcode: {product.barcode or 'N/A'}<br>"
                        f"Stock: {product.stock_level or 0}<br>"
                        f"Retail Price: Rs {product.retail_price or 0:,.2f}<br>"
                        f"Purchase Price: Rs {product.purchase_price or 0:,.2f}<br><br>"
                        f"Product selected in table. You can now edit or delete it."
                    )
                    return
                    
            # Product not found in current table view
            QMessageBox.information(
                self,
                "Product Found",
                f"<b>{product.name}</b><br><br>"
                f"SKU: {product.sku or 'N/A'}<br>"
                f"Barcode: {product.barcode or 'N/A'}<br>"
                f"Stock: {product.stock_level or 0}<br>"
                f"Retail Price: Rs {product.retail_price or 0:,.2f}<br><br>"
                f"Product found but not visible in current table view.<br>"
                f"Try refreshing the product list."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process scanned product: {str(e)}")

    def load_products(self):
        try:
            # Get products with purchase price, sorted by creation date (newest first)
            from pos_app.models.database import Product
            try:
                products = self.controller.session.query(Product).order_by(Product.created_at.desc()).all()
            except:
                # Fallback if created_at doesn't exist
                products = self.controller.session.query(Product).order_by(Product.id.desc()).all()
            # Cache for pagination/filtering
            self._products_cache = products
            
            # Store current page items for selection handling
            self._current_page_items = products
            
            # Clear and populate table
            self.table.setRowCount(len(products))
            for row, product in enumerate(products):
                self.table.setItem(row, 0, QTableWidgetItem(product.name or ""))
                self.table.setItem(row, 1, QTableWidgetItem(product.barcode or ""))
                self.table.setItem(row, 2, QTableWidgetItem(product.description or ""))
                
                # Format prices with 2 decimal places
                purchase_price = QTableWidgetItem(f"Rs {product.purchase_price:,.2f}" if product.purchase_price else "N/A")
                retail_price = QTableWidgetItem(f"Rs {product.retail_price:,.2f}" if product.retail_price else "N/A")
                wholesale_price = QTableWidgetItem(f"Rs {product.wholesale_price:,.2f}" if product.wholesale_price else "N/A")
                
                # Right-align price columns
                for item in [purchase_price, retail_price, wholesale_price]:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                self.table.setItem(row, 3, purchase_price)
                self.table.setItem(row, 4, retail_price)
                self.table.setItem(row, 5, wholesale_price)
                
                # Stock level with conditional formatting
                stock_item = QTableWidgetItem(str(product.stock_level) if product.stock_level is not None else "0")
                stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                # Highlight low stock in Qt.red
                if product.stock_level is not None and product.reorder_level is not None:
                    if product.stock_level <= product.reorder_level:
                        stock_item.setForeground(Qt.red)
                        stock_item.setToolTip(f"Low stock! Reorder level: {product.reorder_level}")
                
                self.table.setItem(row, 6, stock_item)
                
                # Location information
                location_text = "Both"
                if product.warehouse_location and not product.shelf_location:
                    location_text = "Warehouse"
                elif product.shelf_location and not product.warehouse_location:
                    location_text = "Retail"
                elif not product.warehouse_location and not product.shelf_location:
                    location_text = "Both"  # Default
                
                location_item = QTableWidgetItem(location_text)
                location_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, 7, location_item)
                
                # Store product ID in the first column (hidden)
                if hasattr(product, 'id'):
                    self.table.item(row, 0).setData(Qt.UserRole, product.id)
            
            # Update pagination
            self._update_page()
            # Update sync timestamp snapshot
            try:
                from pos_app.models.database import get_sync_timestamp
                ts = get_sync_timestamp(self.controller.session, 'products')
                self._last_sync_ts = ts
            except Exception:
                pass
            
            # Start polling for sync state changes
            self._init_sync_timer()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load products: {str(e)}")
            products = self.controller.session.query(Product).all()
            self._products_cache = products
            self.current_page = 0
            self._update_page()

    def _update_page(self):
        """Update table based on current page and optional filters."""
        items = getattr(self, '_filtered_products', self._products_cache)
        start = self.current_page * self.page_size
        page_items = items[start:start + self.page_size]
        self._current_page_items = page_items

        self.table.setRowCount(len(page_items))
        for row, product in enumerate(page_items):
            self.table.setItem(row, 0, QTableWidgetItem(product.name or ""))
            self.table.setItem(row, 1, QTableWidgetItem(product.barcode or ""))
            self.table.setItem(row, 2, QTableWidgetItem(product.description or ""))

            purchase_price = QTableWidgetItem(f"Rs {product.purchase_price:,.2f}" if product.purchase_price else "N/A")
            retail_price = QTableWidgetItem(f"Rs {product.retail_price:,.2f}" if product.retail_price else "N/A")
            wholesale_price = QTableWidgetItem(f"Rs {product.wholesale_price:,.2f}" if product.wholesale_price else "N/A")

            for item in [purchase_price, retail_price, wholesale_price]:
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.table.setItem(row, 3, purchase_price)
            self.table.setItem(row, 4, retail_price)
            self.table.setItem(row, 5, wholesale_price)

            stock_item = QTableWidgetItem(str(product.stock_level) if product.stock_level is not None else "0")
            stock_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if product.stock_level is not None and product.reorder_level is not None:
                if product.stock_level <= product.reorder_level:
                    stock_item.setForeground(Qt.red)
                    stock_item.setToolTip(f"Low stock! Reorder level: {product.reorder_level}")
            self.table.setItem(row, 6, stock_item)

            location_text = "Both"
            if product.warehouse_location and not product.shelf_location:
                location_text = "Warehouse"
            elif product.shelf_location and not product.warehouse_location:
                location_text = "Retail"
            elif not product.warehouse_location and not product.shelf_location:
                location_text = "Both"

            location_item = QTableWidgetItem(location_text)
            location_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 7, location_item)

        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page+1} / {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled((self.current_page + 1) < total_pages)

    def apply_filter(self, text):
        try:
            text = (text or "").strip().lower()
            if not hasattr(self, '_products_cache'):
                return
            if not text:
                if hasattr(self, '_filtered_products'):
                    del self._filtered_products
                self.current_page = 0
                self._update_page()
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
            self.show_all_btn.setVisible(True)
        except Exception:
            pass

    def show_all_products(self):
        try:
            if hasattr(self, '_filtered_products'):
                del self._filtered_products
            self.current_page = 0
            self._update_page()
            self.show_all_btn.setVisible(False)
        except Exception:
            pass

    def _init_sync_timer(self):
        """Poll sync_state and refresh inventory when products/stock change on other machines."""
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

# If anything goes wrong, err on the side of not submitting
            return True

    def load_product_data(self):
        if not self.product:
            return
            
        self.sku_input.setText(self.product.sku or "")
        self.name_input.setText(self.product.name or "")
        self.description_input.setText(self.product.description or "")
        self.purchase_price_input.setValue(float(self.product.purchase_price or 0))
        self.retail_price_input.setValue(float(self.product.retail_price or 0))
        self.wholesale_price_input.setValue(float(self.product.wholesale_price or 0))
        self.stock_input.setValue(int(self.product.stock_level or 0))
        self.reorder_level_input.setValue(int(self.product.reorder_level or 5))
        # Set supplier selection if available
        try:
            if self.product.supplier_id is not None:
                for i in range(self.supplier_input.count()):
                    if self.supplier_input.itemData(i) == self.product.supplier_id:
                        self.supplier_input.setCurrentIndex(i)
                        break
        except Exception:
            pass
            
        # Set location selection based on product data
        try:
            # Default to "Both" if no specific location is set
            location_choice = 2  # Both
            
            # Check if product has location preferences
            if hasattr(self.product, 'warehouse_location') and self.product.warehouse_location:
                if hasattr(self.product, 'shelf_location') and self.product.shelf_location:
                    location_choice = 2  # Both
                else:
                    location_choice = 0  # Warehouse
            elif hasattr(self.product, 'shelf_location') and self.product.shelf_location:
                location_choice = 1  # Retail
            
            self.location_group.button(location_choice).setChecked(True)
        except Exception:
            # Default to Both if there's any issue
            self.both_radio.setChecked(True)

    def get_selected_location(self):
        """Get the selected storage location"""
        location_id = self.location_group.checkedId()
        if location_id == 0:  # Warehouse
            return InventoryLocation.WAREHOUSE
        elif location_id == 1:  # Retail
            return InventoryLocation.RETAIL
        else:  # Both or default
            return InventoryLocation.BOTH
