from pos_app.views.base import BaseView
from pos_app.models.database import Supplier, Product
try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QComboBox, QHeaderView, QCompleter, QAbstractItemView
    )
    from PySide6.QtCore import Qt, Signal
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
        QLineEdit, QMessageBox, QComboBox, QHeaderView, QCompleter, QAbstractItemView
    )
    from PyQt6.QtCore import Qt, pyqtSignal as Signal

class SuppliersWidget(BaseView):
    action_pay_supplier = Signal(int)  # supplier_id
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        # Ensure clean transaction state
        try:
            self.controller.session.rollback()
        except Exception as e:
            print(f"Warning: Could not rollback session: {e}")
        self.page_size = 12
        self.is_admin = self._check_admin_role()
        self._last_sync_ts = None
        self.setup_ui()
        self.load_suppliers()
        self._init_sync_timer()
    
    def _check_admin_role(self):
        """Check if current user is admin"""
        try:
            # Try to get current user from main window or controllers
            from pos_app.models.database import db_session, User
            # This is a fallback - ideally we'd pass user info from main window
            # For now, we'll check if there's any way to access current user
            return True  # Default to True for now, will be overridden by main window
        except Exception:
            return True

    def setup_ui(self):
        print("[Suppliers] setup_ui start")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🏢 Supplier Management")
        header.setProperty('role', 'heading')
        header.setStyleSheet("font-size: 28px; font-weight: bold; color: #f8fafc;")
        header_layout.addWidget(header)
        header_layout.addStretch()
        
        add_btn = QPushButton("✨ Add New Supplier")
        add_btn.setProperty('accent', 'Qt.green')
        add_btn.setMinimumHeight(44)
        add_btn.clicked.connect(self.show_add_supplier_dialog)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)
        
        # Action buttons (initially disabled)
        actions_layout = QHBoxLayout()
        actions_layout.setContentsMargins(0, 10, 0, 10)
        
        self.edit_supplier_btn = QPushButton("✏️ Edit Supplier")
        self.edit_supplier_btn.setProperty('accent', 'Qt.blue')
        self.edit_supplier_btn.setMinimumHeight(36)
        self.edit_supplier_btn.setEnabled(False)
        self.edit_supplier_btn.clicked.connect(self.edit_selected_supplier)
        self.edit_supplier_btn.setVisible(self.is_admin)
        
        self.delete_supplier_btn = QPushButton("🗑️ Delete Supplier")
        self.delete_supplier_btn.setProperty('accent', 'Qt.red')
        self.delete_supplier_btn.setMinimumHeight(36)
        self.delete_supplier_btn.setEnabled(False)
        self.delete_supplier_btn.clicked.connect(self.delete_selected_supplier)
        self.delete_supplier_btn.setVisible(self.is_admin)
        
        self.pay_supplier_btn = QPushButton("💰 Pay Supplier")
        self.pay_supplier_btn.setProperty('accent', 'orange')
        self.pay_supplier_btn.setMinimumHeight(36)
        self.pay_supplier_btn.setEnabled(False)
        self.pay_supplier_btn.clicked.connect(self.pay_selected_supplier)
        self.pay_supplier_btn.setVisible(self.is_admin)
        
        self.new_purchase_btn = QPushButton("🧾 New Purchase")
        self.new_purchase_btn.setProperty('accent', 'Qt.green')
        self.new_purchase_btn.setMinimumHeight(36)
        self.new_purchase_btn.setEnabled(False)
        self.new_purchase_btn.clicked.connect(self.create_purchase_for_selected)
        self.new_purchase_btn.setVisible(self.is_admin)
        
        self.view_report_btn = QPushButton("📊 Purchase History")
        self.view_report_btn.setProperty('accent', 'purple')
        self.view_report_btn.setMinimumHeight(36)
        self.view_report_btn.setEnabled(False)
        self.view_report_btn.clicked.connect(self.view_supplier_report)
        self.view_report_btn.setVisible(self.is_admin)
        
        actions_layout.addWidget(self.edit_supplier_btn)
        actions_layout.addWidget(self.delete_supplier_btn)
        actions_layout.addWidget(self.pay_supplier_btn)
        actions_layout.addWidget(self.new_purchase_btn)
        actions_layout.addWidget(self.view_report_btn)
        actions_layout.addStretch()
        layout.addLayout(actions_layout)

        # Search + pagination (only show for admin)
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Search suppliers...')
        self.search_input.textChanged.connect(self.apply_filter)
        self.search_input.setVisible(self.is_admin)
        search_layout.addWidget(self.search_input)

        self.page_size = 25
        self.current_page = 0
        self.prev_btn = QPushButton("Prev")
        self.next_btn = QPushButton("Next")
        self.page_label = QLabel("Page 1")
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        self.prev_btn.setVisible(self.is_admin)
        self.next_btn.setVisible(self.is_admin)
        self.page_label.setVisible(self.is_admin)
        search_layout.addStretch()
        search_layout.addWidget(self.prev_btn)
        search_layout.addWidget(self.page_label)
        search_layout.addWidget(self.next_btn)
        layout.addLayout(search_layout)

        # Suppliers Table (only show for admin)
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Name", "Contact", "Email", "Address",
            "Outstanding"
        ])
        self.table.setVisible(self.is_admin)
        
        # Table selection
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        self.selected_supplier_id = None
        try:
            from PySide6.QtWidgets import QHeaderView
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.horizontalHeader().setStretchLastSection(True)
            # Clamp Outstanding column sizing
            self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
            self.table.horizontalHeader().resizeSection(4, 120)
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
        try:
            # Explicitly set layout to ensure it's attached
            self.setLayout(layout)
        except Exception:
            pass
        print("[Suppliers] setup_ui end (layout set)")

    def show_add_supplier_dialog(self):
        dialog = SupplierDialog(self)
        if dialog.exec() == QDialog.Accepted:
            if not dialog.name_input.text().strip():
                QMessageBox.warning(self, "Validation", "Supplier name is required.")
                return
            try:
                self.controller.add_supplier(
                    name=dialog.name_input.text().strip(),
                    contact=dialog.contact_input.text().strip(),
                    email=dialog.email_input.text().strip(),
                    address=dialog.address_input.text().strip()
                )
                QMessageBox.information(self, "Success", "Supplier added successfully!")
                self.load_suppliers()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def load_suppliers(self):
        try:
            print("[Suppliers] load_suppliers called")
            # Support either list_suppliers or get_suppliers on the controller
            if hasattr(self.controller, 'list_suppliers'):
                suppliers = self.controller.list_suppliers()
            else:
                suppliers = self.controller.get_suppliers()

            count = len(suppliers) if suppliers is not None else 0
            print(f"[Suppliers] fetched suppliers: {count}")

            # cache and show first page
            self._suppliers_cache = suppliers or []
            self.current_page = 0

            # Clear previous contents safely
            try:
                self.table.clearContents()
            except Exception:
                pass

            items = self._suppliers_cache[self.current_page*self.page_size:(self.current_page+1)*self.page_size]
            self.table.setRowCount(len(items))

            for i, s in enumerate(items):
                print(f"[Suppliers] row {i}: {getattr(s, 'name', None)}")
                self.table.setItem(i, 0, QTableWidgetItem(s.name or ""))
                self.table.setItem(i, 1, QTableWidgetItem(s.contact or ""))
                self.table.setItem(i, 2, QTableWidgetItem(s.email or ""))
                self.table.setItem(i, 3, QTableWidgetItem(s.address or ""))
                # Outstanding (sum of purchases - paid)
                try:
                    from pos_app.models.database import Purchase
                    purchases = self.controller.session.query(Purchase).filter(Purchase.supplier_id == s.id).all()
                    outstanding = sum((p.total_amount or 0.0) - (p.paid_amount or 0.0) for p in purchases)
                    self.table.setItem(i, 4, QTableWidgetItem(f"{outstanding:.2f}"))
                except Exception as oe:
                    print(f"[Suppliers] outstanding calc error for supplier {getattr(s,'id',None)}: {oe}")
                    try:
                        self.controller.session.rollback()
                    except Exception as e:
                        print(f"Warning: Could not rollback session after error: {e}")
                    self.table.setItem(i, 4, QTableWidgetItem("0.00"))
                # Store supplier ID for selection handling
                item = self.table.item(i, 0)
                if item:
                    item.setData(Qt.UserRole, s.id)
                self.table.setCellWidget(i, 4, None)  # Remove any existing widget

            # update page label and controls
            total_pages = max(1, (len(self._suppliers_cache) + self.page_size - 1) // self.page_size)
            self.page_label.setText(f"Page {self.current_page+1} / {total_pages}")
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled((self.current_page+1) < total_pages)

            # Force repaint to avoid blank rendering
            try:
                self.table.resizeColumnsToContents()
            except Exception:
                pass
            self.table.viewport().update()
            self.table.repaint()
            print(f"[Suppliers] table rows now: {self.table.rowCount()}")
        except Exception as e:
            import traceback
            print("[Suppliers] load_suppliers error:", e)
            traceback.print_exc()
            # Rollback failed transaction
            try:
                self.controller.session.rollback()
            except Exception as e:
                print(f"Error: Could not rollback failed transaction: {e}")
            self.table.setRowCount(0)
            print(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to load suppliers: {str(e)}")
        
        # Update local sync timestamp snapshot
        try:
            from pos_app.models.database import get_sync_timestamp
            ts = get_sync_timestamp(self.controller.session, 'suppliers')
            self._last_sync_ts = ts
        except Exception:
            pass
    
    def _init_sync_timer(self):
        """Poll sync_state and refresh suppliers when data changes on other machines."""
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
            ts = get_sync_timestamp(self.controller.session, 'suppliers')
            if ts is None:
                return
            if self._last_sync_ts is None or ts > self._last_sync_ts:
                self._last_sync_ts = ts
                self.load_suppliers()
        except Exception:
            pass

    def apply_filter(self, text):
        try:
            text = (text or "").strip().lower()
            if not hasattr(self, '_suppliers_cache'):
                return
            filtered = [s for s in self._suppliers_cache if text in (s.name or '').lower() or text in (s.contact or '').lower()]
            self._filtered_suppliers = filtered
            self.current_page = 0
            self._update_page()
        except Exception:
            pass

    def _update_page(self):
        items = getattr(self, '_filtered_suppliers', self._suppliers_cache)
        start = self.current_page * self.page_size
        page_items = items[start:start + self.page_size]
        self.table.setRowCount(len(page_items))
        for i, s in enumerate(page_items):
            self.table.setItem(i, 0, QTableWidgetItem(s.name or ""))
            self.table.setItem(i, 1, QTableWidgetItem(s.contact or ""))
            self.table.setItem(i, 2, QTableWidgetItem(s.email or ""))
            self.table.setItem(i, 3, QTableWidgetItem(s.address or ""))
            try:
                from pos_app.models.database import Purchase
                purchases = self.controller.session.query(Purchase).filter(Purchase.supplier_id == s.id).all()
                outstanding = sum((p.total_amount or 0.0) - (p.paid_amount or 0.0) for p in purchases)
                self.table.setItem(i, 4, QTableWidgetItem(f"{outstanding:.2f}"))
            except Exception:
                self.table.setItem(i, 4, QTableWidgetItem("0.00"))
            # Store supplier ID for selection handling
            item = self.table.item(i, 0)
            if item:
                item.setData(Qt.UserRole, s.id)
        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        self.page_label.setText(f"Page {self.current_page+1} / {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled((self.current_page+1) < total_pages)

    def on_selection_changed(self):
        """Enable/disable action buttons based on selection"""
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            # Get supplier ID from the table item
            item = self.table.item(row, 0)
            if item:
                self.selected_supplier_id = item.data(Qt.UserRole)
                self.edit_supplier_btn.setEnabled(True)
                self.delete_supplier_btn.setEnabled(True)
                self.pay_supplier_btn.setEnabled(True)
                self.new_purchase_btn.setEnabled(True)
                self.view_report_btn.setEnabled(True)
            else:
                self.selected_supplier_id = None
                self.edit_supplier_btn.setEnabled(False)
                self.delete_supplier_btn.setEnabled(False)
                self.pay_supplier_btn.setEnabled(False)
                self.new_purchase_btn.setEnabled(False)
                self.view_report_btn.setEnabled(False)
        else:
            self.selected_supplier_id = None
            self.edit_supplier_btn.setEnabled(False)
            self.delete_supplier_btn.setEnabled(False)
            self.pay_supplier_btn.setEnabled(False)
            self.new_purchase_btn.setEnabled(False)
            self.view_report_btn.setEnabled(False)

    def edit_selected_supplier(self):
        if self.selected_supplier_id:
            self._edit_supplier(self.selected_supplier_id)

    def delete_selected_supplier(self):
        if self.selected_supplier_id:
            self._delete_supplier(self.selected_supplier_id)

    def pay_selected_supplier(self):
        if self.selected_supplier_id:
            self._pay_supplier(self.selected_supplier_id)

    def create_purchase_for_selected(self):
        if self.selected_supplier_id:
            self._new_purchase(self.selected_supplier_id)
    
    def view_supplier_report(self):
        if self.selected_supplier_id:
            try:
                from pos_app.views.dialogs.supplier_report_dialog import SupplierReportDialog
                dlg = SupplierReportDialog(self.controller, self.selected_supplier_id, self)
                dlg.exec()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open supplier report: {str(e)}")

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._update_page()

    def _next_page(self):
        items = getattr(self, '_filtered_suppliers', self._suppliers_cache)
        total_pages = max(1, (len(items) + self.page_size - 1) // self.page_size)
        if (self.current_page+1) < total_pages:
            self.current_page += 1
            self._update_page()

    def _delete_supplier(self, supplier_id):
        try:
            from pos_app.models.database import Supplier, Product, Purchase, Expense
            
            supplier = self.controller.session.get(Supplier, supplier_id)
            if not supplier:
                QMessageBox.warning(self, "Error", "Supplier not found")
                return
            
            # Check for foreign key dependencies
            # Check if supplier has products
            products_count = self.controller.session.query(Product).filter(
                Product.supplier_id == supplier_id
            ).count()
            
            # Check if supplier has purchases
            purchases_count = self.controller.session.query(Purchase).filter(
                Purchase.supplier_id == supplier_id
            ).count()
            
            # Check if supplier has expenses
            expenses_count = self.controller.session.query(Expense).filter(
                Expense.supplier_id == supplier_id
            ).count()
            
            if products_count > 0 or purchases_count > 0 or expenses_count > 0:
                QMessageBox.warning(
                    self,
                    "Cannot Delete Supplier",
                    f"Cannot delete '{supplier.name}' because it is referenced in:\n\n"
                    f"• {products_count} product(s)\n"
                    f"• {purchases_count} purchase(s)\n"
                    f"• {expenses_count} expense(s)\n\n"
                    f"You can mark it as inactive instead of deleting it."
                )
                return
            
            res = QMessageBox.question(
                self, 
                "Confirm Delete", 
                f"Are you sure you want to delete '{supplier.name}'?\n\n"
                f"This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No
            )
            if res == QMessageBox.Yes:
                self.controller.delete_supplier(supplier_id)
                QMessageBox.information(self, "Success", f"Supplier '{supplier.name}' deleted successfully")
                self.load_suppliers()
        except Exception as e:
            self.controller.session.rollback()
            QMessageBox.critical(self, "Error", f"Failed to delete supplier:\n\n{str(e)}")

    def _edit_supplier(self, supplier_id):
        try:
            from pos_app.models.database import Supplier
            sup = self.controller.session.get(Supplier, supplier_id)
            if not sup:
                QMessageBox.warning(self, "Error", "Supplier not found")
                return
            dialog = EditSupplierDialog(self, sup)
            if dialog.exec() == QDialog.Accepted:
                self.controller.update_supplier(
                    supplier_id,
                    name=dialog.name_input.text().strip(),
                    contact=dialog.contact_input.text().strip(),
                    email=dialog.email_input.text().strip(),
                    address=dialog.address_input.text().strip()
                )
                QMessageBox.information(self, "Success", "Supplier updated")
                self.load_suppliers()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _pay_supplier(self, supplier_id):
        """Handle payment to supplier - emit signal for main window to handle"""
        try:
            try:
                supplier_id_int = int(supplier_id)
                if supplier_id_int <= 0:
                    raise ValueError("Invalid supplier ID")
                self.action_pay_supplier.emit(supplier_id_int)
            except (ValueError, TypeError) as e:
                QMessageBox.critical(self, "Error", f"Invalid supplier ID: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open payment dialog: {str(e)}")

    def _new_purchase(self, supplier_id):
        try:
            dlg = NewPurchaseDialog(self.controller, supplier_id)
            if dlg.exec() == QDialog.Accepted:
                # Purchase creation is now handled in the dialog's create_purchase method
                self.load_suppliers()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

class SupplierDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Supplier")
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.contact_input = QLineEdit()
        self.email_input = QLineEdit()
        self.address_input = QLineEdit()

        layout.addRow("Name:", self.name_input)
        layout.addRow("Contact:", self.contact_input)
        layout.addRow("Email:", self.email_input)
        layout.addRow("Address:", self.address_input)

        buttons = QHBoxLayout()
        ok_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

class EditSupplierDialog(SupplierDialog):
    def __init__(self, parent=None, supplier=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Supplier")
        self.supplier = supplier
        if supplier:
            self.name_input.setText(supplier.name or "")
            self.contact_input.setText(supplier.contact or "")
            self.email_input.setText(supplier.email or "")
            self.address_input.setText(supplier.address or "")

class NewPurchaseDialog(QDialog):
    def __init__(self, controller=None, supplier_id=None):
        super().__init__()
        self.setWindowTitle("Create Purchase")
        self.controller = controller
        self.supplier_id = supplier_id
        self.selected_product_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox

        # Searchable product dropdown
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        try:
            self.product_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        except Exception:
            try:
                self.product_combo.setInsertPolicy(QComboBox.NoInsert)
            except Exception:
                pass
        self._load_products()

        # Setup autocomplete
        completer = QCompleter(self.product_combo.model(), self)
        try:
            completer.setCaseSensitivity(False)
            from PySide6.QtCore import Qt as _Qt
            completer.setFilterMode(_Qt.MatchContains)
        except Exception:
            pass
        self.product_combo.setCompleter(completer)

        self.qty_input = QSpinBox()
        self.qty_input.setMaximum(100000)
        self.qty_input.setValue(1)
        self.unit_cost_input = QDoubleSpinBox()
        self.unit_cost_input.setMaximum(100000000.0)
        self.unit_cost_input.setDecimals(2)
        self.amount_paid_input = QDoubleSpinBox()
        self.amount_paid_input.setMaximum(100000000.0)
        self.amount_paid_input.setDecimals(2)
        self.notes_input = QLineEdit()

        layout.addRow("Product:", self.product_combo)
        layout.addRow("Quantity:", self.qty_input)
        layout.addRow("Unit Cost:", self.unit_cost_input)
        layout.addRow("Amount Paid:", self.amount_paid_input)
        layout.addRow("Notes:", self.notes_input)

        buttons = QHBoxLayout()
        ok_button = QPushButton("Create")
        cancel_button = QPushButton("Cancel")
        ok_button.clicked.connect(self.create_purchase)
        cancel_button.clicked.connect(self.reject)
        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow(buttons)

    def _load_products(self):
        try:
            if not self.controller:
                return
            products = self.controller.session.query(Product).filter(Product.is_active == True).all()
            for p in products:
                label = f"{p.name} (SKU: {p.sku or '-'} )"
                self.product_combo.addItem(label, p.id)
        except Exception:
            pass

    def create_purchase(self):
        try:
            # Get selected product ID
            product_id = self.product_combo.currentData()
            if not product_id:
                QMessageBox.warning(self, "Validation", "Please select a product.")
                return

            try:
                qty = int(self.qty_input.value())
                if qty <= 0:
                    QMessageBox.warning(self, "Invalid Input", "Quantity must be greater than 0")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid quantity")
                return
            
            try:
                unit_cost = float(self.unit_cost_input.value())
                if unit_cost < 0:
                    QMessageBox.warning(self, "Invalid Input", "Unit cost cannot be negative")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid unit cost")
                return
            
            try:
                paid = float(self.amount_paid_input.value())
                if paid < 0:
                    QMessageBox.warning(self, "Invalid Input", "Paid amount cannot be negative")
                    return
            except (ValueError, TypeError):
                QMessageBox.warning(self, "Invalid Input", "Please enter a valid paid amount")
                return
            notes = self.notes_input.text().strip()

            # Use the controller method directly
            if not self.controller:
                QMessageBox.critical(self, "Error", "Controller not available")
                return

            if not self.supplier_id:
                QMessageBox.critical(self, "Error", "Supplier ID is None")
                return

            self.controller.create_supplier_purchase(
                self.supplier_id,
                items=[{"product_id": int(product_id), "quantity": qty, "unit_cost": unit_cost}],
                notes=notes,
                amount_paid=paid if paid > 0 else None
            )
            QMessageBox.information(self, "Success", "Purchase created")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

